import time

from vmbpy import *

from gstreamer import GstContext, GstPipeline, GstApp, Gst, GstVideo, GstPipeline
import gstreamer.utils as gst_utils
import utils

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject  
import numpy as np

import typing as typ

import cv2


image_counter = 0
global_record_path = None

def stop(pipeline):
    appsink = pipeline.get_by_name("appsink_record")
    appsink.set_property("emit_signals", False)

def start(pipeline, record_path):
    global global_record_path
    global_record_path = record_path
    appsink = pipeline.get_by_name("appsink_record")
    appsink.set_property("emit_signals", True)

    appsink.connect("new-sample", on_buffer, None)



def save_image(array):
    global image_counter, global_record_path
    timestamp = int(time.time())
    filename = global_record_path + f"/IMG_{image_counter}({timestamp}).jpg"
    cv2.imwrite(filename, array)
    image_counter += 1


def on_buffer(sink: GstApp.AppSink, data: typ.Any) -> Gst.FlowReturn:
    """ Callback on 'new-sample' signal """
    sample = sink.emit("pull-sample")  # Gst.Sample

    if isinstance(sample, Gst.Sample):
        array = extract_buffer(sample)
        print(
            "Received {type} with shape {shape} of type {dtype}".format(type=type(array),
                                                                        shape=array.shape,
                                                                        dtype=array.dtype))
        
        try:
            save_image(array)
            print("Image saved")
        except Exception as e:
            print(f"Error saving image: {e}")

        return Gst.FlowReturn.OK

    return Gst.FlowReturn.ERROR

def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """ Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray """

    buffer = sample.get_buffer()  # Gst.Buffer

    print(buffer.pts, buffer.dts, buffer.offset)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure

    # Print out the details of the caps_format
    print("Caps format:", caps_format.to_string())

    # GstVideo.VideoFormat
    video_format = GstVideo.VideoFormat.from_string(
        caps_format.get_value('format'))

    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = gst_utils.get_num_channels(video_format)

    print(f"Width: {w}, Height: {h}, Channels: {c}")

    buffer_size = buffer.get_size()
    array = np.ndarray(shape=(h, w, c), buffer=buffer.extract_dup(0, buffer_size),
                       dtype=np.uint8)

    return array