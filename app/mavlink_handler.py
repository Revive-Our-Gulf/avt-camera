import threading
import time
from pymavlink import mavutil
from datetime import datetime

class MavlinkHandler:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.connection = None
        self.running = False
        self.telemetry_data = {}
        
    def start_mavlink_thread(self):
        thread = threading.Thread(target=self._mavlink_thread, daemon=True)
        thread.start()
        return thread
        
    def _mavlink_thread(self):
        self.running = True
        try:
            print("Starting MAVLink connection...")
            self.connection = mavutil.mavlink_connection(f'udpin:0.0.0.0:14570')
            self.connection.wait_heartbeat()
            print("MAVLink connection established")
            
            while self.running:
                msg = self.connection.recv_match(blocking=True, timeout=1.0)
                if msg:
                    self.telemetry_data[msg.get_type()] = msg.to_dict()
                    
                    if self.socketio:
                        self.socketio.emit('mavlink_data', self.telemetry_data)
                        
        except Exception as e:
            print(f"MAVLink thread error: {e}")
        finally:
            if self.connection:
                self.connection.close()
            
    def get_telemetry(self):
        return self.telemetry_data