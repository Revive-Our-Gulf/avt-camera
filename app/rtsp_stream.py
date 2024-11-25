#!/usr/bin/env python3

'''
Simple example to demonstrate using GstRtspServer in Python with video source from camera
'''
import argparse
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GLib, Gst, GstRtspServer


def start_rtsp_server(rtsp_port, device, stream_name):
    server = GstRtspServer.RTSPServer.new()
    server.props.service = rtsp_port
    server.attach(None)

    factory = GstRtspServer.RTSPMediaFactory.new()
    launch_str = ("gst-launch-1.0 multifilesrc location=Recordings/stream.jpg loop=true start-index=0 stop-index=0  ! image/jpeg,width=4112,height=3008,type=video,framerate=6/1 ! identity ! jpegdec ! videoscale ! videoconvert ! "
                  "x264enc speed-preset=ultrafast tune=zerolatency ! h264parse ! rtph264pay name=pay0 pt=96")
    # launch_str = ("multifilesrc location=Recordings/stream.h264 loop=true start-index=0 stop-index=0 ! "
    #             "h264parse ! avdec_h264 ! videoconvert ! "
    #             "x264enc speed-preset=ultrafast tune=zerolatency ! h264parse ! rtph264pay name=pay0 pt=96")
    factory.set_launch(launch_str)
    factory.set_shared(True)

    server.get_mount_points().add_factory("/" + stream_name, factory)
    print(f"Device: {device} \nUnder: rtsp://localhost:{rtsp_port}/{stream_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--camera",
        help="Camera file path",
        type=str,
        default="/dev/video0",
    )
    parser.add_argument("--rtsp-port", default="8554")
    parser.add_argument("--stream-name", default="stream")
    args = parser.parse_args()
    Gst.init(None)
    start_rtsp_server(args.rtsp_port, args.camera, args.stream_name)
    loop = GLib.MainLoop()
    loop.run()
