import time
import argparse
from utils import network_utils, record_utils, camera_utils

from gstreamer import GstPipeline, GstContext
import os

SETTINGS_FILE_PATH = "/home/pi/Repos/avt/app/settings/strobe.xml"

DEFAULT_PIPELINE = (f"vimbasrc camera=DEV_000A4700155E settingsfile={SETTINGS_FILE_PATH} ! "
                    "queue ! videoconvert ! queue ! videoscale ! video/x-raw,width=640,height=480 ! "
                    "queue ! x264enc speed-preset=veryfast tune=zerolatency bitrate=800 ! "
                    "queue ! rtspclientsink location=rtsp://localhost:8554/mystream"
)

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pipeline", required=False,
                default=DEFAULT_PIPELINE, help="Gstreamer pipeline without gst-launch")
ap.add_argument("-f", "--filename", required=False,
                default="output", help="Output filename (no extension)")
ap.add_argument("-c", "--camera", required=False,
                default="DEV_000A4700155E", help="Name of the GigE camera to check")

args = vars(ap.parse_args())

if __name__ == '__main__':
    network_utils.modify_mtu()

    with GstContext(), GstPipeline(args['pipeline']) as pipeline:      
        while not pipeline.is_done:
            time.sleep(.1)