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

is_recording = False  # Global variable to control recording state
was_recording = False  # Global variable to track previous recording state


# DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile={SETTINGS_FILE_PATH}  ! "
#                     "video/x-raw,format=RGB ! videoconvert ! "
#                     "interpipesink name=src "

#                     "interpipesrc name=interpipesrc_stream listen-to=src ! "
#                     "queue leaky=downstream max-size-buffers=1 ! jpegenc ! "
#                     "multifilesink name=filesink_stream location=Recordings/stream.jpg "

#                     "interpipesrc name=interpipesrc_record listen-to=src ! "
#                     "queue leaky=downstream max-size-buffers=1 ! jpegenc ! "
#                     "multifilesink name=filesink_record location=Recordings/test_1/frame_%05d.jpg"
# )

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile={SETTINGS_FILE_PATH} ! "
                    "video/x-raw,format=RGB ! videoconvert ! tee name=t "

                    "t. ! queue ! interpipesink name=src_stream "

                    "t. ! queue ! interpipesink name=src_record "
                    
                    "interpipesrc name=interpipesrc_stream listen-to=src_stream ! "
                    "queue leaky=downstream max-size-buffers=1 ! videoscale ! video/x-raw,width=640,height=480 ! jpegenc ! "
                    "multifilesink name=filesink_stream location=Recordings/stream.jpg "

                    "interpipesrc name=interpipesrc_record listen-to=src_record ! "
                    "queue leaky=downstream max-size-buffers=1 ! jpegenc ! "
                    "multifilesink name=filesink_record location=Recordings/test_stream_jpeg_1/frame_%05d.jpg"
)
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pipeline", required=False,
                default=DEFAULT_PIPELINE, help="Gstreamer pipeline without gst-launch")
ap.add_argument("-f", "--filename", required=True,
                default="output", help="Output filename (no extension)")
ap.add_argument("-c", "--camera", required=False,
                default="DEV_000A4700155E", help="Name of the GigE camera to check")

args = vars(ap.parse_args())

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/stream')
def last_frame():
    return send_file('Recordings/stream.jpg', mimetype='image/jpeg')


def print_usage():
    print('Usage:')
    print('    python synchronous_grab.py [camera_id]')
    print('    python synchronous_grab.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print()

@profile(stream=LogFile('memory_profile.log', reportIncrementFlag=False))
def main():
    print_usage()
    camera_utils.wait_for_camera(args['camera'])
    network_utils.modify_mtu()

    is_recording = False
    was_recording = True

    try:
        with GstContext(), GstPipeline(args['pipeline']) as pipeline:
            
            filesink_record = pipeline.get_by_name("filesink_record")
            # filesink_record.set_state(Gst.State.NULL)

            record_path = record_utils.create_recording_folder(args['filename'])
            filesink_record.set_property("location", f"{record_path}/frame_%04d.jpg")
            
            count = 0
            while not pipeline.is_done and count < 600:
                if is_recording and not was_recording:
                    filesink_record.set_state(Gst.State.PLAYING)
                elif not is_recording and was_recording:
                    filesink_record.set_state(Gst.State.NULL)
                
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
    thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False))
    thread.daemon = True
    thread.start()
    main()