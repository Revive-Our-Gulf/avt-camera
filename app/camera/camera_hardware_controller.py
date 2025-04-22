import threading
import time
import cv2
import functools
from datetime import datetime
from vmbpy import Camera, Stream, Frame, FrameStatus, VmbFeatureError, PixelFormat, VmbSystem
from detect_blur import variance_of_laplacian
from settings_manager import SettingsManager
import numpy as np
from state_machine import CameraState, TriggerMode

class CameraHardwareController:
    def __init__(self, state_machine, frame_save_queue, mavlink_handler):
        self.state_machine = state_machine
        self.frame_save_queue = frame_save_queue
        self.current_camera = None
        self.camera_lock = threading.Lock()
        self.frame_buffer = None
        self.frame_lock = threading.Lock()
        self.focus_mode = False
        self.settings_manager = SettingsManager()
        self.mavlink_handler = mavlink_handler

        self.frame_index = 0
        self.start_time = None
        self.frame_trigger_time = None
        self.frame_trigger_time_lock = threading.Lock()

        self.time_interval = 1
        self.preview_interval = 0.5

        self.last_telemetry = None

    def set_time_interval(self, interval_seconds):
        self.time_interval = interval_seconds
        print(f"Time interval set to {interval_seconds} seconds")
        
    def set_preview_interval(self, interval_seconds):
        self.preview_interval = interval_seconds
        print(f"Preview interval set to {interval_seconds} seconds")

    def requires_camera(default_return=None):
        """Decorator that checks if a camera is available before executing a method"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                camera = self.get_camera()
                if not camera:
                    print(f"No camera available for {func.__name__}")
                    return default_return
                return func(self, camera, *args, **kwargs)
            return wrapper
        return decorator

    def toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode
        return self.focus_mode

    def setup_camera(self, cam):
        self.load_saved_settings()
        cam.TriggerSource.set('Software')
        cam.TriggerSelector.set('FrameStart')
        cam.TriggerMode.set('On')
        cam.AcquisitionMode.set('Continuous')

        cam.set_pixel_format(PixelFormat.BayerRG12)
                
        try:
            stream = cam.get_streams()[0]
            stream.GVSPAdjustPacketSize.run()
            while not stream.GVSPAdjustPacketSize.is_done():
                pass
        except (AttributeError, VmbFeatureError) as e:
            print(f"An error occurred during stream setup or packet size adjustment: {e}")
    
    def frame_handler(self, cam: Camera, stream: Stream, frame: Frame):
        print(f"Frame received: Status={frame.get_status()}, FrameIndex={self.frame_index}")
        if frame.get_status() == FrameStatus.Complete:

            image = frame.as_numpy_ndarray()
            image = cv2.cvtColor(image, cv2.COLOR_BayerRG2RGB)
            
            if image.dtype == np.uint16:
                image = (image / 16).astype(np.uint8)
            
            if self.focus_mode:
                image = variance_of_laplacian(image)

            # image_stream = cv2.resize(image, (1028, 752), interpolation=cv2.INTER_AREA)
            image_stream = image

        
            _, jpeg = cv2.imencode('.jpg', image_stream)
            with self.frame_lock:
                self.frame_buffer = jpeg.tobytes()

            with self.frame_trigger_time_lock:
                trigger_time = self.frame_trigger_time
            
            if self.state_machine.should_save() and not self.frame_save_queue.full():
                print(f"Frame {self.frame_index} processed successfully")
                self.frame_save_queue.put((image.copy(), trigger_time, self.frame_index, self.last_telemetry))
                        
        
        cam.queue_frame(frame)
    
    def get_latest_frame(self):
        with self.frame_lock:
            return self.frame_buffer
    
    def start_camera_thread(self):
        thread = threading.Thread(target=self._camera_thread, daemon=True)
        thread.start()
        return thread

    def _camera_thread(self):
        retry_count = 0
        max_retries = 20
        retry_delay = 5
        
        with VmbSystem.get_instance() as vmb:
            while retry_count < max_retries:
                try:
                    camera = self._find_camera(vmb)
                    if not camera:
                        print("No cameras found! Retrying in 5 seconds...")
                        time.sleep(retry_delay)
                        retry_count += 1
                        continue
                        
                    print(f"Attempt {retry_count+1}: Trying to access camera in Full mode...")
                    self._run_camera_loop(camera)
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if "invalid Mode 'AccessMode.Full'" in str(e):
                        print(f"Camera not available in Full mode (attempt {retry_count}/{max_retries})")
                        print(f"Waiting {retry_delay} seconds before retrying...")
                    else:
                        print(f"Camera thread error: {e}")
                        print(f"Retrying in {retry_delay} seconds (attempt {retry_count}/{max_retries})...")
                    
                    if retry_count >= max_retries:
                        print("Maximum retries reached. Camera could not be accessed in Full mode.")
                    else:
                        time.sleep(retry_delay)

    def _find_camera(self, vmb):
        cameras = vmb.get_all_cameras()
        if not cameras:
            print("No cameras found!")
            return None
        return cameras[0]

    def _run_camera_loop(self, camera):
        print(f"Camera found: {camera.get_name()}")
        with camera:
            try:
                with self.camera_lock:
                    self.current_camera = camera

                self.setup_camera(camera)
                camera.start_streaming(self.frame_handler)
                self._process_frames(camera)
            finally:
                camera.stop_streaming()
                with self.camera_lock:
                    self.current_camera = None

    def interval_met(self, target_interval):
        current_time = time.time()
        trigger_time = self.frame_index * target_interval + self.start_time
        if current_time >= trigger_time:
            return True
        return False

    def trigger_frame(self, camera):
        with self.frame_trigger_time_lock:
            self.frame_trigger_time = datetime.now()
        self.frame_index += 1
        self.last_telemetry = self.mavlink_handler.get_telemetry()
        print(f"Triggering frame {self.frame_index}")   
        camera.TriggerSoftware.run()

    def _process_frames(self, camera):
        previous_time = time.time()
        while True:
            if self.state_machine.should_stream():
                if self.state_machine.get_state() == CameraState.PREVIEW:
                    current_time = time.time()
                    if current_time - previous_time >= self.preview_interval:
                        print("TRIGGERING PREVIEW")
                        self.trigger_frame(camera)
                        previous_time = current_time
                        
                elif self.state_machine.get_state() == CameraState.WRITE:
                    if self.state_machine.trigger_mode == TriggerMode.TIME:
                        current_time = time.time()
                        if current_time - previous_time >= self.time_interval:
                            print("TRIGGERING TIME")
                            self.trigger_frame(camera)
                            previous_time = current_time
                    elif self.state_machine.trigger_mode == TriggerMode.DISTANCE:
                        if self.mavlink_handler and self.mavlink_handler.should_trigger_photo_by_distance():
                            print("TRIGGERING DISTANCE")
                            self.trigger_frame(camera)
                            self.mavlink_handler.reset_distance_tracking()

            time.sleep(0.01)
    
    def get_camera(self):
        with self.camera_lock:
            return self.current_camera
        
    @requires_camera(default_return={})
    def get_camera_settings(self, camera):
        settings = {}
        parameters_info = self.settings_manager.get_parameters_definitions()
        
        for param in parameters_info["parameters"]:
            param_id = param["id"]
            if hasattr(camera, param_id):
                try:
                    value = camera.__getattribute__(param_id).get()
                    settings[param_id] = value
                except Exception as e:
                    print(f"Error retrieving setting {param_id}: {e}")
        
        return settings

    def _apply_parameter(self, camera, param_id, value, param_type=None):
        try:
            if param_type == "select":
                self._update_select_parameter(camera, param_id, value)
            else:
                camera.__getattribute__(param_id).set(value)
            print(f"Applied parameter: {param_id}={value}")
            return True
        except Exception as e:
            print(f"Error applying parameter {param_id}: {e}")
            return False

    def _get_parameter_types(self):
        """Get a dictionary mapping parameter IDs to their types"""
        parameters_info = self.settings_manager.get_parameters_definitions()
        return {param["id"]: param["type"] for param in parameters_info["parameters"]}

    @requires_camera(default_return=False)
    def apply_specific_settings(self, camera, settings):
        param_types = self._get_parameter_types()
        
        success = True
        for param_id, value in settings.items():
            if hasattr(camera, param_id):
                if not self._apply_parameter(camera, param_id, value, param_types.get(param_id)):
                    success = False
        
        return success

    @requires_camera(default_return=False)
    def load_saved_settings(self, camera):             
        parameters_info = self.settings_manager.get_parameters_definitions()
        param_types = self._get_parameter_types()
        
        for param in parameters_info["parameters"]:
            param_id = param["id"]
            value = param.get("value", param.get("default"))
            
            if hasattr(camera, param_id):
                self._apply_parameter(camera, param_id, value, param_types.get(param_id))
        
        return True
            
    def _update_select_parameter(self, camera, param_id, value):
        feature = camera.__getattribute__(param_id)
        entries = feature.get_available_entries()
        
        for entry in entries:
            if str(entry) == str(value):
                feature.set(entry)
                break

