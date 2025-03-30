import time
import logging
from gstreamer import GstPipeline, GstContext
from app.core import pipeline

class CameraController:
    """
    Central controller for camera operations.
    Manages pipeline, preview, recording, and camera settings.
    """
    def __init__(self, pipeline_config):
        """Initialize camera controller with pipeline configuration"""
        self.pipeline = None
        self.pipeline_config = pipeline_config
        self.is_preview_active = False
        self.is_recording = False
        self.was_recording = False
        self.start_time = 0
        self.transect_name = "transect"
        self.record_folder = None
        self.gst_context = None
        
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
    
    def start_preview(self):
        """Start camera preview"""
        if not self.is_preview_active:
            try:
                pipeline.config.start(self.pipeline)
                self.is_preview_active = True
                return True
            except Exception as e:
                logging.error(f"Failed to start preview: {e}")
                return False
        return True
    
    def stop_preview(self):
        """Stop camera preview"""
        if self.is_recording:
            return False
        
        if self.is_preview_active:
            try:
                pipeline.config.stop(self.pipeline)
                self.is_preview_active = False
                return True
            except Exception as e:
                logging.error(f"Failed to stop preview: {e}")
                return False
        return True
    
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

    

    def toggle_recording(self, custom_transect_name=None):
        """Toggle recording state"""
        # If not recording and not previewing, start preview first
        if not self.is_recording and not self.is_preview_active:
            if not self.start_preview():
                return False
        
        # Toggle recording state
        self.is_recording = not self.is_recording
        
        if self.is_recording:
            self.start_time = time.time()
            if custom_transect_name:
                self.transect_name = custom_transect_name.strip() or 'transect'
            self.record_folder = pipeline.recording.start(self.pipeline, self.transect_name)
            logging.info(f"Recording started with name {self.transect_name}")
        else:
            pipeline.recording.stop(self.pipeline)
            self.start_time = 0
            logging.info("Recording stopped.")
            # Automatically stop the preview when recording stops
            self.stop_preview()
        
        return True
    
    def restart_pipeline(self):
        """Restart the pipeline"""
        pipeline.config.restart(self.pipeline)
        self.is_recording = False
        self.start_time = 0
        return True
    
    def get_recording_state(self):
        """Get current recording state and elapsed time"""
        elapsed_time = (time.time() - self.start_time) if self.is_recording else 0
        return {
            'isRecording': self.is_recording, 
            'elapsedTime': elapsed_time
        }
    
    def update(self):
        """Update method to be called in a loop"""
        if not self.pipeline.is_done:
            if self.is_recording and not self.was_recording:
                self.record_folder = pipeline.recording.start(self.pipeline, self.transect_name)
                self.start_time = time.time()
            elif not self.is_recording and self.was_recording:
                pipeline.recording.stop(self.pipeline)
                self.start_time = 0
            
            self.was_recording = self.is_recording
        
        return not self.pipeline.is_done
    
    def cleanup(self):
        """Clean up resources"""
        if self.pipeline:
            if self.is_recording:
                pipeline.recording.stop(self.pipeline)
            if self.is_preview_active:
                pipeline.config.stop(self.pipeline)