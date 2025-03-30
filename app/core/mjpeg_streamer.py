import threading
import time
import logging
import uuid
from queue import Queue, Full, Empty

class MJPEGStreamer:
    def __init__(self, camera_controller, max_queue_size=10):
        self.camera_controller = camera_controller
        self.frame_queue = Queue(maxsize=max_queue_size)
        self.clients = set()
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.last_frame_time = 0
        
    def start(self):
        """Start the image streaming thread"""
        if self.thread is not None and self.thread.is_alive():
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._frame_producer)
        self.thread.daemon = True
        self.thread.start()
        logging.info("MJPEG Streamer started")
    
    def stop(self):
        """Stop the image streaming thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logging.info("MJPEG Streamer stopped")
    
    def _frame_producer(self):
        """Producer thread that puts frames from appsink into the queue"""
        while self.running:
            try:
                # Only try to queue frames if preview is active and we have clients
                if self.camera_controller and self.camera_controller.is_preview_active and len(self.clients) > 0:
                    # Don't process frames too quickly
                    current_time = time.time()
                    if current_time - self.last_frame_time < 0.05:  # max 20fps
                        time.sleep(0.01)
                        continue
                    
                    if self.frame_queue.full():
                        # Remove old frame if queue is full
                        try:
                            self.frame_queue.get_nowait()
                        except Empty:
                            pass
                    
                    # Get frame directly from camera controller
                    frame = self.camera_controller.get_latest_frame()
                    if frame is not None:
                        try:
                            self.frame_queue.put(frame, block=False)
                            self.last_frame_time = current_time
                        except Full:
                            pass
                
            except Exception as e:
                logging.error(f"Error in frame producer: {e}")
            
            time.sleep(0.001)  # Sleep to prevent CPU overuse
    
    def add_client(self, client_id):
        with self.lock:
            self.clients.add(client_id)
            logging.info(f"MJPEG client {client_id} connected ({len(self.clients)} total)")
    
    def remove_client(self, client_id):
        with self.lock:
            try:
                self.clients.remove(client_id)
                logging.info(f"MJPEG client {client_id} disconnected ({len(self.clients)} total)")
            except KeyError:
                pass
    
    def get_frame(self):
        """Get a frame from the queue"""
        try:
            return self.frame_queue.get(timeout=1.0)
        except Empty:
            return None

def mjpeg_generator(streamer, client_id):
    """Generator for MJPEG streaming"""
    if streamer is None:
        # Return empty frames if streamer doesn't exist
        while True:
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n\r\n')
            time.sleep(0.5)
    
    try:
        streamer.add_client(client_id)
        last_frame = None
        
        while True:
            # If camera is not in preview mode, return an empty frame but keep connection alive
            if not streamer.camera_controller.is_preview_active:
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n\r\n')
                time.sleep(0.5)
                continue
                
            frame = streamer.get_frame()
            if frame:
                last_frame = frame
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            elif last_frame:
                # Use the last successful frame as a fallback
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + last_frame + b'\r\n')
            else:
                # If no frame is available, send an empty frame to keep connection alive
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n\r\n')
                time.sleep(0.1)
    
    finally:
        if streamer:
            streamer.remove_client(client_id)