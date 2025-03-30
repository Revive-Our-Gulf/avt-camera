#!/usr/bin/env python3

import sys
import os
import time
import logging
import threading
import uuid
from flask import Flask, Response
import cv2
import numpy as np

# Add project root to path (fix for importing app modules)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from gstreamer import GstContext, GstPipeline, Gst
from app.core.camera.controller import CameraController
from app.core.mjpeg_streamer import MJPEGStreamer, mjpeg_generator
from app.config.settings import DEFAULT_PIPELINE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Initialize GStreamer
GstContext()

# Modify the pipeline to use appsink instead of filesink
DIRECT_PIPELINE = DEFAULT_PIPELINE

class TestCameraController:
    """Camera controller that uses appsink to get frames directly"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.is_preview_active = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.appsink = None
        
    def setup_pipeline(self):
        """Set up the pipeline for testing"""
        # First, start the pipeline so the elements are available
        try:
            # Initialize the pipeline
            self.pipeline.startup()
            self.is_preview_active = True
            logging.info("Pipeline started for setup")
            
            # Now we can safely get the appsink element
            self.appsink = self.pipeline.get_by_name("jpeg_sink")
            if not self.appsink:
                logging.error("Could not find appsink element 'jpeg_sink' in pipeline")
                return False
                
            # Connect to the new-sample signal
            self.appsink.connect("new-sample", self.on_new_sample)
            logging.info("Connected to appsink element")
            return True
        except Exception as e:
            logging.error(f"Failed to setup pipeline: {e}")
            return False
        
    def on_new_sample(self, appsink):
        """Callback for new samples from appsink"""
        sample = appsink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.ERROR
            
        buffer = sample.get_buffer()
        if not buffer:
            return Gst.FlowReturn.ERROR
            
        # Get data from buffer
        success, map_info = buffer.map(Gst.MapFlags.READ)
        if not success:
            buffer.unmap(map_info)
            return Gst.FlowReturn.ERROR
            
        # Copy the buffer data to avoid issues with buffer reuse
        data = bytes(map_info.data)
        buffer.unmap(map_info)
        
        # Store the latest frame with thread safety
        with self.frame_lock:
            self.current_frame = data
            
        return Gst.FlowReturn.OK
        
    def start_preview(self):
        """Start the pipeline directly"""
        try:
            self.pipeline.startup()
            self.is_preview_active = True
            logging.info("Camera preview started successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to start preview: {e}")
            return False
    
    def stop_preview(self):
        """Stop the pipeline directly"""
        try:
            self.pipeline.shutdown()
            self.is_preview_active = False
            logging.info("Camera preview stopped successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to stop preview: {e}")
            return False
    
    def get_latest_frame(self):
        """Get latest JPEG frame directly from memory"""
        with self.frame_lock:
            return self.current_frame

def main():
    # Create Flask app for MJPEG streaming
    app = Flask(__name__)
    
    # Create and initialize pipeline with our modified pipeline that uses appsink
    pipeline = GstPipeline(DIRECT_PIPELINE)
    
    # Create camera controller (using our direct memory version)
    camera_controller = TestCameraController(pipeline)
    
    # Set up the pipeline - this will start it
    if not camera_controller.setup_pipeline():
        logging.error("Failed to set up pipeline, exiting.")
        return
    
    # Create MJPEG streamer
    mjpeg_streamer = MJPEGStreamer(camera_controller, max_queue_size=1)
    mjpeg_streamer.start()
    
    @app.route('/stream')
    def stream():
        """Stream MJPEG to client"""
        client_id = str(uuid.uuid4())
        return Response(
            mjpeg_generator(mjpeg_streamer, client_id),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    
    @app.route('/')
    def index():
        """Serve a simple HTML page with the stream embedded"""
        return """
        <html>
          <head>
            <title>Vimba Camera MJPEG Stream</title>
            <style>
              body { font-family: Arial, sans-serif; text-align: center; }
              img { max-width: 100%; border: 1px solid #ddd; }
              .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>Vimba Camera MJPEG Stream</h1>
              <img src="/stream" alt="Camera Stream">
              <p>Stream is active and running directly from camera memory without saving files.</p>
            </div>
          </body>
        </html>
        """
    
    try:
        # Skip starting the preview again - it's already started in setup_pipeline
        logging.info("Camera preview is already running from setup_pipeline")
        
        # Run Flask app
        logging.info("Starting MJPEG streaming server on http://0.0.0.0:5500/")
        app.run(host='0.0.0.0', port=5500, debug=False, threaded=True)
    
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    
    finally:
        # Clean up
        mjpeg_streamer.stop()
        camera_controller.stop_preview()
        logging.info("Streaming stopped.")

if __name__ == "__main__":
    main()