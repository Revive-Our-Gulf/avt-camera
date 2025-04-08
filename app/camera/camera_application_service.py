from datetime import datetime
from state_machine import CameraState, CameraStateMachine
from settings_manager import SettingsManager
from vmbpy import EnumEntry
import os
import json

class CameraApplicationService:
    def __init__(self, state_machine, camera_hardware_controller, socketio=None):
        self.state_machine = state_machine
        self.socketio = socketio
        self.base_output_dir = "recordings"
        self.current_recording_folder = None
        self.camera_hardware_controller = camera_hardware_controller
        self.settings_manager = SettingsManager()
    
    def change_state(self, new_state, folder_name=None):
        current_state = self.state_machine.get_state()
        if new_state == CameraState.WRITE and current_state != CameraState.WRITE:
            self.set_recording_folder(folder_name)
    
        success = self.state_machine.toggle_state(new_state)
        
        if self.socketio:
            self.socketio.emit('state_change', {'state': self.state_machine.get_state().name})
        
        return success
    
    def set_recording_folder(self, folder_name=None):
        if folder_name is None:
            now = datetime.now()
            folder_name = now.strftime('%Y-%m-%d_%H-%M-%S')
        
        path = os.path.join(self.base_output_dir, folder_name)
        os.makedirs(path, exist_ok=True)
        self.current_recording_folder = path
        return path

    def get_camera_settings(self):
        try:
            current_settings = self.camera_hardware_controller.get_camera_settings()
            
            serializable_settings = {}
            for key, value in current_settings.items():
                if isinstance(value, EnumEntry):
                    serializable_settings[key] = str(value)
                else:
                    serializable_settings[key] = value
            
            return {
                "success": True,
                "settings": serializable_settings
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_camera_settings(self, settings_data):
        try:
            filtered_settings = self.settings_manager.get_adjusted_settings(settings_data)
            self.settings_manager.save_current_settings(settings_data)
            success = self.camera_hardware_controller.apply_specific_settings(filtered_settings)
            
            
            return {
                "success": success,
                "message": "Camera settings updated successfully"
            }
        except Exception as e:
            return {
                "success": success,
                "error": str(e)
            }