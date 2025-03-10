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
    global is_recording, record_folder, start_time

    is_recording = not is_recording

    if is_recording:
        start_time = time.time()
        print(f"Recording started in folder {record_folder}")
    else:
        start_time = 0
        print("Recording stopped.")

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


def emit_images():
    global is_recording, was_recording
    last_image_data = None

    while True:
        with open('/home/pi/Repos/avt-camera/stream.jpg', 'rb') as image_file:
            image_data = image_file.read()
            if image_data != last_image_data:
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                socketio.emit('image_update', {'image': encoded_image})
                last_image_data = image_data
        time.sleep(0.1)  # Emit images at 10 frames per second (100 ms delay)

def convert_jpegs_to_mjpeg(record_folder, fps=25):
    # Specify the folder containing the images
    output_video_path = record_folder + "/output.avi"
    fps = 2  # Frames per second of the video
    scale_factor = 0.125

    # Regex to match image filenames
    image_pattern = re.compile(r"IMG_(\d+)_\(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\)\.jpg")

    # Get a sorted list of matching image filenames
    images = [
        img for img in os.listdir(record_folder)
        if image_pattern.match(img)
    ]
    images.sort(key=lambda x: int(image_pattern.match(x).group(1)))

    # Check if images are found
    if not images:
        print("No matching images found in the folder.")
        exit()

    # Read the first image to get the dimensions
    first_image_path = os.path.join(record_folder, images[0])
    first_image = cv2.imread(first_image_path)
    original_height, original_width, _ = first_image.shape

    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    new_size = (new_width, new_height)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # MJPEG codec
    out = cv2.VideoWriter(output_video_path, fourcc, fps, new_size)

    # Write each image to the video
    for image_file in images:
        image_path = os.path.join(record_folder, image_file)
        frame = cv2.imread(image_path)

        # Resize the frame
        downscaled_frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

        # Write the downscaled frame to the video
        out.write(downscaled_frame)

    # Release the VideoWriter
    out.release()

    print(f"Downscaled video saved as {output_video_path}")         


def main():
    global is_recording, was_recording, record_folder, start_time
    was_recording = False  # Initialize was_recording

    # utils.camera.wait_for_camera('DEV_000A4700155E')
    utils.network.modify_mtu()

    utils.storage.ensure_stream_image_exists()

    try:
        with GstContext(), GstPipeline(DEFAULT_PIPELINE) as pipeline:         
            
            utils.pipeline.config.setup(pipeline)

            

            def handle_restart_pipeline():
                global is_recording, start_time
                utils.pipeline.config.restart(pipeline)
                is_recording = False
                start_time = 0


            socketio.on_event('toggle_recording', handle_toggle_recording_wrapper)
            socketio.on_event('update_parameters', lambda data: handlers.handle_update_parameters(data, pipeline))
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
                    
                    was_recording = is_recording
                time.sleep(.25)
                    
    finally:
        print("Cleaning up and saving memory profile log...")


if __name__ == "__main__":
    thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False, allow_unsafe_werkzeug=True))
    thread.daemon = True
    thread.start()
    main()