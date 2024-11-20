import argparse
import io
import os
import sys
import threading
import time
import base64
from typing import Optional

from flask import Flask, send_file, render_template, Response
from flask_socketio import SocketIO, emit
from PIL import Image
from vmbpy import *

from gstreamer import GstPipeline, GstContext, Gst
from utils import network_utils, record_utils, camera_utils

from memory_profiler import profile, LogFile

app = Flask(__name__)
socketio = SocketIO(app)

is_recording = False
was_recording = False  
record_folder = "transect" 

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile=settings/strobe.xml exposureauto=Continuous name=vimbasrc ! "
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
    return render_template('index_exposure.html')

@app.route('/stream')
def last_frame():
    return send_file('Recordings/stream.jpg', mimetype='image/jpeg')

@socketio.on('toggle_recording')
def handle_toggle_recording(data):
    global is_recording, record_folder
    is_recording = data['isRecording']
    record_folder = data['folderName']
    print(f"Recording state: {is_recording}, Folder: {record_folder}")

@socketio.on('update_exposure_time')
def handle_update_exposure_time(data, pipeline):
    exposure_time = data['exposureTime']
    print(f"Updating exposure time to: {exposure_time} ms")
    camera_src = pipeline.get_by_name("vimbasrc")
    camera_src.set_state(Gst.State.NULL)
    camera_src.set_property("exposuretime", int(exposure_time))
    camera_src.set_state(Gst.State.PLAYING)

@profile(stream=LogFile('memory_profile.log', reportIncrementFlag=False))
def main():
    global is_recording, was_recording, record_folder
    was_recording = False

    camera_utils.wait_for_camera('DEV_000A4700155E')
    network_utils.modify_mtu()

    try:
        with GstContext(), GstPipeline(DEFAULT_PIPELINE) as pipeline:
            
            filesink_record = pipeline.get_by_name("filesink_record")
            filesink_record.set_state(Gst.State.NULL)
            record_valve = pipeline.get_by_name("record_valve")
            record_valve.set_property("drop", True)

            
            
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

                socketio.on_event('update_exposure_time', lambda data: handle_update_exposure_time(data, pipeline))
                
                was_recording = is_recording
                time.sleep(.3)
    finally:
        print("Cleaning up and saving memory profile log...")

if __name__ == "__main__":
    thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False))
    thread.daemon = True
    thread.start()
    main()