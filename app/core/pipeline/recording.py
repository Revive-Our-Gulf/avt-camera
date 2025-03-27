import time
from gstreamer import Gst
from app.core import storage
import shutil
from . import appsink
from app.config.settings import CURRENT_XML

def save_parameters(record_path):
    parameters_destination = record_path + '/current.xml'
    print(CURRENT_XML)
    print(parameters_destination)
    shutil.copy(CURRENT_XML, parameters_destination)


def start(pipeline, record_folder):
    record_path = storage.create_recording_folder(record_folder)
    save_parameters(record_path)
    appsink.start(record_path)

    return record_path

def stop(pipeline):
    appsink.stop()