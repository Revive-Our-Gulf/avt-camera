import subprocess
import time
import logging
from gstreamer import Gst

def is_camera_available(camera_name):
    try:
        result = subprocess.run(['arv-tool-0.10'], capture_output=True, text=True, check=True)
        if camera_name in result.stdout:
            print(camera_name)
            return True
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while checking camera status: {e}")
        return False

def wait_for_camera(camera_name, check_interval=5):
    logging.info(f"Waiting for camera {camera_name} to become available...")
    while not is_camera_available(camera_name):
        logging.info(f"Camera {camera_name} is not available. Retrying in {check_interval} seconds...")
        time.sleep(check_interval)
    logging.info(f"Camera {camera_name} is now available.")


