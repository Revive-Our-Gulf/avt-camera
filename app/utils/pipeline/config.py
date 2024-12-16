import time
from gstreamer import Gst
from utils import storage
from .valve import update_valve
from . import appsink


def setup(pipeline):
    appsink.connect(pipeline)
    appsink.stop()

    pipeline.get_by_name("filesink_stream").set_state(Gst.State.NULL)
    pipeline.get_by_name("filesink_stream").set_state(Gst.State.PLAYING)
    


def restart(pipeline):
    pipeline.shutdown()
    pipeline.startup()

    while not pipeline.is_active:
        print("Waiting for pipeline to Restart...")
        time.sleep(.1)
    
    setup(pipeline)

    print("Camera restarted successfully")

