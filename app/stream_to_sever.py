from flask import Flask, send_file, render_template_string, Response
import threading
import time
import sys
from typing import Optional
from vmbpy import *
import io
from PIL import Image

host_name = "0.0.0.0"
port = "5000"
app = Flask(__name__)

last_frame = None
last_frame_io = io.BytesIO()
frame_event = threading.Event()

@app.route("/")
def main():
    return render_template_string('''
        <html>
            <head>
                <style>
                    img {
                        width: 100%;
                        height: auto;
                    }
                </style>
            </head>
            <body>
                <h1>Live Feed</h1>
                <img id="live_feed" src="/last_frame" alt="Live Feed"/>
                <script type="text/javascript">
                    var evtSource = new EventSource("/stream");
                    evtSource.onmessage = function(e) {
                        document.getElementById("live_feed").src = "/last_frame?" + new Date().getTime();
                    };
                </script>
            </body>
        </html>
    ''')

@app.route('/last_frame')
def get_last_frame():
    global last_frame_io
    if last_frame_io.getbuffer().nbytes > 0:
        last_frame_io.seek(0)
        return send_file(last_frame_io, mimetype='image/jpeg')
    else:
        return "No frame available", 404

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            frame_event.wait()  # Wait for a new frame to be available
            frame_event.clear()  # Clear the event
            yield 'data: update\n\n'
    return Response(event_stream(), mimetype="text/event-stream")

def print_preamble():
    print('//////////////////////////////////////')
    print('/// VmbPy Synchronous Grab Example ///')
    print('//////////////////////////////////////\n')

def print_usage():
    print('Usage:')
    print('    python synchronous_grab.py [camera_id]')
    print('    python synchronous_grab.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print()

def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)

def parse_args() -> Optional[str]:
    args = sys.argv[1:]
    argc = len(args)

    for arg in args:
        if arg in ('/h', '-h'):
            print_usage()
            sys.exit(0)

    if argc > 1:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return None if argc == 0 else args[0]

def get_camera(camera_id: Optional[str]) -> Camera:
    with VmbSystem.get_instance() as vmb:
        if camera_id:
            try:
                return vmb.get_camera_by_id(camera_id)

            except VmbCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

        else:
            cams = vmb.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')

            return cams[0]

def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            stream = cam.get_streams()[0]
            stream.GVSPAdjustPacketSize.run()
            while not stream.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VmbFeatureError):
            pass

def main():
    global last_frame, last_frame_io
    print_preamble()
    cam_id = parse_args()

    recording = False

    with VmbSystem.get_instance():
        with get_camera(cam_id) as cam:
            setup_camera(cam)
            settings_file = 'strobe_configured.xml'.format(cam.get_id())

            cam.load_settings(settings_file, PersistType.All)
            print("--> Feature values have been loaded from given file '%s'" % settings_file)

            # Acquire frames continuously
            previous_time = None
            for frame in cam.get_frame_generator(limit=None, timeout_ms=3000):
                last_frame = frame
                frame_event.set()  # Signal that a new frame is available
                print(f"Frame acquired: Size={frame.get_width()}x{frame.get_height()}, Pixel Format={frame.get_pixel_format()}")

                # Save the frame to a BytesIO object
                frame_data = frame.as_numpy_ndarray()
                img = Image.fromarray(frame_data)
                last_frame_io = io.BytesIO()
                img.save(last_frame_io, 'JPEG')

                if previous_time is not None:
                    time_diff = time.time() - previous_time
                    print(f"Time between frames: {time_diff:.2f} seconds")
                previous_time = time.time()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()
    main()