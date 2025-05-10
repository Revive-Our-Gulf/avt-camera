import threading
import time
from pymavlink import mavutil
from datetime import datetime
import math
import os
import subprocess

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

        self.last_time_sync = 0
        self.time_sync_interval = 30 
    
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

                    if msg_type == "SYSTEM_TIME":
                        self.check_and_sync_system_time()

                    if msg_type == "GLOBAL_POSITION_INT":
                        self._process_position_update(self.telemetry_data[msg_type])

                    # if msg_type == "GPS_RAW_INT":
                    #     gps_raw_time = self.telemetry_data[msg_type]["time_usec"]
                    #     gps_time = datetime.fromtimestamp(gps_raw_time / 1e6).strftime('%Y-%m-%d %H:%M:%S')

                    #     system_time = self.telemetry_data["SYSTEM_TIME"]["time_unix_usec"]
                    #     system_time_str = datetime.fromtimestamp(system_time / 1e6).strftime('%Y-%m-%d %H:%M:%S')

                    #     time_diff = (gps_raw_time - system_time) / 1e6
                    #     print(f"GPS Time: {gps_time}, System Time: {system_time_str}, Time Difference: {time_diff:.2f} seconds")
                    
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

    def check_and_sync_system_time(self):
        current_time = time.time()
        if current_time - self.last_time_sync >= self.time_sync_interval:
            self.sync_system_time()
            self.last_time_sync = current_time

    def sync_system_time(self):
        """Sync system time with MAVLink SYSTEM_TIME message"""
        try:
            if "SYSTEM_TIME" in self.telemetry_data:
                unix_time_us = self.telemetry_data["SYSTEM_TIME"]["time_unix_usec"]
                unix_time_sec = unix_time_us / 1000000
                time_str = datetime.fromtimestamp(unix_time_sec).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"Syncing system time to: {time_str}")
                
                # Run the date command to set the system time locally
                result = subprocess.run(['/usr/bin/sudo', 'date', '-s', time_str], check=False)
                
                if result.returncode == 0:
                    print("System time synchronized successfully")
                else:
                    print(f"Failed to set system time, error code: {result.returncode}")
                    
                    # Attempt to get the time from remote Pi (192.168.2.2) via SSH
                    print("Attempting to get time from remote Pi (192.168.2.2) via SSH...")
                    try:
                        ssh_cmd = ["/usr/bin/ssh", "pi@192.168.2.2", "date +'%Y-%m-%d %H:%M:%S'"]
                        remote_time_output = subprocess.check_output(ssh_cmd, text=True).strip()
                        
                        if remote_time_output:
                            print(f"Remote Pi time retrieved: {remote_time_output}")
                            # Now, set the time on the local Pi (192.168.2.3) using the retrieved time
                            set_time_cmd = ['/usr/bin/sudo', 'date', '-s', remote_time_output]
                            set_result = subprocess.run(set_time_cmd, check=False)
                            
                            if set_result.returncode == 0:
                                print(f"Local Pi time synchronized to remote Pi's time: {remote_time_output}")
                            else:
                                print(f"Failed to set local Pi time with remote Pi's time. Error: {set_result.returncode}")
                        else:
                            print("Failed to retrieve time from remote Pi.")
                    
                    except subprocess.CalledProcessError as ssh_error:
                        print(f"SSH command failed: {ssh_error}")
                    except Exception as e:
                        print(f"Error syncing with remote Pi: {e}")
                    
                    # Calculate and print the time difference if the sync fails
                    time_diff = unix_time_sec - time.time()
                    print(f"Time difference: {time_diff:.2f} seconds")
                    
        except Exception as e:
            print(f"Error syncing system time: {e}")

    def get_remote_pi_time_diff(self, remote_pi="pi@192.168.2.2"):
        """Get time difference between local Pi and remote Pi"""
        try:
            # Make sure to specify full path to `ssh` command
            ssh_cmd = ["/usr/bin/ssh", remote_pi, "date +%s.%N"]
            remote_time_output = subprocess.check_output(ssh_cmd, text=True).strip()

            remote_time_sec = float(remote_time_output)
            local_time = time.time()

            time_diff = remote_time_sec - local_time
            
            remote_time_str = datetime.fromtimestamp(remote_time_sec).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            local_time_str = datetime.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            return {
                "success": True,
                "time_diff_seconds": time_diff,
                "remote_pi": remote_pi,
                "remote_time": remote_time_str,
                "local_time": local_time_str
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"SSH connection failed: {str(e)}",
                "remote_pi": remote_pi
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "remote_pi": remote_pi
            }
