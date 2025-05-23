from enum import Enum, auto
import threading

class TriggerMode(Enum):
    TIME = auto()
    DISTANCE = auto()
    
class CameraState(Enum):
    UNAVAILABLE = auto()
    STANDBY = auto()
    PREVIEW = auto()
    WRITE = auto()
    
class CameraStateMachine:
    def __init__(self):
        self.state = CameraState.UNAVAILABLE
        self.trigger_mode = TriggerMode.TIME
        self.state_lock = threading.Lock()
        print(f"Camera initialised in {self.state.name} state")
    
    def transition_to(self, new_state):
        with self.state_lock:
            if new_state == self.state:
                return False
            
            old_state = self.state
            self.state = new_state
            print(f"Camera state changed: {old_state.name} → {new_state.name}")
            return True
    
    def get_state(self):
        with self.state_lock:
            return self.state
    
    def should_stream(self):
        with self.state_lock:
            return self.state in [CameraState.PREVIEW, CameraState.WRITE]
    
    def should_save(self):
        with self.state_lock:
            return self.state == CameraState.WRITE
    
    def toggle_state(self, new_state):
        current_state = self.get_state()

        if current_state == CameraState.UNAVAILABLE:
            print("Cannot toggle state: Camera is unavailable")
            return False
        
        if current_state == new_state:
            return self.transition_to(CameraState.STANDBY)
        else:
            return self.transition_to(new_state)
        
    def set_camera_available(self, available=True):
        """Mark the camera as available or unavailable"""
        if available and self.get_state() == CameraState.UNAVAILABLE:
            return self.transition_to(CameraState.STANDBY)
        elif not available and self.get_state() != CameraState.UNAVAILABLE:
            return self.transition_to(CameraState.UNAVAILABLE)
        return False
    
    def is_available(self):
        with self.state_lock:
            return self.state != CameraState.UNAVAILABLE

    def set_trigger_mode(self, mode):
        with self.state_lock:
            if mode not in TriggerMode:
                print(f"Invalid trigger mode: {mode}")
                return False
            
            self.trigger_mode = mode
            print(f"Trigger mode set to: {self.trigger_mode.name}")
            return True