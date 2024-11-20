import xml.etree.ElementTree as ET
import re
from pathlib import Path

def read_xml(path):
    file = Path(path)
    data = file.read_bytes()
    
    # Remove XML declaration if present
    data = re.sub(b'<\?xml.*?\?>', b'', data)
    
    # Add a single root tag
    data = b'<root>' + data + b'</root>'
    root = ET.fromstring(data)

    return root

def write_xml(root, path):
    updated_data = ET.tostring(root, encoding='utf-8', method='xml')
    try:
        updated_data = re.sub(b'<root>', b'', updated_data)
        updated_data = re.sub(b'</root>', b'', updated_data)
    except re.error as e:
        print(f"Regex error: {e}")
    with open(path, 'wb') as updated_file:
        updated_file.write(updated_data)