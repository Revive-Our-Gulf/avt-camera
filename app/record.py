import time
import argparse
from utils import network_utils, record_utils, camera_utils

from gstreamer import GstPipeline, GstContext
import os

# DEFAULT_PIPELINE = ("aravissrc ! "
#                     "video/x-raw,format=RGB ! videoconvert ! "
#                     "interpipesink name=src "

#                     # "interpipesrc name=interpipesrc_stream listen-to=src ! "
#                     # "queue max-size-buffers=1 ! videoconvert ! video/x-raw,width=514,height=376 ! videoconvert ! "
#                     # "fakesink "

#                     "interpipesrc name=interpipesrc_record listen-to=src ! "
#                     "queue leaky=downstream max-size-buffers=2 ! jpegenc ! "
#                     "multifilesink name=filesink location=Recordings/test_1/frame_%05d.jpg"
# )

# DEFAULT_PIPELINE = ("aravissrc ! "
#                     "video/x-raw,format=RGB ! videoconvert ! "
#                     "interpipesink name=src "

#                     "interpipesrc name=interpipesrc_stream listen-to=src ! "
#                     "queue max-size-buffers=1 ! videoconvert ! video/x-raw,width=514,height=376 ! videoconvert ! "
#                     "x264enc speed-preset=veryfast tune=zerolatency bitrate=800 ! "
#                     "h264parse ! "
#                     "rtspclientsink location=rtsp://localhost:8554/stream "

#                     "interpipesrc name=interpipesrc_record listen-to=src ! "
#                     "queue leaky=downstream max-size-buffers=2 ! jpegenc ! "
#                     "multifilesink name=filesink location=Recordings/test_1/frame_%05d.jpg"
# )

DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile={SETTINGS_FILE_PATH}  ! "
                    "video/x-raw,format=RGB ! videoconvert ! "
                    "interpipesink name=src "

                    "interpipesrc name=interpipesrc_record listen-to=src ! "
                    "queue leaky=downstream max-size-buffers=2 ! jpegenc ! "
                    "multifilesink name=filesink location=Recordings/test_1/frame_%05d.jpg"
)


ap = argparse.ArgumentParser()
ap.add_argument("-p", "--pipeline", required=False,
                default=DEFAULT_PIPELINE, help="Gstreamer pipeline without gst-launch")
ap.add_argument("-f", "--filename", required=True,
                default="output", help="Output filename (no extension)")
ap.add_argument("-c", "--camera", required=False,
                default="DEV_000A4700155E", help="Name of the GigE camera to check")

args = vars(ap.parse_args())

if __name__ == '__main__':
    camera_utils.wait_for_camera(args['camera'])
    network_utils.modify_mtu()

    with GstContext(), GstPipeline(args['pipeline']) as pipeline:
        # interpipesrc_record = pipeline.get_by_name("interpipesrc_record")

        
        filesink = pipeline.get_by_name("filesink")
        record_path = record_utils.create_recording_folder(args['filename'])
        filesink.set_property("location", f"{record_path}/frame_%04d.jpg")
        
        while not pipeline.is_done:
            time.sleep(.1)
