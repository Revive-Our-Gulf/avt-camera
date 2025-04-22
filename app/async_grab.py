import sys
from typing import Optional, Tuple

from vmbpy import *
import time
initial_time = None


def print_usage():
    print('Usage:')
    print('    python asynchronous_grab.py [/x] [-x] [camera_id]')
    print('    python asynchronous_grab.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    /x, -x      If set, use AllocAndAnnounce mode of buffer allocation')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print()


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Tuple[Optional[str], AllocationMode]:
    args = sys.argv[1:]
    argc = len(args)

    allocation_mode = AllocationMode.AnnounceFrame
    cam_id = ""
    for arg in args:
        if arg in ('/h', '-h'):
            print_usage()
            sys.exit(0)
        elif arg in ('/x', '-x'):
            allocation_mode = AllocationMode.AllocAndAnnounceFrame
        elif not cam_id:
            cam_id = arg

    if argc > 2:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return (cam_id if cam_id else None, allocation_mode)


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
        try:
            cam.TriggerSource.set('Software')
            cam.TriggerSelector.set('FrameStart')
            cam.TriggerMode.set('On')
            cam.AcquisitionMode.set('Continuous')
            cam.ExposureAuto.set('Off')
            cam.ExposureTime.set(2000)
            stream = cam.get_streams()[0]
            stream.GVSPAdjustPacketSize.run()

            while not stream.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VmbFeatureError):
            abort('Failed to setup camera. Abort.')


def frame_handler(cam: Camera, stream: Stream, frame: Frame):
    global initial_time
    print(f'Trigger Time: {time.time() - initial_time:.3f} seconds')
    print(f"Frame: {frame}")


def main():
    global initial_time
    cam_id, allocation_mode = parse_args()

    with VmbSystem.get_instance():
        with get_camera(cam_id) as cam:

            setup_camera(cam)
            cam.start_streaming(frame_handler)

            try:
                initial_time = time.time()
                cam.TriggerSoftware.run()
                

            except VmbError as e:
                abort(f'Failed to trigger camera: {e}')


if __name__ == '__main__':
    main()