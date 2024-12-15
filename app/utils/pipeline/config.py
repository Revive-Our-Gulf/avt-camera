import time
from gstreamer import Gst
from utils import storage
from .valve import update_valve
from . import appsink


def setup(pipeline):
    # filesink_record = pipeline.get_by_name("filesink_record")
    # filesink_record.set_state(Gst.State.NULL)

    update_valve(pipeline, enable=True)
    appsink.stop(pipeline)


def restart(pipeline):
    pipeline.shutdown()
    pipeline.startup()

    while not pipeline.is_active:
        print("Waiting for pipeline to Restart...")
        time.sleep(.1)
    
    setup(pipeline)

    print("Camera restarted successfully")

