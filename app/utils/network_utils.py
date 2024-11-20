# network_utils.py

import subprocess
import logging
import time

def modify_mtu():
    try:
        # Check if MTU is already set to 9000
        result = subprocess.run(['ip', 'link', 'show', 'eth0'], capture_output=True, text=True, check=True)
        if 'mtu 9000' in result.stdout:
            logging.info("MTU is already set to 9000 for eth0")
            return
        
        logging.info("Bringing down the network interface eth0")
        subprocess.run(['sudo', 'ip', 'link', 'set', 'eth0', 'down'], check=True)
        
        logging.info("Setting MTU to 9000 for eth0")
        subprocess.run(['sudo', 'ip', 'link', 'set', 'eth0', 'mtu', '9000'], check=True)
        
        logging.info("Bringing up the network interface eth0")
        subprocess.run(['sudo', 'ip', 'link', 'set', 'eth0', 'up'], check=True)
        
        logging.info("Waiting for the network interface to stabilize")
        time.sleep(10)
        
        logging.info("MTU modification completed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running sudo commands: {e}")
        exit(1)