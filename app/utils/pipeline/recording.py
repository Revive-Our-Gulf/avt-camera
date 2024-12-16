import time
from gstreamer import Gst
from utils import storage
import shutil
from .valve import update_valve
from . import appsink

def save_parameters(record_path):
    parameters_file = '/home/pi/Repos/avt/app/settings/current.xml'
    parameters_destination = record_path + '/current.xml'
    print(parameters_file)
    print(parameters_destination)
    shutil.copy(parameters_file, parameters_destination)


def start(pipeline, record_folder):
    record_path = storage.create_recording_folder(record_folder)
    save_parameters(record_path)
    appsink.start(record_path)

    return record_path

def stop(pipeline):
    appsink.stop()