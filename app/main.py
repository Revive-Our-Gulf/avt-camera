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

from flask import Flask, send_file, render_template, Response, jsonify
from flask_socketio import SocketIO, emit
from PIL import Image
from vmbpy import *

from gstreamer import GstPipeline, GstContext, Gst
from utils import network_utils, record_utils, camera_utils, xml_utils, json_utils, pipeline_utils
from handlers import handlers

from memory_profiler import profile, LogFile

app = Flask(__name__)
socketio = SocketIO(app)

is_recording = False  # Global variable to control recording state
was_recording = False  # Global variable to track previous recording state
record_folder = "transect"  # Default folder name

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile=settings/current.xml name=vimbasrc ! "
                    "video/x-bayer,format=rggb ! bayer2rgb ! videoconvert ! tee name=t "

                    "t. ! queue ! videoscale ! capsfilter name=capsfilter_stream caps=video/x-raw,width=2056,height=1504 ! "
                    "jpegenc ! multifilesink name=filesink_stream location=Recordings/stream.jpg "

                    "t. ! queue ! valve name=record_valve drop=true ! jpegenc ! "
                    "multifilesink name=filesink_record location=Recordings/")


@app.route("/")
def main():
    return render_template('index.html')

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
    parameters = json_utils.get_parameters('settings/parameters.json')
    values = xml_utils.get_values_from_xml('settings/current.xml', parameters)
    
    print(f" Parameters: {parameters}")
    print(f" Values : {values}")

    return render_template('parameters.html', parameters=parameters, values=values)
    

@profile(stream=LogFile('memory_profile.log', reportIncrementFlag=False))
def main():
    global is_recording, was_recording, record_folder
    was_recording = False  # Initialize was_recording

    camera_utils.wait_for_camera('DEV_000A4700155E')
    network_utils.modify_mtu()

    try:
        with GstContext(), GstPipeline(DEFAULT_PIPELINE) as pipeline:         
            
            pipeline_utils.setup_pipeline(pipeline)

            def handle_toggle_recording_wrapper(data):
                global is_recording, record_folder
                is_recording, record_folder = handlers.handle_toggle_recording(data, pipeline)

            socketio.on_event('toggle_recording', handle_toggle_recording_wrapper)
            socketio.on_event('update_parameters', lambda data: handlers.handle_update_parameters(data, pipeline))
            socketio.on_event('reset_parameters', lambda: handlers.handle_reset_parameters(pipeline))
            socketio.on_event('restart_pipeline', lambda: pipeline_utils.restart_pipeline(pipeline))

            while True:
                if not pipeline.is_done:
                    if is_recording and not was_recording:
                        pipeline_utils.start_recording(pipeline, record_folder)
                    elif not is_recording and was_recording:
                        pipeline_utils.stop_recording(pipeline)
                    

                    with open('Recordings/stream.jpg', 'rb') as image_file:
                        image_data = image_file.read()
                        encoded_image = base64.b64encode(image_data).decode('utf-8')
                        socketio.emit('image_update', {'image': encoded_image})
                    
                    was_recording = is_recording
                time.sleep(.25)
                    
    finally:
        print("Cleaning up and saving memory profile log...")

if __name__ == "__main__":
    thread = threading.Thread(target=lambda: socketio.run(app, host='192.168.2.3', port=5000, debug=True, use_reloader=False))
    thread.daemon = True
    thread.start()
    main()
