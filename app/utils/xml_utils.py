import xml.etree.ElementTree as ET
import re
from pathlib import Path

def read(path):
    file = Path(path)
    data = file.read_bytes()
    
    # Remove XML declaration if present
    data = re.sub(b'<\?xml.*?\?>', b'', data)
    
    # Add a single root tag
    data = b'<root>' + data + b'</root>'
    root = ET.fromstring(data)

    return root

def write(root, path):
    updated_data = ET.tostring(root, encoding='utf-8', method='xml')
    try:
        updated_data = re.sub(b'<root>', b'', updated_data)
        updated_data = re.sub(b'</root>', b'', updated_data)
    except re.error as e:
        print(f"Regex error: {e}")
    with open(path, 'wb') as updated_file:
        updated_file.write(updated_data)

def get_feature_value(root, feature_name):
    feature = root.find(f".//Feature[@Name='{feature_name}']")
    if feature is not None:
        return feature.text

    feature = root.find(f".//SelectorCombination[@Feature='{feature_name}']")
    if feature is not None:
        return feature.text
    
    return None

def get_values_from_xml(xml_path, parameters):
    root = read(xml_path)
    values = {}

    for param_name, param_info in parameters.items():
        if 'entry' not in param_info:
            values[param_name] = get_feature_value(root, param_name)
        else:
            feature_name = param_info['feature']
            entry_name = param_info['entry']
            feature = root.find(f".//SelectorCombination[@Feature='{feature_name}'][@Entry='{entry_name}']")
            if feature is not None:
                values[param_name] = feature.text

    return values


def update_feature(root, feature_name, value):
    for feature in root.findall(f".//Feature[@Name='{feature_name}']"):
        feature.text = str(value)
        print(f"Set {feature_name} to {value}")
    for feature in root.findall(f".//SelectorCombination[@Feature='{feature_name}']"):
        feature.text = str(value)
        print(f"Set {feature_name} to {value}")

def update_selector(root, feature_name, entry_name, value):
    for combination in root.findall(f".//SelectorCombination[@Feature='{feature_name}'][@Entry='{entry_name}']"):
        combination.text = str(value)
        print(f"Set {feature_name} with entry {entry_name} to {value}")


def update_from_json(root, data):
    print(data)
    for key, value in data.items():
        if '+' in key:
            print("Found +")
            # Handle parameters with entries
            feature_name, entry_name = key.split('+')
            print(f"Feature: {feature_name}, Entry: {entry_name}")
            update_selector(root, feature_name, entry_name, value)
        else:
            # Handle regular parameters
            update_feature(root, key, value)