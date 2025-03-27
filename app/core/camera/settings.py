import os
import logging
import xml.etree.ElementTree as ET

class CameraSettings:
    """
    Manages camera settings including loading/saving profiles
    and handling XML configuration files.
    """
    DEFAULT_SETTINGS_PATH = "/home/pi/Repos/avt-camera/app/config/camera_settings/default.xml"
    CURRENT_SETTINGS_PATH = "/home/pi/Repos/avt-camera/app/config/camera_settings/current.xml"
    
    def __init__(self):
        """Initialize camera settings handler"""
        self.settings = {}
        self.load_settings()
    
    def load_settings(self, path=None):
        """Load camera settings from XML file"""
        if not path:
            path = self.CURRENT_SETTINGS_PATH
            
        if not os.path.exists(path):
            path = self.DEFAULT_SETTINGS_PATH
            
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            # Extract camera settings from XML
            settings = {}
            
            # Parse main features
            for feature in root.findall(".//Feature"):
                name = feature.get('Name')
                value = feature.get('Value') or feature.text
                settings[name] = value
                
            # Parse selector combinations
            for selector in root.findall(".//Selector"):
                selector_name = selector.get('Name')
                for combo in selector.findall(".//SelectorCombination"):
                    entry = combo.get('Entry')
                    feature = combo.get('Feature')
                    value = combo.get('Value') or combo.text
                    key = f"{feature}+{entry}"
                    settings[key] = value
            
            self.settings = settings
            return True
        except Exception as e:
            logging.error(f"Failed to load camera settings: {e}")
            return False
    
    def save_settings(self, path=None):
        """Save current camera settings to XML file"""
        if not path:
            path = self.CURRENT_SETTINGS_PATH
        
        try:
            # Load the original file as template
            tree = ET.parse(self.DEFAULT_SETTINGS_PATH)
            root = tree.getroot()
            
            # Update feature values
            for feature in root.findall(".//Feature"):
                name = feature.get('Name')
                if name in self.settings:
                    if feature.get('Value') is not None:
                        feature.set('Value', str(self.settings[name]))
                    else:
                        feature.text = str(self.settings[name])
            
            # Update selector combinations
            for selector in root.findall(".//Selector"):
                for combo in selector.findall(".//SelectorCombination"):
                    feature = combo.get('Feature')
                    entry = combo.get('Entry')
                    key = f"{feature}+{entry}"
                    if key in self.settings:
                        if combo.get('Value') is not None:
                            combo.set('Value', str(self.settings[key]))
                        else:
                            combo.text = str(self.settings[key])
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tree.write(path)
            return True
        except Exception as e:
            logging.error(f"Failed to save camera settings: {e}")
            return False
    
    def get_setting(self, name):
        """Get a specific camera setting"""
        return self.settings.get(name)
    
    def set_setting(self, name, value):
        """Set a specific camera setting"""
        self.settings[name] = value
        return True
    
    def reset_to_default(self):
        """Reset settings to default values"""
        return self.load_settings(self.DEFAULT_SETTINGS_PATH)