#!/usr/bin/env python3
# Simple PyMAVLink connection test script

import sys
import time
from pymavlink import mavutil

def test_mavlink_connection(connection_string):
    print(f"Attempting to connect using: {connection_string}")
    
    try:
        # Connect to the MAVLink source
        connection = mavutil.mavlink_connection(connection_string)
        
        # Wait for a heartbeat message to confirm the connection
        print("Waiting for heartbeat...")
        connection.wait_heartbeat(timeout=10)
        print(f"Heartbeat received from system {connection.target_system} component {connection.target_component}")
        
        # Listen for messages for 30 seconds
        print("Listening for MAVLink messages for 30 seconds...")
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < 30:
            msg = connection.recv_match(blocking=True, timeout=1.0)
            if msg:
                message_count += 1
                # Print the message type and a subset of fields
                print(f"Message #{message_count}: {msg.get_type()}")
                
                # For certain message types, print more details
                if msg.get_type() == 'HEARTBEAT':
                    print(f"  System: {msg.get_srcSystem()}, Component: {msg.get_srcComponent()}")
                elif msg.get_type() == 'ATTITUDE':
                    print(f"  Roll: {msg.roll:.2f}, Pitch: {msg.pitch:.2f}, Yaw: {msg.yaw:.2f}")
                elif msg.get_type() == 'GLOBAL_POSITION_INT':
                    print(f"  Lat: {msg.lat/1e7:.6f}, Lon: {msg.lon/1e7:.6f}, Alt: {msg.alt/1000:.1f}m")
        
        print(f"Test complete. Received {message_count} messages.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    # Try different connection strings based on your setup
    
    # Option 1: Listen on all interfaces for UDP broadcasts
    connection_string = 'udpin:0.0.0.0:14570'
    
    # Option 2: Alternative ports that BlueOS might be using
    # connection_string = 'udpin:0.0.0.0:14570'
    
    # Option 3: TCP connection to BlueOS
    # connection_string = 'tcp:192.168.2.2:5760'
    
    # Option 4: Direct UDP connection to BlueOS
    # connection_string = 'udpout:192.168.2.2:14550'
    
    # If a command line argument is provided, use that as the connection string
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    
    test_mavlink_connection(connection_string)