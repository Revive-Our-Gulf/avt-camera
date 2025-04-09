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

from mavlink_handler import MavlinkHandler
import cv2
import piexif
import json
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)
app.register_blueprint(views_bp)
mavlink_handler = MavlinkHandler(socketio)

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
    def to_deg(value, loc):
        if value < 0:
            loc_value = loc[0]  # S or W
        elif value > 0:
            loc_value = loc[1]  # N or E
        else:
            loc_value = ""
            
        abs_value = abs(value)
        deg = int(abs_value)
        t1 = (abs_value-deg)*60
        min = int(t1)

        sec = (t1 - min)* 60
        sec_multiplier = 10000
        sec_int = int(sec * sec_multiplier)
        
        return ((deg, 1), (min, 1), (sec_int, sec_multiplier)), loc_value
        
    while True:
        try:
            image, now, frame_index = frame_save_queue.get()
            timestamp = now.strftime('%Y_%m_%d_%H-%M-%S') + f'-{int(now.microsecond / 10000):02d}'
            folder = camera_service.current_recording_folder
            if folder:
                filename = os.path.join(folder, f"IMG_{frame_index}_{timestamp}.jpg")
                
                telemetry = mavlink_handler.get_telemetry()
                
                cv2.imwrite(filename, image)
                
                if telemetry:
                    exif_dict = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}
                    
                    exif_dict["0th"][piexif.ImageIFD.DateTime] = now.strftime("%Y:%m:%d %H:%M:%S")

                    lat, lon, alt = None, None, None
                    
                    lat = float(telemetry['GLOBAL_POSITION_INT']['lat']) / 1e7
                    lon = float(telemetry['GLOBAL_POSITION_INT']['lon']) / 1e7

                    lat_deg = to_deg(lat, ["S", "N"])
                    lon_deg = to_deg(lon, ["W", "E"])
                    
                    exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_deg[1].encode()
                    exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_deg[1].encode()
                    
                    exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_deg[0]
                    exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_deg[0]    
                        
                    alt = float(telemetry['GLOBAL_POSITION_INT']['relative_alt']) / 1e3   
                    exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (int(abs(alt) * 1000), 1000)
                    exif_dict["GPS"][piexif.GPSIFD.GPSAltitudeRef] = 1 if alt < 0 else 0    

                    satellites = telemetry['GPS_RAW_INT']['satellites_visible']
                    exif_dict["GPS"][piexif.GPSIFD.GPSSatellites] = str(satellites).encode()

                    time_in_seconds = telemetry['GLOBAL_POSITION_INT']['time_boot_ms'] // 1000
                    hours = time_in_seconds // 3600
                    minutes = (time_in_seconds % 3600) // 60
                    seconds = time_in_seconds % 60
                    exif_dict["GPS"][piexif.GPSIFD.GPSTimeStamp] = ((hours, 1), (minutes, 1), (seconds, 1))

                    exif_dict["Exif"][piexif.ExifIFD.UserComment] = json.dumps({
                        "lat": lat,
                        "lon": lon,
                        "alt": alt
                    }).encode()

                    exif_bytes = piexif.dump(exif_dict)        
                    piexif.insert(exif_bytes, filename)

                    print(f"Saved frame with telemetry to {filename}")
                else:
                    print(f"Saved frame to {filename} (no telemetry available)")
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
    
@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    return jsonify({
        'success': True,
        'telemetry': mavlink_handler.get_telemetry()
    })


if __name__ == '__main__':
    threading.Thread(target=frame_saver_worker, daemon=True).start()
    mavlink_handler.start_mavlink_thread()
    camera_handler.start_camera_thread()
    socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False)
