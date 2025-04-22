import sys
from typing import Optional

from vmbpy import *

import time


def print_preamble():
    print('//////////////////////////////////////')
    print('/// VmbPy Synchronous Grab Example ///')
    print('//////////////////////////////////////\n')


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
        cam.ExposureAuto.set('Off')
        cam.ExposureTime.set(2000)
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

            initial_time = time.time()
            frame = cam.get_frame()
            print(f'Trigger Time: {time.time() - initial_time:.3f} seconds')
            print(f"Frame: {frame}")



if __name__ == '__main__':
    main()