import sys
from typing import Optional
from vmbpy import *
import time

from utils import camera_utils
import os


def print_usage():
    print('Usage:')
    print('    python synchronous_grab.py [camera_id]')
    print('    python synchronous_grab.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print()


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Optional[str]:
    args = sys.argv[1:]
    argc = len(args)

    for arg in args:
        if arg in ('/h', '-h'):
            print_usage()
            sys.exit(0)

    if argc > 1:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return None if argc == 0 else args[0]


def get_camera(camera_id: Optional[str]) -> Camera:
    with VmbSystem.get_instance() as vmb:
        if camera_id:
            try:
                return vmb.get_camera_by_id(camera_id)

            except VmbCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

        else:
            cams = vmb.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')

            return cams[0]


def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            stream = cam.get_streams()[0]
            stream.GVSPAdjustPacketSize.run()
            while not stream.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VmbFeatureError):
            pass





def main():
    cam_id = parse_args()

    with VmbSystem.get_instance():
        with get_camera(cam_id) as cam:
            setup_camera(cam)

            settings_file = 'strobe_configured.xml'.format(cam.get_id())
            
            try:
                cam.load_settings(settings_file, PersistType.All)
            except VmbCameraError as e:
                abort(f"Failed to load settings from '{settings_file}'. Error: {e}")

            # Print camera settings
            try:
                frame_rate = cam.AcquisitionFrameRate.get()
                print(f"Frame rate: {frame_rate}")

                exposure_time = cam.ExposureTime.get()
                print(f"Exposure time: {exposure_time}")

            except VmbFeatureError as e:
                abort(f"Failed to retrieve camera settings. Error: {e}")

            # Acquire 10 frames with a custom timeout (default is 2000ms) per frame acquisition.
            previous_time = None
            
            for frame in cam.get_frame_generator(limit=None, timeout_ms=3000):
                current_time = time.time()
                if previous_time is not None:
                    time_diff = current_time - previous_time
                    print('Time between frames: {:.2f} seconds'.format(time_diff), flush=True)
                print('Got {}'.format(frame), flush=True)
                

                print(f"Frame size: {frame.get_buffer_size()}")
                width = frame.get_width()
                height = frame.get_height()
                pixel_format = frame.get_pixel_format()

                print(f"Frame width: {width}")
                print(f"Frame height: {height}")
                print(f"Pixel format: {pixel_format}")
                previous_time = current_time

if __name__ == '__main__':
    main()
