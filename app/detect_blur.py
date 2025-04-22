import cv2
import numpy as np

# Default threshold value
FOCUS_THRESHOLD = 30

def set_focus_threshold(threshold):
    """Set the global threshold value for blur detection"""
    global FOCUS_THRESHOLD
    FOCUS_THRESHOLD = threshold
    return FOCUS_THRESHOLD

def get_focus_threshold():
    """Get the current threshold value"""
    return FOCUS_THRESHOLD

def variance_of_laplacian(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    lap_abs = np.abs(lap)
    threshold = FOCUS_THRESHOLD  # Use the global threshold
    strong_edges_mask = lap_abs > threshold
    
    height, width = gray.shape
    lap_bgr = np.zeros((height, width, 3), dtype=np.uint8)
    
    lap_bgr[strong_edges_mask] = [0, 0, 255]
    
    score = laplacian_score(gray)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = f"Laplacian Score: {score:.2f}"
    text_size = cv2.getTextSize(text, font, 3, 2)[0]
    text_x = min(10, width - text_size[0] - 10)
    text_y = max(30, text_size[1] + 10)
    cv2.putText(lap_bgr, text, (text_x, text_y), font, 3, (255, 255, 255), 2, cv2.LINE_AA)
    
    return lap_bgr

def laplacian_score(image_grey):
    lap = cv2.Laplacian(image_grey, cv2.CV_64F)
    return lap.var()