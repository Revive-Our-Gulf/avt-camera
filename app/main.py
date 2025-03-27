import threading
import time
import base64
from datetime import datetime

from flask import Flask, send_file, render_template
from flask_socketio import SocketIO
from vmbpy import *

from gstreamer import GstContext, GstPipeline, GstApp, Gst, GstVideo, GstPipeline
import utils
from handlers import handlers

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject  
import logging
import subprocess
import cv2
import os
import re

import psutil

from flask import Flask, request, jsonify

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


app = Flask(__name__)
socketio = SocketIO(app)

is_recording = False  # Global variable to control recording state
was_recording = False  # Global variable to track previous recording state
is_preview_active = False
record_folder = None # Default folder name
transect_name = "transect"
start_time = 0  # Variable to track the start time of the recording

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile=/home/pi/Repos/avt-camera/app/settings/current.xml name=vimbasrc ! "
                    "video/x-bayer,format=rggb ! bayer2rgb ! videoconvert ! "
                    "tee name=t "

                    "t. ! queue ! "
                    "videoscale ! capsfilter name=capsfilter_stream caps=video/x-raw,width=1028,height=752 ! "
                    "jpegenc ! "
                    "multifilesink name=filesink_stream location=/home/pi/Repos/avt-camera/stream.jpg "

                    "t. ! queue ! "
                    "videoconvert ! "
                    "video/x-raw,format=RGB ! "
                    "appsink name=appsink_record emit-signals=true")

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/cockpit")
def cockpit():
    return render_template('cockpit.html')

@app.route("/record")
def record_input():
    return render_template('record_input.html')

@app.route('/stream')
def stream():
    return render_template('stream.html')

@app.route('/last_frame')
def last_frame():
    return send_file('/home/pi/Repos/avt-camera/recordings/stream.jpg', mimetype='image/jpeg')

@app.route('/parameters')
def parameters():
    parameters = utils.json.get_parameters('/home/pi/Repos/avt-camera/app/settings/parameters.json')
    values = utils.xml.get_values_from_xml('/home/pi/Repos/avt-camera/app/settings/current.xml', parameters)
    
    print(f" Parameters: {parameters}")
    print(f" Values : {values}")

    return render_template('parameters.html', parameters=parameters, values=values)

@app.route('/files')
def files():
    return render_template('filebrowser.html')


@app.route('/set_transect_name', methods=['POST'])
def set_transect_name():
    global transect_name
    data = request.get_json()
    if data and 'transect_name' in data:
        transect_name = data['transect_name'].strip() or 'transect'
    return jsonify(status="success")

@app.route('/get_transect_name')
def get_transect_name():
    global transect_name
    return jsonify(transect_name=transect_name)


@socketio.on('toggle_recording')
def handle_toggle_recording_wrapper(data=None):
    global is_recording, record_folder, start_time, is_preview_active, pipeline
    
    # If not recording and not previewing, start preview first
    if not is_recording and not is_preview_active:
        try:
            utils.pipeline.config.start(pipeline)
            is_preview_active = True
            socketio.emit('preview_state', {'isActive': is_preview_active})
        except Exception as e:
            logging.error(f"Failed to start preview: {e}")
            socketio.emit('error', {'message': f'Failed to start camera preview: {str(e)}'})
            return
    
    # Toggle recording state
    is_recording = not is_recording
    
    if is_recording:
        start_time = time.time()
        if data and 'folderName' in data:
            transect_name = data['folderName'].strip() or 'transect'
        print(f"Recording started with name {transect_name}")
    else:
        start_time = 0
        print("Recording stopped.")
        # Automatically stop the preview when recording stops
        try:
            utils.pipeline.config.stop(pipeline)
            is_preview_active = False
            socketio.emit('preview_state', {'isActive': is_preview_active})
            print("Camera preview stopped automatically after recording")
        except Exception as e:
            logging.error(f"Failed to stop preview after recording: {e}")

    # Emit the updated state to all clients
    elapsed_time = (time.time() - start_time) if is_recording else 0
    socketio.emit('current_recording_state', {'isRecording': is_recording, 'elapsedTime': elapsed_time})


@socketio.on('get_recording_state')
def handle_get_recording_state(data=None):
    global start_time, is_recording
    elapsed_time = (time.time() - start_time) if is_recording else 0
    socketio.emit('current_recording_state', {'isRecording': is_recording, 'elapsedTime': elapsed_time})

@socketio.on('get_strobe_state')
def handle_get_strobe_state():
    parameters = utils.json.get_parameters('/home/pi/Repos/avt-camera/app/settings/parameters.json')
    values = utils.xml.get_values_from_xml('/home/pi/Repos/avt-camera/app/settings/current.xml', parameters)
    current_value = values.get('LineSource+Line2', 'Off')
    socketio.emit('strobe_state', {'value': current_value})

@socketio.on('get_storage')
def emit_storage_info():
    print("Emitting storage info...")
    disk_usage = psutil.disk_usage('/')
    free_space_gb = disk_usage.free / (1024 * 1024 * 1024)
    total_space_gb = disk_usage.total / (1024 * 1024 * 1024)
    socketio.emit('storage_info', {
        'free_space_gb': free_space_gb,
        'total_space_gb': total_space_gb
    })

@socketio.on('get_time_sync')
def check_time_sync():
    try:
        result = subprocess.run(['chronyc', 'tracking'], capture_output=True, text=True)
        if '192.168.2.2' in result.stdout and 'Stratum         : ' in result.stdout:
            # Extract the Last offset value
            last_offset_line = next(line for line in result.stdout.split('\n') if 'Last offset' in line)
            last_offset = float(last_offset_line.split(':')[1].strip().split()[0])
            if abs(last_offset) < 1e-6:
                human_readable_offset = f"{last_offset * 1e9:.1f} ns"
            elif abs(last_offset) < 1e-3:
                human_readable_offset = f"{last_offset * 1e6:.1f} µs"
            elif abs(last_offset) < 1:
                human_readable_offset = f"{last_offset * 1e3:.1f} ms"
            elif abs(last_offset) < 60:
                human_readable_offset = f"{last_offset:.1f} s"
            elif abs(last_offset) < 3600:
                human_readable_offset = f"{last_offset / 60:.1f} min"
            else:
                human_readable_offset = f"{last_offset / 3600:.1f} h"
            socketio.emit('time_sync_status', {'status': 'success', 'message': f'Time is synced with BlueOS. Last offset: {human_readable_offset}'})
        else:
            socketio.emit('time_sync_status', {'status': 'error', 'message': 'Time is not synced with BlueOS'})
    except Exception as e:
        socketio.emit('time_sync_status', {'status': 'error', 'message': str(e)})

@socketio.on('start_preview')
def handle_start_preview():
    global is_preview_active, pipeline
    
    if pipeline is None:
        socketio.emit('error', {'message': 'Camera not available. Please restart the application.'})
        return
    
    if not is_preview_active:
        try:
            # Use the existing start function from config
            utils.pipeline.config.start(pipeline)
            is_preview_active = True
            socketio.emit('preview_state', {'isActive': is_preview_active})
        except Exception as e:
            logging.error(f"Failed to start preview: {e}")
            socketio.emit('error', {'message': f'Failed to start camera preview: {str(e)}'})

@socketio.on('stop_preview')
def handle_stop_preview():
    global is_preview_active, pipeline, is_recording
    
    if pipeline is None:
        socketio.emit('error', {'message': 'Camera not available. Please restart the application.'})
        return
    
    # Don't allow stopping preview while recording
    if is_recording:
        socketio.emit('error', {'message': 'Cannot stop preview while recording is active'})
        return
    
    if is_preview_active:
        try:
            # Use the existing stop function from config
            utils.pipeline.config.stop(pipeline)
            is_preview_active = False
            socketio.emit('preview_state', {'isActive': is_preview_active})
        except Exception as e:
            logging.error(f"Failed to stop preview: {e}")
            socketio.emit('error', {'message': f'Failed to stop camera preview: {str(e)}'})

@socketio.on('get_preview_state')
def handle_get_preview_state():
    global is_preview_active
    socketio.emit('preview_state', {'isActive': is_preview_active})


def emit_images():
    global is_recording, was_recording, is_preview_active
    last_image_data = None

    while True:
        try:
            # Only try to read the image if preview is active
            if is_preview_active:
                with open('/home/pi/Repos/avt-camera/stream.jpg', 'rb') as image_file:
                    image_data = image_file.read()
                    if image_data != last_image_data:
                        encoded_image = base64.b64encode(image_data).decode('utf-8')
                        socketio.emit('image_update', {'image': encoded_image})
                        last_image_data = image_data
        except Exception as e:
            # If there's an error reading the file, just continue
            pass
            
        time.sleep(0.1)

def main():
    global is_recording, was_recording, record_folder, start_time, is_preview_active
    was_recording = False  # Initialize was_recording

    # utils.camera.wait_for_camera('DEV_000A4700155E')
    utils.network.modify_mtu()
    utils.storage.ensure_stream_image_exists()

    try:
        with GstContext(), GstPipeline(DEFAULT_PIPELINE) as pipeline:         
            
            globals()['pipeline'] = pipeline            

            def handle_restart_pipeline():
                global is_recording, start_time
                utils.pipeline.config.restart(pipeline)
                is_recording = False
                start_time = 0


            socketio.on_event('toggle_recording', handle_toggle_recording_wrapper)
            socketio.on_event('update_parameters', lambda data: handlers.handle_update_parameters(data, pipeline, is_preview_active, is_recording))
            socketio.on_event('reset_parameters', lambda: handlers.handle_reset_parameters(pipeline))
            socketio.on_event('restart_pipeline', handle_restart_pipeline)

            image_thread = threading.Thread(target=emit_images)
            image_thread.daemon = True
            image_thread.start()

            modified_record_folder = None

            while True:
                if not pipeline.is_done:
                    if is_recording and not was_recording:
                        modified_record_folder = utils.pipeline.recording.start(pipeline, transect_name)
                        start_time = time.time()
                    elif not is_recording and was_recording:
                        utils.pipeline.recording.stop(pipeline)
                        start_time = 0
                        # We don't need to stop the preview here since it's already handled in the toggle_recording handler
                    
                    was_recording = is_recording
                time.sleep(.25)
                    
    finally:
        print("Cleaning up and saving memory profile log...")


if __name__ == "__main__":
    thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False, allow_unsafe_werkzeug=True))
    thread.daemon = True
    thread.start()
    main()