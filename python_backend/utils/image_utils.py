"""
Utility functions for image processing and validation
"""

import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image_path, target_size=(640, 480)):
    """
    Preprocess image for face detection
    
    Args:
        image_path: Path to image file
        target_size: Target size for resizing (width, height)
        
    Returns:
        Preprocessed image as numpy array
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to read image: {image_path}")
            return None
        
        # Resize if too large
        height, width = img.shape[:2]
        if width > target_size[0] or height > target_size[1]:
            img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
        
        # Enhance image quality
        img = enhance_image(img)
        
        return img
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def enhance_image(img):
    """
    Enhance image quality for better face detection
    
    Args:
        img: Image as numpy array
        
    Returns:
        Enhanced image
    """
    try:
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels
        enhanced = cv2.merge([l, a, b])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing image: {str(e)}")
        return img

def validate_image(image_path):
    """
    Validate if image is readable and has sufficient quality
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple (is_valid, message)
    """
    try:
        # Check if file exists
        img = cv2.imread(image_path)
        if img is None:
            return False, "Unable to read image file"
        
        # Check image size
        height, width = img.shape[:2]
        if width < 100 or height < 100:
            return False, "Image resolution too low (minimum 100x100)"
        
        # Check if image is too dark
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        if mean_brightness < 30:
            return False, "Image is too dark"
        
        if mean_brightness > 225:
            return False, "Image is overexposed"
        
        return True, "Image is valid"
        
    except Exception as e:
        return False, f"Error validating image: {str(e)}"

def draw_face_boxes(image_path, faces, output_path):
    """
    Draw bounding boxes around detected faces
    
    Args:
        image_path: Path to input image
        faces: List of detected faces with bbox
        output_path: Path to save output image
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return
        
        for face in faces:
            bbox = face['bbox']
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Draw rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw landmarks if available
            if 'landmarks' in face:
                landmarks = face['landmarks']
                for landmark_name, (x, y) in landmarks.items():
                    cv2.circle(img, (int(x), int(y)), 2, (0, 0, 255), -1)
        
        cv2.imwrite(output_path, img)
        logger.info(f"Saved annotated image to {output_path}")
        
    except Exception as e:
        logger.error(f"Error drawing face boxes: {str(e)}")

def calculate_face_quality(face_img):
    """
    Calculate quality score for a face image
    
    Args:
        face_img: Face image as numpy array
        
    Returns:
        Quality score (0-1)
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        
        # Calculate sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, laplacian_var / 500.0)
        
        # Calculate brightness
        mean_brightness = np.mean(gray)
        brightness_score = 1.0 - abs(mean_brightness - 128) / 128.0
        
        # Calculate contrast
        contrast = gray.std()
        contrast_score = min(1.0, contrast / 64.0)
        
        # Combined quality score
        quality_score = (sharpness_score * 0.4 + 
                        brightness_score * 0.3 + 
                        contrast_score * 0.3)
        
        return quality_score
        
    except Exception as e:
        logger.error(f"Error calculating face quality: {str(e)}")
        return 0.5
