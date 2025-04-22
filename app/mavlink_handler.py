import threading
import time
from pymavlink import mavutil
from datetime import datetime
import math

class MavlinkHandler:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.connection = None
        self.running = False
        self.telemetry_data = {}

        self.last_photo_position = None
        self.distance_threshold = 1.0
        self.should_trigger_photo = False
        self.distance_since_last_photo = 0.0

    
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
                    msg_type = msg.get_type()
                    self.telemetry_data[msg_type] = msg.to_dict()

                if msg_type == "GLOBAL_POSITION_INT":
                    self._process_position_update(self.telemetry_data[msg_type])
                    
        except Exception as e:
            print(f"MAVLink thread error: {e}")
        finally:
            if self.connection:
                self.connection.close()
            
    def get_telemetry(self):
        return self.telemetry_data
    
    def set_distance_threshold(self, meters):
        self.distance_threshold = float(meters)
        print(f"Distance threshold set to {self.distance_threshold} meters")

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def should_trigger_photo_by_distance(self):
        if self.should_trigger_photo:
            self.should_trigger_photo = False
            return True
        return False
    
    def reset_distance_tracking(self):
        if "GLOBAL_POSITION_INT" in self.telemetry_data:
            pos = self.telemetry_data["GLOBAL_POSITION_INT"]
            self.last_photo_position = (pos['lat'] / 1e7, pos['lon'] / 1e7) 
            self.distance_since_last_photo = 0.0
            print(f"Distance tracking reset at position: {self.last_photo_position}")

    def _process_position_update(self, position_data):
        current_lat = position_data['lat'] / 1e7
        current_lon = position_data['lon'] / 1e7
        
        if self.last_photo_position is None:
            self.last_photo_position = (current_lat, current_lon)
            return
        
        distance = self.calculate_distance(
            self.last_photo_position[0], self.last_photo_position[1],
            current_lat, current_lon
        )
        
        self.distance_since_last_photo += distance
        self.last_photo_position = (current_lat, current_lon)
        
        if self.distance_since_last_photo >= self.distance_threshold:
            self.should_trigger_photo = True
            print(f"Distance threshold ({self.distance_threshold}m) reached: {self.distance_since_last_photo:.2f}m traveled")
            self.distance_since_last_photo = 0.0
