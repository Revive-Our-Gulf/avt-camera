import time
from gstreamer import Gst
from utils import storage
import shutil


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
    filesink_record.set_property("location", f"{record_path}/IMG_%04d.jpg")
    filesink_record.set_state(Gst.State.NULL)
    filesink_record.set_state(Gst.State.PLAYING)
    
    update_valve(pipeline, enable=False)

    parameters_file = '/home/pi/Repos/avt/app/settings/current.xml'
    parameters_destination = record_path + '/current.xml'
    print(parameters_file)
    print(parameters_destination)
    shutil.copy(parameters_file, parameters_destination)

    return record_path

def stop_recording(pipeline):
    filesink_record = pipeline.get_by_name("filesink_record")
    filesink_record.set_state(Gst.State.PAUSED)

    update_valve(pipeline, enable=True)
    