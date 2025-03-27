import logging
import os
import sys
import threading
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_socketio import SocketIO

from app.core.network import modify_mtu
from app.core.storage import ensure_stream_image_exists
from app.core.camera import controller as camera_controller_module 
from app.core.streamer import ImageStreamer
from config.settings import DEFAULT_PIPELINE, HOST, PORT, DEBUG, STREAM_IMAGE_PATH
from app.api.socket_handlers import register_handlers
from app.api.web_routes import web_routes, set_camera_controller

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.WARNING)

def create_app():
    """Create and configure Flask application"""
    app = Flask(
        __name__, 
        template_folder='/home/pi/Repos/avt-camera/app/ui/templates',
        static_folder='/home/pi/Repos/avt-camera/app/ui/static'
    )
    socketio = SocketIO(app)
    app.register_blueprint(web_routes)
    return app, socketio

def setup_camera():
    """Initialize camera and related services"""
    # Network and storage setup
    modify_mtu()
    ensure_stream_image_exists()
    
    # Initialize camera controller
    camera_controller = camera_controller_module.CameraController(DEFAULT_PIPELINE)
    if not camera_controller.setup_pipeline():
        logging.error("Failed to setup camera pipeline")
        return None
    
    return camera_controller

def run_application():
    """Main application entry point"""
    # Create Flask application
    app, socketio = create_app()
    
    # Setup camera
    camera_controller = setup_camera()
    if not camera_controller:
        return
    
    # Setup routes and handlers
    set_camera_controller(camera_controller)
    register_handlers(socketio, camera_controller)
    
    # Start image streamer
    streamer = ImageStreamer(socketio, camera_controller, STREAM_IMAGE_PATH)
    streamer.start()
    
    # Start Flask in a separate thread
    server_thread = threading.Thread(
        target=lambda: socketio.run(
            app,
            host=HOST,
            port=PORT,
            debug=DEBUG,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
    )
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Main application loop
        while True:
            camera_controller.update()
            time.sleep(0.25)
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
    finally:
        streamer.stop()
        if camera_controller:
            camera_controller.cleanup()
        logging.info("Application terminated")

if __name__ == "__main__":
    run_application()