import utils 
from flask_socketio import emit
import time


def handle_toggle_recording(data):
    is_recording = data['isRecording']
    record_folder = data['folderName']
    return is_recording, record_folder




def handle_update_parameters(data, pipeline, is_preview_active, is_recording):
    root = utils.xml.read('/home/pi/Repos/avt-camera/app/settings/current.xml')
    
    print(f" data is {data}")

    utils.xml.update_from_json(root, data)
    utils.xml.write(root, '/home/pi/Repos/avt-camera/app/settings/current.xml')

    emit('parameters_updated', data)

    if is_preview_active and not is_recording:
        print("Restarting pipeline")
        utils.pipeline.config.restart(pipeline)

def handle_reset_parameters(pipeline):
    root = utils.xml.read('/home/pi/Repos/avt-camera/app/settings/current.xml')
    utils.xml.write(root, '/home/pi/Repos/avt-camera/app/settings/current.xml')

    
    # Emit a reset event to the client
    emit('parameters_reset', {'message': 'Parameters have been reset to default settings.'})
    pipeline.restart_pipeline(pipeline)