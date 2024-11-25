# import required GStreamer and GLib modules
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GLib, GstRtspServer

# initialize GStreamer and start the GLib Mainloop
Gst.init(None)
mainloop = GLib.MainLoop()

# Create the RTSP Server
server = GstRtspServer.RTSPServer()
mounts = server.get_mount_points()

# define the pipeline to record images ad attach it to the "stream1" endpoint
vimbasrc_factory = GstRtspServer.RTSPMediaFactory()
vimbasrc_factory.set_launch('vimbasrc camera=DEV_000A4700155E ! videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency ! queue ! rtph264pay name=pay0')
mounts.add_factory("/stream1", vimbasrc_factory)
server.attach(None)

mainloop.run()