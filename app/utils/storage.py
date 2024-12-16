import os
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_recording_folder(base_folder_name):
    base_path = os.path.join("/home/pi/Repos/avt/recordings", base_folder_name)
    folder_path = base_path + "_1"
    counter = 1

    logging.info(f"Creating recording folder with base path: {base_path}")

    # Check if the folder exists and if it's not empty, increment the name
    while os.path.exists(folder_path) and os.listdir(folder_path):
        logging.info(f"Folder {folder_path} already exists and is not empty. Incrementing counter.")
        counter += 1
        folder_path = f"{base_path}_{counter}"

    # Create the folder
    os.makedirs(folder_path, exist_ok=True)
    logging.info(f"Folder created at path: {folder_path}")
    return folder_path



def ensure_stream_image_exists():
    image_path = get_image_path("stream.jpg")
    if not os.path.exists(image_path):
        logging.info(f"{image_path} does not exist. Creating a blank image.")
        create_blank_jpg(image_path)
    else:
        logging.info(f"{image_path} already exists.")

def create_blank_jpg(image_path):
    width, height = 4112, 3008
    color = (255, 255, 255)  # white

    image = Image.new("RGB", (width, height), color)
    image.save(image_path, "JPEG")
    logging.info(f"Blank image created at path: {image_path}")

    return image_path

def get_image_path(filename):
    return os.path.join("/home/pi/Repos/avt/", filename)