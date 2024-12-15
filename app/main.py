import threading
import time
import base64

from flask import Flask, send_file, render_template
from flask_socketio import SocketIO
from vmbpy import *

from gstreamer import GstContext, GstPipeline, GstApp, Gst, GstVideo, GstPipeline
import gstreamer.utils as gst_utils
import utils
from handlers import handlers

import cProfile
import pstats
import io

import shutil

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject  
import numpy as np

import typing as typ

import cv2


app = Flask(__name__)
socketio = SocketIO(app)

is_recording = False  # Global variable to control recording state
was_recording = False  # Global variable to track previous recording state
record_folder = "transect"  # Default folder name

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile=settings/current.xml name=vimbasrc ! "
                    "video/x-bayer,format=rggb ! bayer2rgb ! videoconvert ! "
                    # "video/x-raw,format=RGB ! "
                    "tee name=t "

                    "t. ! queue ! "
                    "videoscale ! capsfilter name=capsfilter_stream caps=video/x-raw,width=1028,height=752 ! "
                    "jpegenc ! "
                    # "fakesink "
                    "multifilesink name=filesink_stream location=/home/pi/Repos/avt/stream.jpg "

                    "t. ! queue ! "
                    # "valve name=record_valve drop=false ! "
                    # "jpegenc ! "
                    # "multifilesink name=filesink_record location=/home/pi/Repos/avt/recordings/stream.jpg post-messages=true")
                    "videoconvert ! "
                    "video/x-raw,format=RGB ! "
                    "appsink name=appsink_record emit-signals=false")




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
    return send_file('/home/pi/Repos/avt/recordings/stream.jpg', mimetype='image/jpeg')

@app.route('/parameters')
def parameters():
    parameters = utils.json.get_parameters('settings/parameters.json')
    values = utils.xml.get_values_from_xml('settings/current.xml', parameters)
    
    print(f" Parameters: {parameters}")
    print(f" Values : {values}")

    return render_template('parameters.html', parameters=parameters, values=values)


def emit_images():
    global is_recording, was_recording
    last_image_data = None

    while True:
        with open('/home/pi/Repos/avt/stream.jpg', 'rb') as image_file:
            image_data = image_file.read()
            if image_data != last_image_data:
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                socketio.emit('image_update', {'image': encoded_image})
                last_image_data = image_data
        time.sleep(0.1)  # Emit images at 10 frames per second (100 ms delay)


def main():
    global is_recording, was_recording, record_folder
    was_recording = False  # Initialize was_recording

    utils.camera.wait_for_camera('DEV_000A4700155E')
    utils.network.modify_mtu()

    utils.storage.ensure_stream_image_exists()

    try:
        with GstContext(), GstPipeline(DEFAULT_PIPELINE) as pipeline:         
            
            # utils.pipeline.setup_pipeline(pipeline)

            def handle_toggle_recording_wrapper(data):
                global is_recording, record_folder
                is_recording, record_folder = handlers.handle_toggle_recording(data, pipeline)

            socketio.on_event('toggle_recording', handle_toggle_recording_wrapper)
            socketio.on_event('update_parameters', lambda data: handlers.handle_update_parameters(data, pipeline))
            socketio.on_event('reset_parameters', lambda: handlers.handle_reset_parameters(pipeline))
            socketio.on_event('restart_pipeline', lambda: utils.pipeline.restart_pipeline(pipeline))

            image_thread = threading.Thread(target=emit_images)
            image_thread.daemon = True
            image_thread.start()

            pipeline.get_by_name("filesink_stream").set_state(Gst.State.NULL)
            pipeline.get_by_name("filesink_stream").set_state(Gst.State.PLAYING)

            while True:
                if not pipeline.is_done:
                    if is_recording and not was_recording:
                        utils.pipeline.recording.start(pipeline, record_folder)
                    elif not is_recording and was_recording:
                        utils.pipeline.recording.stop(pipeline)
                    
                    was_recording = is_recording
                time.sleep(.25)
                    
    finally:
        print("Cleaning up and saving memory profile log...")


if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()

    try:
        thread = threading.Thread(target=lambda: socketio.run(app, host='192.168.2.3', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True))
        thread.daemon = True
        thread.start()
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        with open('/home/pi/Repos/avt/profile_output.txt', 'w') as f:
            f.write(s.getvalue())
        print("Profile data saved to /home/pi/Repos/avt/profile_output.txt")
