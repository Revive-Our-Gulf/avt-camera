import os
import json
from pathlib import Path

class SettingsManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_dir = os.path.join(base_dir, 'settings')
        self.parameters_path = os.path.join(self.settings_dir, 'parameters.json')

    def get_parameters_definitions(self):
        try:
            with open(self.parameters_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading camera parameters: {e}")
            return {"parameters": []}

    def get_parameter_by_id(self, param_id):
        params = self.get_parameters_definitions()
        for param in params.get("parameters", []):
            if param["id"] == param_id:
                return param
        return None
    
    def get_adjusted_settings(self, settings):
        filtered_settings = {}

        for param_id, value in settings.items():
            print(f"Processing setting: {param_id}={value}")
            param_def = self.get_parameter_by_id(param_id)
            if param_def and not param_def.get("writeable", False):
                continue
            
            if param_def.get("value") != value:
                filtered_settings[param_id] = value

        return filtered_settings


    def save_current_settings(self, settings):
        filtered_settings = self.get_adjusted_settings(settings)
        print(f"Filtered settings to save: {filtered_settings}")

        try:
            existing_data = self.get_parameters_definitions()
            
            if "parameters" in existing_data:
                params_list = existing_data["parameters"]
                for param in params_list:
                    if param["id"] in filtered_settings:
                        param["value"] = filtered_settings[param["id"]]
            
            with open(self.parameters_path, 'w') as f:
                json.dump(existing_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving parameters: {e}")
            return False
        
    def get_exif_settings(self):
        exif_path = os.path.join(self.settings_dir, 'exif_data.json')
        try:
            with open(exif_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading EXIF settings: {e}")
            return {
                "camera": {}, 
                "lens": {}, 
                "exposure": {}, 
                "other": {}
            }

    def get_app_settings_definitions(self):
        app_settings_path = os.path.join(self.settings_dir, 'app_settings.json')
        try:
            with open(app_settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading app settings: {e}")
            return {"settings": []}

    def get_app_settings(self):
        """Get all app settings as a dictionary of id:value pairs"""
        settings_dict = {}
        settings_data = self.get_app_settings_definitions()
        
        for setting in settings_data.get("settings", []):
            settings_dict[setting["id"]] = setting["value"]
        
        return settings_dict

    def update_app_settings(self, new_settings):
        """Update app settings with provided values"""
        try:
            app_settings_data = self.get_app_settings_definitions()
            
            for setting in app_settings_data.get("settings", []):
                if setting["id"] in new_settings:
                    # Type conversion to ensure data consistency
                    if setting["type"] == "number":
                        setting["value"] = float(new_settings[setting["id"]])
                    elif setting["type"] == "boolean":
                        setting["value"] = bool(new_settings[setting["id"]])
                    else:
                        setting["value"] = new_settings[setting["id"]]
            
            # Write updated settings back to file
            app_settings_path = os.path.join(self.settings_dir, 'app_settings.json')
            with open(app_settings_path, 'w') as f:
                json.dump(app_settings_data, f, indent=4)
            
            return True, "Settings updated successfully"
        except Exception as e:
            print(f"Error updating app settings: {e}")
            return False, str(e)