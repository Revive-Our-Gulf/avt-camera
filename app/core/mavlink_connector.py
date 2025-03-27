import logging
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging to silence the urllib3 debug messages
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

# Create a session that can be reused
mavlink_session = None

def initialise_mavlink_session():
    """Initialize and return a persistent HTTP session with retry capability"""
    global mavlink_session
    if mavlink_session is None:
        mavlink_session = requests.Session()
        # Configure the session with retries
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        mavlink_session.mount('http://', adapter)
        mavlink_session.mount('https://', adapter)
    return mavlink_session

def get_mavlink_timestamp():
    try:
        session = initialise_mavlink_session()
        response = session.get(
            "http://192.168.2.2/mavlink2rest/v1/mavlink/vehicles/1/components/1/messages/GLOBAL_POSITION_INT", 
            timeout=2
        )
        if response.status_code == 200:
            data = response.json()
            blueos_time = data["status"]["time"]["last_update"]
            # Convert ISO format timestamp to datetime object
            timestamp = datetime.fromisoformat(blueos_time.replace('Z', '+00:00'))
            return timestamp
        else:
            logging.warning(f"Failed to get BlueOS timestamp, status code: {response.status_code}")
            return None
    except Exception as e:
        logging.warning(f"Error getting BlueOS timestamp: {e}")
        return None
    
