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

from app.core.mavlink_connector import get_mavlink_timestamp
import datetime
from app.core.mavlink_connector import get_mavlink_timestamp, initialise_mavlink_session

import logging


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
    mavlink_time = get_mavlink_timestamp()
    
    # Fall back to system time if MAVLink timestamp fails
    if mavlink_time is None:
        mavlink_time = datetime.datetime.now()
        logging.warning("Using system time as fallback for image timestamp")
        
    timestamp = mavlink_time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = global_record_path + f"/IMG_{image_counter}_({timestamp}).jpg"
    
    rgb_image = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    
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