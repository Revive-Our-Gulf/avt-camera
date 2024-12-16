import utils 
from flask_socketio import emit
import time


def handle_toggle_recording(data, pipeline):
    is_recording = data['isRecording']
    record_folder = data['folderName']
    return is_recording, record_folder








def handle_update_parameters(data, pipeline):

    root = utils.xml.read('/home/pi/Repos/avt/app/settings/current.xml')

    print(f" data is {data}")

    utils.xml.update_from_json(root, data)
    utils.xml.write(root, '/home/pi/Repos/avt/app/settings/current.xml')

    emit('parameters_updated', data)

    utils.pipeline.config.restart(pipeline)

    for param_name, param_value in data.items():
        if param_name == "StreamResolution":
            print("Updating stream resolution")
            pipeline = pipeline.update_stream_resolution(pipeline, param_value)

def handle_reset_parameters(pipeline):
    root = utils.xml.read('/home/pi/Repos/avt/app/settings/current.xml')
    utils.xml.write(root, '/home/pi/Repos/avt/app/settings/current.xml')

    
    # Emit a reset event to the client
    emit('parameters_reset', {'message': 'Parameters have been reset to default settings.'})
    pipeline.restart_pipeline(pipeline)