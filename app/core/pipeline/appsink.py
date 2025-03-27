import time

from vmbpy import *

from gstreamer import GstContext, GstPipeline, GstApp, Gst, GstVideo, GstPipeline
import gstreamer.utils as gst_utils
import app.core as core

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject  
import numpy as np

import typing as typ

import cv2

import datetime
from app.core.mavlink_connector import get_mavlink_timestamp, initialise_mavlink_session

import logging

import piexif
import piexif.helper
from fractions import Fraction


image_counter = 0
global_record_path = None

save_images = False

def init():
    initialise_mavlink_session()

def start(record_path):
    global image_counter, global_record_path, save_images
    global_record_path = record_path
    image_counter = 0
    save_images = True
    # Initialize the MAVLink session
    init()

def save_image(array):
    global image_counter, global_record_path
    
    try:
        # Get MAVLink data
        session = initialise_mavlink_session()
        response = session.get(
            "http://192.168.2.2/mavlink2rest/v1/mavlink/vehicles/1/components/1/messages/GLOBAL_POSITION_INT", 
            timeout=2
        )
        
        # Extract timestamp and geo data
        if response.status_code == 200:
            data = response.json()
            mavlink_time = get_mavlink_timestamp()
            
            # Extract GPS data (convert from integer format to decimal degrees)
            lat = data["message"]["lat"] / 10000000.0  # Convert from 1E7 format
            lon = data["message"]["lon"] / 10000000.0  # Convert from 1E7 format
            alt = data["message"]["alt"] / 1000.0      # Convert from mm to meters
            
            logging.info(f"Image geotagged: Lat={lat}, Lon={lon}, Alt={alt}")
            has_geo_data = True
        else:
            mavlink_time = datetime.datetime.now()
            has_geo_data = False
            logging.warning(f"Failed to get GPS data, status code: {response.status_code}")
    except Exception as e:
        mavlink_time = datetime.datetime.now()
        has_geo_data = False
        logging.warning(f"Error getting GPS data: {e}")
    
    # Format timestamp
    timestamp = mavlink_time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = global_record_path + f"/IMG_{image_counter}_({timestamp}).jpg"
    
    # Convert image and save
    rgb_image = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    
    # If GPS data is available, add EXIF metadata
    if has_geo_data:
        try:
            # Debugging: Log start of EXIF processing
            logging.debug("Starting EXIF metadata processing.")

            # Convert decimal coordinates to EXIF format (degrees, minutes, seconds)
            exif_dict = piexif.load(cv2.imencode('.jpg', rgb_image)[1].tobytes())
            
            # If no EXIF data exists, initialize it
            if "GPS" not in exif_dict:
                exif_dict["GPS"] = {}
            
            # Debugging: Log GPS data before conversion
            logging.debug(f"Raw GPS data - Lat: {lat}, Lon: {lon}, Alt: {alt}")
            
            # Convert latitude to EXIF format
            lat_deg = abs(lat)
            lat_deg_int = int(lat_deg)
            lat_min = (lat_deg - lat_deg_int) * 60
            lat_min_int = int(lat_min)
            lat_sec = (lat_min - lat_min_int) * 60
            
            # Convert longitude to EXIF format
            lon_deg = abs(lon)
            lon_deg_int = int(lon_deg)
            lon_min = (lon_deg - lon_deg_int) * 60
            lon_min_int = int(lon_min)
            lon_sec = (lon_min - lon_min_int) * 60
            
            # Debugging: Log converted GPS data
            logging.debug(f"Converted GPS data - Lat: {lat_deg_int}°{lat_min_int}'{lat_sec}\", "
                          f"Lon: {lon_deg_int}°{lon_min_int}'{lon_sec}\", Alt: {alt}m")
            
            # Set EXIF GPS Tags
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = "N" if lat >= 0 else "S"
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = [
                (lat_deg_int, 1),
                (lat_min_int, 1),
                (int(lat_sec * 100), 100)
            ]
            
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = "E" if lon >= 0 else "W"
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = [
                (lon_deg_int, 1),
                (lon_min_int, 1),
                (int(lon_sec * 100), 100)
            ]
            
            # Add altitude
            exif_dict["GPS"][piexif.GPSIFD.GPSAltitudeRef] = 1 if alt < 0 else 0
            exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (int(abs(alt) * 100), 100)
            
            # Add timestamp
            exif_bytes = piexif.dump(exif_dict)
            
            # Debugging: Log EXIF data before saving
            logging.debug(f"EXIF data prepared: {exif_dict}")
            
            # Save with EXIF data
            with open(filename, "wb") as f:
                f.write(cv2.imencode('.jpg', rgb_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])[1].tobytes())
            
            piexif.insert(exif_bytes, filename)
            
            # Debugging: Log successful save
            logging.debug(f"Image saved with EXIF metadata: {filename}")
        except Exception as e:
            # Debugging: Log any errors during EXIF processing
            logging.error(f"Error during EXIF metadata processing: {e}")
    else:
        # Just save the image without geo data
        cv2.imwrite(filename, rgb_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    
    image_counter += 1

def stop():
    global save_images
    save_images = False
    
def connect(pipeline):
    appsink = pipeline.get_by_name("appsink_record")
    appsink.connect("new-sample", on_buffer, None)


def on_buffer(sink: GstApp.AppSink, data: typ.Any) -> Gst.FlowReturn:
    """ Callback on 'new-sample' signal """
    sample = sink.emit("pull-sample")  # Gst.Sample

    if isinstance(sample, Gst.Sample):
        array = extract_buffer(sample)
        # print(
        #     "Received {type} with shape {shape} of type {dtype}".format(type=type(array),
        #                                                                 shape=array.shape,
        #                                                                 dtype=array.dtype))
        
        try:
            if (save_images):
                save_image(array)
                print("Image saved")
        except Exception as e:
            print(f"Error saving image: {e}")

        return Gst.FlowReturn.OK

    return Gst.FlowReturn.ERROR

def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """ Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray """

    buffer = sample.get_buffer()  # Gst.Buffer

    # print(buffer.pts, buffer.dts, buffer.offset)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure

    # Print out the details of the caps_format
    # print("Caps format:", caps_format.to_string())

    # GstVideo.VideoFormat
    video_format = GstVideo.VideoFormat.from_string(
        caps_format.get_value('format'))

    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = gst_utils.get_num_channels(video_format)

    # print(f"Width: {w}, Height: {h}, Channels: {c}")

    buffer_size = buffer.get_size()
    array = np.ndarray(shape=(h, w, c), buffer=buffer.extract_dup(0, buffer_size),
                       dtype=np.uint8)

    return array