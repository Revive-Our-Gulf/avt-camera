from gstreamer import Gst
from utils import xml_utils
import json
from flask_socketio import emit

def handle_toggle_recording(data, pipeline):
    is_recording = data['isRecording']
    record_folder = data['folderName']
    print(f"Recording state: {is_recording}, Folder: {record_folder}")

    # Emit the current recording state and folder name to the client
    emit('recording_state_updated', {'isRecording': is_recording, 'folderName': record_folder}, broadcast=True)

    return is_recording, record_folder

def handle_update_parameters(data, pipeline):

    # Load the parameters from the JSON file
    with open('settings/parameters.json') as f:
        parameters = json.load(f)

    # Update the parameters in the JSON
    for key, value in data.items():
        if key in parameters:
            parameters[key]['value'] = value
            print(f"JSON Update: Set {key} to {value}")

    # Save the updated parameters to the JSON file
    with open('settings/parameters.json', 'w') as f:
        json.dump(parameters, f, indent=4)

    # Update the XML file with the new parameters
    root = xml_utils.read_xml('settings/current.xml')

    # Update Features
    for feature in root.findall(".//Feature"):
        if feature.get('Name') in data:
            feature.text = data[feature.get('Name')]
            print(f"Set {feature.get('Name')} to {data[feature.get('Name')]}")

    # Update Selectors
    for selector in root.findall(".//Selector"):
        selector_name = selector.get('Name')
        for combination in selector.findall(".//SelectorCombination"):
            feature_name = combination.get('Feature')
            entry_name = combination.get('Entry')
            param_key = f"{feature_name}{entry_name}"
            if param_key in data:
                combination.text = data[param_key]
                print(f"Set {feature_name} in {selector_name} with entry {entry_name} to {data[param_key]}")
            elif feature_name in data and 'entry' not in parameters[feature_name]:
                combination.text = data[feature_name]
                print(f"Set {feature_name} in {selector_name} with entry {entry_name} to {data[feature_name]}")

    xml_utils.write_xml(root, 'settings/current.xml')

    # Restart the camera with the new settings file
    camera_src = pipeline.get_by_name("vimbasrc")
    camera_src.set_property("settingsfile", 'settings/current.xml')
    camera_src.set_state(Gst.State.NULL)
    camera_src.set_state(Gst.State.PLAYING)

    # Emit the updated parameters back to the client
    emit('parameters_updated', parameters)






def handle_restore_default_parameters(data, pipeline):
    print(f"Updating parameters: {data}")

    root = xml_utils.read_xml('settings/default.xml')

    # Load the parameters from the JSON file
    with open('settings/parameters.json') as f:
        parameters = json.load(f)

    for feature in root.findall(".//Feature"):
        if feature.get('Name') in data:
            data[feature.get('Name')] = feature.text

    # Update Selectors
    for selector in root.findall(".//Selector"):
        selector_name = selector.get('Name')
        for combination in selector.findall(".//SelectorCombination"):
            feature_name = combination.get('Feature')
            entry_name = combination.get('Entry')
            param_key = f"{feature_name}{entry_name}"
            if param_key in data:
               data[param_key] = combination.text

    
    # Update the parameters in the JSON
    for key, value in data.items():
        if key in parameters:
            parameters[key]['value'] = value
            print(f"Set {key} to {value}")

    # Save the updated parameters to the JSON file
    with open('settings/parameters.json', 'w') as f:
        json.dump(parameters, f, indent=4)
    

    xml_utils.write_xml(root, 'settings/current.xml')

    # Restart the camera with the new settings file
    camera_src = pipeline.get_by_name("vimbasrc")
    camera_src.set_property("settingsfile", 'settings/current.xml')
    camera_src.set_state(Gst.State.NULL)
    camera_src.set_state(Gst.State.PLAYING)

    # Emit the updated parameters back to the client
    emit('parameters_updated', parameters)
