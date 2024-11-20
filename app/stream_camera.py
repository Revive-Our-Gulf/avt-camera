import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib
import threading
import subprocess
import time
import logging
import signal
import sys
import tracemalloc

Gst.init(None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pipeline = None

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

def run_pipeline(pipeline_str):
    global pipeline
    logging.info("Creating the pipeline from the string")

    pipeline = Gst.parse_launch(pipeline_str)
    pipeline.set_state(Gst.State.PLAYING)

    logging.info("Pipeline is running")
    return pipeline

def stop_pipeline(pipeline):
    logging.info("Stopping the pipeline")
    pipeline.send_event(Gst.Event.new_eos())
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS)
    pipeline.set_state(Gst.State.NULL)
    logging.info("Pipeline stopped")

def signal_handler(sig, frame):
    logging.info("Signal received, stopping the pipeline")
    if pipeline:
        stop_pipeline(pipeline)
    sys.exit(0)

if __name__ == "__main__":
    tracemalloc.start()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    modify_mtu()

    pipeline_str = (
        "aravissrc ! video/x-raw,format=RGB ! videoconvert ! queue max-size-buffers=1 ! interpipesink name=src "
        "interpipesrc name=interpipesrc listen-to=src ! queue max-size-buffers=1 ! videoconvert ! fakesink"
    )

    pipeline = run_pipeline(pipeline_str)

    bus = pipeline.get_bus()
    start_time = time.time()

    while True:
        # Check for messages on the bus
        msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
        if msg:
            if msg.type == Gst.MessageType.ERROR:
                err, debug = msg.parse_error()
                logging.error(f"Error received: {err}, {debug}")
                break
            elif msg.type == Gst.MessageType.EOS:
                logging.info("End-Of-Stream reached")
                break

        # Monitor memory usage
        with open('/proc/self/status') as f:
            for line in f:
                if 'VmRSS' in line:
                    logging.info(f"Memory usage: {line.strip()}")
                    break

        time.sleep(1)

    # Free resources
    stop_pipeline(pipeline)

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    logging.info("[ Top 10 memory usage ]")
    for stat in top_stats[:10]:
        logging.info(stat)