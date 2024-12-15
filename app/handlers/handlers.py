from utils import xml 
from utils import pipeline as pipeline_utils
from flask_socketio import emit

def handle_toggle_recording(data, pipeline):
    is_recording = data['isRecording']
    record_folder = data['folderName']
    print(f"Recording state: {is_recording}, Folder: {record_folder}")

    # Emit the current recording state and folder name to the client
    emit('recording_state_updated', {'isRecording': is_recording, 'folderName': record_folder}, broadcast=True)

    return is_recording, record_folder

def handle_update_parameters(data, pipeline):

    root = xml.read('/home/pi/Repos/avt/app/settings/current.xml')

    print(f" data is {data}")

    xml.update_from_json(root, data)
    xml.write(root, '/home/pi/Repos/avt/app/settings/current.xml')

    
    
    # Emit the updated parameters back to the client
    emit('parameters_updated', data)



    pipeline_utils.restart_pipeline(pipeline)

    for param_name, param_value in data.items():
        if param_name == "StreamResolution":
            print("Updating stream resolution")
            pipeline = pipeline.update_stream_resolution(pipeline, param_value)

def handle_reset_parameters(pipeline):
    root = xml.read('/home/pi/Repos/avt/app/settings/current.xml')
    xml.write(root, '/home/pi/Repos/avt/app/settings/current.xml')

    
    # Emit a reset event to the client
    emit('parameters_reset', {'message': 'Parameters have been reset to default settings.'})
    pipeline.restart_pipeline(pipeline)