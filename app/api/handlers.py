from app.utils import json, xml
from app.core import pipeline
from flask_socketio import emit
from app.config.settings import CURRENT_XML, PARAMETERS_JSON

def handle_toggle_recording(data):
    is_recording = data['isRecording']
    record_folder = data['folderName']
    return is_recording, record_folder

def handle_update_parameters(data, pipeline_obj, is_preview_active, is_recording):
    # Use the path from settings instead of hardcoded path
    root = xml.read(CURRENT_XML)
    
    print(f" data is {data}")

    xml.update_from_json(root, data)
    xml.write(root, CURRENT_XML)

    emit('parameters_updated', data)

    if is_preview_active and not is_recording:
        print("Restarting pipeline")
        pipeline.config.restart(pipeline_obj)

def handle_reset_parameters(pipeline_obj):
    # Use the path from settings
    # Note: You need to define a DEFAULT_XML path in settings or use a different approach
    default_xml = CURRENT_XML.replace('current.xml', 'default.xml')
    root = xml.read(default_xml)
    xml.write(root, CURRENT_XML)
    
    emit('parameters_reset', {'message': 'Parameters have been reset to default settings.'})
    pipeline.config.restart(pipeline_obj)