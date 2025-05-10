import os
from flask import Flask, Response, request, jsonify
from flask_socketio import SocketIO
from queue import Queue
import threading

from views import views_bp
from state_machine import TriggerMode, CameraState, CameraStateMachine
from camera.camera_hardware_controller import CameraHardwareController
from camera.camera_application_service import CameraApplicationService
from exif_manager import ExifManager

from mavlink_handler import MavlinkHandler
import cv2
import piexif
import json
from datetime import datetime

import subprocess
import time

app = Flask(__name__)
socketio = SocketIO(app)
app.register_blueprint(views_bp)
mavlink_handler = MavlinkHandler(socketio)

base_output_dir = "recordings"
os.makedirs(base_output_dir, exist_ok=True)

frame_save_queue = Queue(maxsize=30)

state_machine = CameraStateMachine()
camera_handler = CameraHardwareController(state_machine, frame_save_queue, mavlink_handler)
camera_service = CameraApplicationService(state_machine, camera_handler, socketio)

exif_manager = ExifManager(camera_service.settings_manager)

camera_service.settings_manager.apply_current_app_settings(state_machine, camera_handler, mavlink_handler)

def modify_mtu():
    try:
        # Check if MTU is already set to 9000
        result = subprocess.run(['/usr/sbin/ip', 'link', 'show', 'eth0'], capture_output=True, text=True, check=True)
        if 'mtu 9000' in result.stdout:
            print("MTU is already set to 9000 for eth0")
            return
        
        print("Bringing down the network interface eth0")
        subprocess.run(['/usr/bin/sudo', 'ip', 'link', 'set', 'eth0', 'down'], check=True)
        
        print("Setting MTU to 9000 for eth0")
        subprocess.run(['/usr/bin/sudo', 'ip', 'link', 'set', 'eth0', 'mtu', '9000'], check=True)
        
        print("Bringing up the network interface eth0")
        subprocess.run(['/usr/bin/sudo', 'ip', 'link', 'set', 'eth0', 'up'], check=True)
        
        print("Waiting for the network interface to stabilize")
        time.sleep(10)
        
        print("MTU modification completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running sudo commands: {e}")
        exit(1)

def generate_frames():
    while True:
        frame = camera_handler.get_latest_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def frame_saver_worker():
    while True:
        try:
            image, now, frame_index, telemetry = frame_save_queue.get()
            timestamp = now.strftime('%Y_%m_%d_%H-%M-%S') + f'-{int(now.microsecond / 10000):02d}'
            folder = camera_service.current_recording_folder
            if folder:
                filename = os.path.join(folder, f"IMG_{frame_index}_{timestamp}.jpg")
                
                cv2.imwrite(filename, image)
                
                app_settings = camera_service.settings_manager.get_app_settings()
                include_telemetry = app_settings.get('exif_telemetry', False)
                
                if include_telemetry and telemetry and telemetry != {}:
                    exif_manager.apply_exif_to_file(filename, now, telemetry)
                    print(f"Saved frame with telemetry to {filename}")
                else:
                    exif_manager.apply_exif_to_file(filename, now)
                    print(f"Saved frame without telemetry to {filename}")
        except Exception as e:
            print(f"Error saving frame: {e}")
            import traceback
            traceback.print_exc()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify({'state': state_machine.get_state().name})

@app.route('/api/state', methods=['POST'])
def set_state():
    data = request.get_json()
    if 'state' not in data:
        return jsonify({'error': 'Missing state parameter'}), 400
        
    requested_state = data['state'].upper()
    try:
        new_state = CameraState[requested_state]
        success = camera_service.change_state(new_state, data.get('folder_name', ''))
        
        return jsonify({
            'success': success, 
            'state': state_machine.get_state().name
        })
    except KeyError:
        valid_states = [s.name for s in CameraState]
        return jsonify({'error': f'Invalid state. Valid states are: {valid_states}'}), 400

@app.route('/api/camera/parameters', methods=['GET'])
def get_camera_parameters():
    params = camera_service.settings_manager.get_parameters_definitions()
    return jsonify({"success": True, "parameters": params["parameters"]})

@app.route('/api/camera/settings', methods=['GET'])
def get_camera_settings():
    result = camera_service.get_camera_settings()
    return jsonify(result)

@app.route('/api/camera/settings', methods=['POST'])
def update_camera_settings():
    data = request.get_json()
    result = camera_service.update_camera_settings(data)
    return jsonify(result)
    
@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    return jsonify({
        'success': True,
        'telemetry': mavlink_handler.get_telemetry()
    })

@app.route('/api/app_settings', methods=['GET'])
def get_app_settings():
    settings = camera_service.settings_manager.get_app_settings_definitions()
    return jsonify({"success": True, "settings": settings.get("settings", [])})

@app.route('/api/app_settings', methods=['POST'])
def update_app_settings():
    try:
        data = request.get_json()
        success, message = camera_service.settings_manager.update_app_settings(data)
    
        camera_service.settings_manager.apply_current_app_settings(
            state_machine, camera_handler, mavlink_handler
        )
        
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.after_request
def add_header(response):
    if 'static/' in request.path:
        response.cache_control.max_age = 86400  # 1 day in seconds
    return response

@app.route('/api/remote_pi_time', methods=['GET'])
def get_remote_pi_time():
    try:
        time_diff = mavlink_handler.get_remote_pi_time_diff()
        print(time_diff)
        return jsonify(time_diff)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/sync_system_time', methods=['POST'])
def sync_system_time():
    try:
        mavlink_handler.sync_system_time()
        return jsonify({"success": True, "message": "System time synchronized"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    modify_mtu()
    threading.Thread(target=frame_saver_worker, daemon=True).start()
    mavlink_handler.start_mavlink_thread()
    camera_handler.start_camera_thread()
    socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
