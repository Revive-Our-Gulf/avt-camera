import os
from flask import Flask, Response, request, jsonify
from flask_socketio import SocketIO
from queue import Queue
import threading

from views import views_bp
from state_machine import CameraStateMachine, CameraState
from camera.camera_hardware_controller import CameraHardwareController
from camera.camera_application_service import CameraApplicationService
from detect_blur import set_focus_threshold, get_focus_threshold

app = Flask(__name__)
socketio = SocketIO(app)
app.register_blueprint(views_bp)

base_output_dir = "recordings"
os.makedirs(base_output_dir, exist_ok=True)

frame_save_queue = Queue(maxsize=30)

state_machine = CameraStateMachine()
camera_handler = CameraHardwareController(state_machine, frame_save_queue)
camera_service = CameraApplicationService(state_machine, camera_handler, socketio)



def generate_frames():
    while True:
        frame = camera_handler.get_latest_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def frame_saver_worker():
    while True:
        try:
            image, timestamp = frame_save_queue.get()
            folder = camera_service.current_recording_folder
            if folder:
                filename = os.path.join(folder, f"frame_{timestamp}.jpg")
                import cv2
                cv2.imwrite(filename, image)
                print(f"Saved frame to {filename}")
        except Exception as e:
            print(f"Error saving frame: {e}")

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
    
@app.route('/api/toggle_focus_mode', methods=['POST'])
def toggle_focus_mode():
    focus_mode = camera_handler.toggle_focus_mode()
    return jsonify({'success': True, 'focus_mode_enabled': focus_mode})

@app.route('/api/focus/tolerance', methods=['GET', 'POST'])
def focus_tolerance():
    if request.method == 'POST':
        data = request.get_json()
        threshold = data.get('threshold', 30)
        
        if threshold < 10 or threshold > 100:
            return jsonify({'success': False, 'error': 'Threshold must be between 10 and 100'})
            
        new_threshold = set_focus_threshold(threshold)
        return jsonify({'success': True, 'threshold': new_threshold})
    else:
        current_threshold = get_focus_threshold()
        return jsonify({'success': True, 'threshold': current_threshold})

if __name__ == '__main__':
    threading.Thread(target=frame_saver_worker, daemon=True).start()
    camera_handler.start_camera_thread()
    socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False)
