import os
from datetime import datetime
import cv2
import threading

class StorageManager:
    def __init__(self, base_dir="recordings"):
        self.base_dir = base_dir
        self.current_folder = None
        self.folder_lock = threading.Lock()
        os.makedirs(base_dir, exist_ok=True)
        
    def create_new_folder(self, folder_name=None):
        with self.folder_lock:
            if not folder_name:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                folder_name = timestamp
                
            full_path = os.path.join(self.base_dir, folder_name)
            os.makedirs(full_path, exist_ok=True)
            self.current_folder = full_path
            return full_path
            
    def get_current_folder(self):
        with self.folder_lock:
            return self.current_folder
            
    def save_frame(self, frame, timestamp):
        folder = self.get_current_folder()
        if not folder:
            folder = self.create_new_folder()
            
        filename = os.path.join(folder, f"frame_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        return filename
