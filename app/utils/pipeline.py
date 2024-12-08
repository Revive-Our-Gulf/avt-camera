import time
from gstreamer import Gst
from utils import storage



def update_valve(pipeline, enable=True):
    record_valve = pipeline.get_by_name("record_valve")
    record_valve.set_property("drop", enable)


def restart_pipeline(pipeline):
    pipeline.shutdown()
    pipeline.startup()
    while not pipeline.is_active:
        print("Waiting for pipeline to Restart...")
        time.sleep(.1)
    
    setup_pipeline(pipeline)

    print("Camera restarted successfully")


def setup_pipeline(pipeline):
    filesink_record = pipeline.get_by_name("filesink_record")
    filesink_record.set_state(Gst.State.NULL)

    update_valve(pipeline, enable=True)


def start_recording(pipeline, record_folder):
    record_path = storage.create_recording_folder(record_folder)
    
    filesink_record = pipeline.get_by_name("filesink_record")
    filesink_record.set_property("location", f"{record_path}/frame_%04d.jpg")
    filesink_record.set_state(Gst.State.NULL)
    filesink_record.set_state(Gst.State.PLAYING)
    
    update_valve(pipeline, enable=False)

def stop_recording(pipeline):
    filesink_record = pipeline.get_by_name("filesink_record")
    filesink_record.set_state(Gst.State.PAUSED)

    update_valve(pipeline, enable=True)
    