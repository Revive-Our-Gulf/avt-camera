import argparse
import io
import os
import sys
import threading
import time
import base64
import json
from pathlib import Path
from typing import Optional

from flask import Flask, send_file, render_template, Response
from flask_socketio import SocketIO, emit
from PIL import Image
from vmbpy import *

from gstreamer import GstPipeline, GstContext, Gst
from utils import network_utils, record_utils, camera_utils, xml_utils
import handlers as handlers

from memory_profiler import profile, LogFile

app = Flask(__name__)
socketio = SocketIO(app)

is_recording = False  # Global variable to control recording state
was_recording = False  # Global variable to track previous recording state
record_folder = "transect"  # Default folder name

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile=settings/current.xml name=vimbasrc ! "
                    "video/x-raw,format=RGB ! videoconvert ! tee name=t "

                    "t. ! queue ! interpipesink name=src_stream "

                    "t. ! queue ! interpipesink name=src_record "
                    
                    "interpipesrc name=interpipesrc_stream listen-to=src_stream ! "
                    "queue leaky=downstream max-size-buffers=1 ! videoscale ! video/x-raw,width=640,height=480 ! jpegenc ! "
                    "multifilesink name=filesink_stream location=Recordings/stream.jpg "

                    "interpipesrc name=interpipesrc_record listen-to=src_record ! "
                    "queue leaky=downstream max-size-buffers=1 ! valve name=record_valve ! jpegenc ! "
                    "multifilesink name=filesink_record location=Recordings/test_stream_jpeg_1/frame_%05d.jpg"
)

@app.route("/")
def main():
    return render_template('index_record.html')

@app.route("/record")
def record_input():
    return render_template('record_input.html')

@app.route('/stream')
def stream():
    return render_template('stream.html')

@app.route('/last_frame')
def last_frame():
    return send_file('Recordings/stream.jpg', mimetype='image/jpeg')

@app.route('/parameters')
def parameters():
    # Load the parameters from the JSON file
    with open('settings/parameters.json') as f:
        parameters = json.load(f)

    return render_template('parameters.html', parameters=parameters)

@profile(stream=LogFile('memory_profile.log', reportIncrementFlag=False))
def main():
    global is_recording, was_recording, record_folder
    was_recording = False  # Initialize was_recording

    camera_utils.wait_for_camera('DEV_000A4700155E')
    network_utils.modify_mtu()

    try:
        with GstContext(), GstPipeline(DEFAULT_PIPELINE) as pipeline:
            
            filesink_record = pipeline.get_by_name("filesink_record")
            filesink_record.set_state(Gst.State.NULL)

            record_valve = pipeline.get_by_name("record_valve")
            record_valve.set_property("drop", True)

            def handle_toggle_recording_wrapper(data):
                global is_recording, record_folder
                is_recording, record_folder = handlers.handle_toggle_recording(data, pipeline)

            socketio.on_event('toggle_recording', handle_toggle_recording_wrapper)
            socketio.on_event('update_parameters', lambda data: handlers.handle_update_parameters(data, pipeline))
            socketio.on_event('restore_default_parameters', lambda data: handlers.handle_restore_default_parameters(data, pipeline))

            while not pipeline.is_done:
                if is_recording and not was_recording:
                    print("Starting recording...")
                    record_path = record_utils.create_recording_folder(record_folder)
                    filesink_record.set_property("location", f"{record_path}/frame_%04d.jpg")
                    filesink_record.set_state(Gst.State.PLAYING)
                    record_valve.set_property("drop", False)
                elif not is_recording and was_recording:
                    print("Stopping recording...")
                    record_valve.set_property("drop", True)
                    filesink_record.set_state(Gst.State.PAUSED)
                
                # Read the latest frame and emit it via WebSocket
                with open('Recordings/stream.jpg', 'rb') as image_file:
                    image_data = image_file.read()
                    encoded_image = base64.b64encode(image_data).decode('utf-8')
                    socketio.emit('image_update', {'image': encoded_image})
                
                was_recording = is_recording
                time.sleep(.3)
             
    finally:
        print("Cleaning up and saving memory profile log...")

if __name__ == "__main__":
    thread = threading.Thread(target=lambda: socketio.run(app, host='192.168.2.3', port=5000, debug=True, use_reloader=False))
    thread.daemon = True
    thread.start()
    main()