import time
from gstreamer import Gst
from app.core import storage
from . import appsink


def setup(pipeline):
    appsink.connect(pipeline)
    appsink.stop()

    pipeline.get_by_name("filesink_stream").set_state(Gst.State.NULL)
    pipeline.get_by_name("filesink_stream").set_state(Gst.State.PLAYING)
    
def start(pipeline):
    if not pipeline.is_active:
        pipeline.startup()

        while not pipeline.is_active:
            print("Waiting for pipeline to Restart...")
            time.sleep(.1)
        
        setup(pipeline)

        print("Camera restarted successfully")

def stop(pipeline):
    if pipeline.is_active:
        pipeline.shutdown()
        print("Camera stopped successfully")

def restart(pipeline):
    pipeline.shutdown()
    time.sleep(1)
    start(pipeline)

