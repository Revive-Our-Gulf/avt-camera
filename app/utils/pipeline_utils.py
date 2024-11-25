import time
from gstreamer import Gst
from utils import record_utils



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

    record_valve = pipeline.get_by_name("record_valve")
    record_valve.set_property("drop", True)


def start_recording(pipeline, record_folder):
    filesink_record = pipeline.get_by_name("filesink_record")
    record_valve = pipeline.get_by_name("record_valve")
    
    record_path = record_utils.create_recording_folder(record_folder)
    filesink_record = pipeline.get_by_name("filesink_record")
    filesink_record.set_property("location", f"{record_path}/frame_%04d.jpg")
    filesink_record.set_state(Gst.State.PLAYING)
    record_valve.set_property("drop", False)

def stop_recording(pipeline):
    filesink_record = pipeline.get_by_name("filesink_record")
    record_valve = pipeline.get_by_name("record_valve")

    record_valve.set_property("drop", True)
    filesink_record.set_state(Gst.State.PAUSED)

def update_stream_resolution(pipeline, resolution):
    print(f"Updating stream resolution to {resolution}")
    width, height = map(int, resolution.split('x'))
    caps = Gst.Caps.from_string(f"video/x-raw,width={width},height={height}")
    capsfilter = pipeline.get_by_name("capsfilter_stream")
    capsfilter.set_property("caps", caps)
    print(f"Stream resolution updated to {width}x{height}")
    print(pipeline.get_by_name("capsfilter_stream").get_property("caps").to_string())
    return pipeline
