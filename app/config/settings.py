# Camera and pipeline configuration
DEFAULT_PIPELINE = ("vimbasrc camera=DEV_000A4700155E settingsfile=/home/pi/Repos/avt-camera/app/config/camera_settings/current.xml name=vimbasrc ! "
                   "video/x-bayer,format=rggb ! bayer2rgb ! videoconvert ! "
                   "tee name=t "
                   "t. ! queue leaky=downstream max-size-buffers=1 max-size-time=0 max-size-bytes=0 ! "
                   "videoscale ! "
                   "capsfilter name=capsfilter_stream caps=video/x-raw,width=2056,height=1504 ! "
                   "jpegenc quality=65 ! appsink name=jpeg_sink emit-signals=true max-buffers=1 drop=true sync=false "
                   "t. ! queue ! "
                   "videoconvert ! "
                   "video/x-raw,format=RGB ! "
                   "appsink name=appsink_record emit-signals=true")
                   
# Path settings
APP_ROOT = "/home/pi/Repos/avt-camera"
STREAM_IMAGE_PATH = f"{APP_ROOT}/stream.jpg"
SETTINGS_PATH = f"{APP_ROOT}/app/config/camera_settings"
PARAMETERS_JSON = f"{SETTINGS_PATH}/parameters.json"
CURRENT_XML = f"{SETTINGS_PATH}/current.xml"

# Server settings
HOST = '0.0.0.0'
PORT = 80
DEBUG = True