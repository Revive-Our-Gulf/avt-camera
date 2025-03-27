import logging
import subprocess
import psutil
import utils.json
import utils.xml
from app.api import handlers

def register_handlers(socketio, camera_controller):
    @socketio.on('toggle_recording')
    def handle_toggle_recording(data=None):
        try:
            folderName = data.get('folderName', '').strip() if data else None
            success = camera_controller.toggle_recording(folderName)
            if not success:
                socketio.emit('error', {'message': 'Failed to toggle recording'})
            
            # Emit updated states
            socketio.emit('current_recording_state', camera_controller.get_recording_state())
            socketio.emit('preview_state', {'isActive': camera_controller.is_preview_active})
        except Exception as e:
            logging.error(f"Error in toggle_recording: {e}")
            socketio.emit('error', {'message': str(e)})

    @socketio.on('get_recording_state')
    def handle_get_recording_state(data=None):
        socketio.emit('current_recording_state', camera_controller.get_recording_state())

    @socketio.on('start_preview')
    def handle_start_preview():
        if camera_controller.pipeline is None:
            socketio.emit('error', {'message': 'Camera not available. Please restart the application.'})
            return
        
        success = camera_controller.start_preview()
        if success:
            socketio.emit('preview_state', {'isActive': camera_controller.is_preview_active})
        else:
            socketio.emit('error', {'message': 'Failed to start camera preview'})

    @socketio.on('stop_preview')
    def handle_stop_preview():
        if camera_controller.pipeline is None:
            socketio.emit('error', {'message': 'Camera not available. Please restart the application.'})
            return
        
        if camera_controller.is_recording:
            socketio.emit('error', {'message': 'Cannot stop preview while recording is active'})
            return
        
        success = camera_controller.stop_preview()
        if success:
            socketio.emit('preview_state', {'isActive': camera_controller.is_preview_active})
        else:
            socketio.emit('error', {'message': 'Failed to stop camera preview'})

    @socketio.on('get_preview_state')
    def handle_get_preview_state():
        socketio.emit('preview_state', {'isActive': camera_controller.is_preview_active})

    @socketio.on('restart_pipeline')
    def handle_restart_pipeline():
        success = camera_controller.restart_pipeline()
        if success:
            socketio.emit('current_recording_state', camera_controller.get_recording_state())
            socketio.emit('preview_state', {'isActive': camera_controller.is_preview_active})
        else:
            socketio.emit('error', {'message': 'Failed to restart pipeline'})

    @socketio.on('get_strobe_state')
    def handle_get_strobe_state():
        parameters = core.json.get_parameters('/home/pi/Repos/avt-camera/app/settings/parameters.json')
        values = core.xml.get_values_from_xml('/home/pi/Repos/avt-camera/app/settings/current.xml', parameters)
        current_value = values.get('LineSource+Line2', 'Off')
        socketio.emit('strobe_state', {'value': current_value})

    @socketio.on('get_storage')
    def emit_storage_info():
        disk_usage = psutil.disk_usage('/')
        free_space_gb = disk_usage.free / (1024 * 1024 * 1024)
        total_space_gb = disk_usage.total / (1024 * 1024 * 1024)
        socketio.emit('storage_info', {
            'free_space_gb': free_space_gb,
            'total_space_gb': total_space_gb
        })

    @socketio.on('get_time_sync')
    def check_time_sync():
        try:
            result = subprocess.run(['chronyc', 'tracking'], capture_output=True, text=True)
            if '192.168.2.2' in result.stdout and 'Stratum         : ' in result.stdout:
                # Extract the Last offset value
                last_offset_line = next(line for line in result.stdout.split('\n') if 'Last offset' in line)
                last_offset = float(last_offset_line.split(':')[1].strip().split()[0])
                
                # Format the offset in a human-readable way
                if abs(last_offset) < 1e-6:
                    human_readable_offset = f"{last_offset * 1e9:.1f} ns"
                elif abs(last_offset) < 1e-3:
                    human_readable_offset = f"{last_offset * 1e6:.1f} µs"
                elif abs(last_offset) < 1:
                    human_readable_offset = f"{last_offset * 1e3:.1f} ms"
                elif abs(last_offset) < 60:
                    human_readable_offset = f"{last_offset:.1f} s"
                elif abs(last_offset) < 3600:
                    human_readable_offset = f"{last_offset / 60:.1f} min"
                else:
                    human_readable_offset = f"{last_offset / 3600:.1f} h"
                    
                socketio.emit('time_sync_status', {
                    'status': 'success', 
                    'message': f'Time is synced with BlueOS. Last offset: {human_readable_offset}'
                })
            else:
                socketio.emit('time_sync_status', {
                    'status': 'error', 
                    'message': 'Time is not synced with BlueOS'
                })
        except Exception as e:
            socketio.emit('time_sync_status', {'status': 'error', 'message': str(e)})

    @socketio.on('update_parameters')
    def handle_update_parameters_wrapper(data):
        handlers.handle_update_parameters(
            data, 
            camera_controller.pipeline, 
            camera_controller.is_preview_active, 
            camera_controller.is_recording
        )

    @socketio.on('reset_parameters')
    def handle_reset_parameters_wrapper():
        handlers.handle_reset_parameters(camera_controller.pipeline)