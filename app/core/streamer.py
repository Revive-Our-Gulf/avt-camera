import base64
import time
import threading

class ImageStreamer:
    def __init__(self, socketio, camera_controller, image_path):
        self.socketio = socketio
        self.camera_controller = camera_controller
        self.image_path = image_path
        self.running = False
        self.thread = None
        self.last_image_data = None
    
    def start(self):
        """Start the image streaming thread"""
        self.running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the image streaming thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _stream_loop(self):
        """Main streaming loop"""
        while self.running:
            try:
                # Only try to read the image if preview is active
                if self.camera_controller.is_preview_active:
                    with open(self.image_path, 'rb') as image_file:
                        image_data = image_file.read()
                        if image_data != self.last_image_data:
                            encoded_image = base64.b64encode(image_data).decode('utf-8')
                            self.socketio.emit('image_update', {'image': encoded_image})
                            self.last_image_data = image_data
            except Exception:
                # If there's an error reading the file, just continue
                pass
                
            time.sleep(0.1)