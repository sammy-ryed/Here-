"""
Face Detection using RetinaFace
Detects multiple faces in images with high accuracy
OPTIMIZED: Smart processing - only enhance poor quality images
"""

import cv2
import numpy as np
import os
try:
    from retinaface import RetinaFace
except ImportError:
    from retina_face import RetinaFace
import logging
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

class FaceDetector:
    """Face detection using RetinaFace with smart enhancement"""
    
    def __init__(self):
        """Initialize RetinaFace detector"""
        self.detector = None
        self.ready = True
        self.detection_cache = {}  # Cache for faster repeated detections
        logger.info("FaceDetector initialized with RetinaFace (GPU-optimized)")
    
    def is_ready(self):
        """Check if detector is ready"""
        return self.ready
    
    def _get_image_hash(self, image_input):
        """Generate hash for image caching - handles both file paths and numpy arrays"""
        if isinstance(image_input, str):
            # File path
            with open(image_input, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        else:
            # Numpy array
            return hashlib.md5(image_input.tobytes()).hexdigest()

    def _calculate_image_quality(self, img):
        """
        Calculate image quality metrics to decide if enhancement is needed
        Returns: (blur_score, brightness_score, needs_enhancement)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate blur (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness_score = np.mean(gray)
        
        # Decide if enhancement needed
        # Low blur (<100) = blurry image → needs enhancement
        # Low brightness (<100) or high brightness (>180) → needs enhancement
        needs_enhancement = (blur_score < 100 or 
                           brightness_score < 100 or 
                           brightness_score > 180)
        
        return blur_score, brightness_score, needs_enhancement
    
    def detect_faces(self, image_input):
        """
        Detect faces in an image with SMART enhancement
        Only applies upscaling/enhancements if image quality is poor
        
        Args:
            image_input: Path to the image file (str) or numpy array
            
        Returns:
            List of detected faces with bounding boxes and landmarks
        """
        try:
            # Check cache first
            img_hash = self._get_image_hash(image_input)
            if img_hash in self.detection_cache:
                logger.info("✅ Using cached detection result")
                return self.detection_cache[img_hash]
            
            # Read image - handle both file paths and numpy arrays
            if isinstance(image_input, str):
                # File path
                img = cv2.imread(image_input)
                if img is None:
                    logger.error(f"Could not read image from path: {image_input}")
                    return []
            else:
                # Numpy array
                img = image_input.copy() if image_input is not None else None
                if img is None:
                    logger.error("Received None as image input")
                    return []
            
            height, width = img.shape[:2]
            
            # SMART PROCESSING: Check image quality first
            blur_score, brightness, needs_enhancement = self._calculate_image_quality(img)
            
            logger.info(f"Image Quality - Blur: {blur_score:.1f}, Brightness: {brightness:.1f}, "
                       f"Enhancement needed: {needs_enhancement}")
            
            # For numpy arrays, we use the original image directly
            detection_image = img
            scale_factor = 1.0
            
            # ONLY enhance if image quality is poor OR it's a distant group photo with small faces
            if needs_enhancement or (width > 1200 or height > 1200):
                logger.info("⚡ SMART MODE: Enhancing poor quality image")
                
                # Upscale only if needed
                if width > 800 or height > 800:
                    scale_factor = 2.0
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    img_enhanced = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                    logger.info(f"  Upscaled: {width}x{height} → {new_width}x{new_height}")
                else:
                    img_enhanced = img.copy()
                
                # Apply sharpening only if blurry
                if blur_score < 100:
                    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                    img_enhanced = cv2.filter2D(img_enhanced, -1, kernel)
                    logger.info("  Applied sharpening (image was blurry)")
                
                # Apply contrast enhancement only if brightness is off
                if brightness < 100 or brightness > 180:
                    img_enhanced = cv2.convertScaleAbs(img_enhanced, alpha=1.2, beta=10)
                    logger.info("  Applied contrast enhancement (brightness was off)")
                
                # Use enhanced image
                detection_image = img_enhanced
            else:
                logger.info("🚀 FAST MODE: Good quality image, skipping enhancements")
            
            # IMPROVED: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # This helps detect faces at different angles and lighting conditions
            lab = cv2.cvtColor(detection_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            detection_image = cv2.merge([l, a, b])
            detection_image = cv2.cvtColor(detection_image, cv2.COLOR_LAB2BGR)
            logger.info("  Applied CLAHE for better angle detection")
            
            # Detect faces using RetinaFace - it can accept numpy arrays directly
            # BALANCED: 0.45 threshold - stricter to reduce false positives while still detecting real faces
            faces = RetinaFace.detect_faces(
                detection_image,
                threshold=0.45,  # Higher = fewer false positives
                allow_upscaling=False  # We handle upscaling manually now
            )
            
            if not isinstance(faces, dict):
                logger.info("No faces detected")
                return []
            
            # Convert to list format and adjust coordinates if upscaled
            detected_faces = []
            for key, face_data in faces.items():
                # Extract bounding box
                facial_area = face_data['facial_area']
                bbox = [facial_area[0], facial_area[1], facial_area[2], facial_area[3]]
                
                # If we upscaled, scale bbox back to original coordinates
                if scale_factor != 1.0:
                    bbox = [coord / scale_factor for coord in bbox]
                
                # Extract landmarks
                landmarks = face_data['landmarks']
                if scale_factor != 1.0:
                    # Scale landmarks back too
                    for landmark_key in landmarks:
                        landmarks[landmark_key] = tuple(coord / scale_factor for coord in landmarks[landmark_key])
                
                # Calculate confidence score
                confidence = face_data.get('score', 0.99)
                
                detected_faces.append({
                    'bbox': bbox,
                    'landmarks': landmarks,
                    'confidence': confidence
                })
            
            # Log detection result with appropriate message for input type
            input_type = "file" if isinstance(image_input, str) else "image array"
            logger.info(f"✅ DETECTED {len(detected_faces)} FACE(S) in {input_type}")
            
            # Cache the result
            self.detection_cache[img_hash] = detected_faces
            
            return detected_faces
            
        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}", exc_info=True)
            return []
    
    def detect_faces_from_array(self, img_array):
        """
        Detect faces from numpy array (BGR format)
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            List of detected faces
        """
        try:
            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = RetinaFace.detect_faces(img_rgb)
            
            if not isinstance(faces, dict):
                return []
            
            detected_faces = []
            for key, face_data in faces.items():
                facial_area = face_data['facial_area']
                bbox = [facial_area[0], facial_area[1], facial_area[2], facial_area[3]]
                landmarks = face_data['landmarks']
                confidence = face_data.get('score', 0.99)
                
                detected_faces.append({
                    'bbox': bbox,
                    'landmarks': landmarks,
                    'confidence': confidence
                })
            
            return detected_faces
            
        except Exception as e:
            logger.error(f"Error detecting faces from array: {str(e)}")
            return []
    
    def align_face(self, image, landmarks):
        """
        Align face using landmarks for better recognition
        
        Args:
            image: Image as numpy array
            landmarks: Dictionary of facial landmarks
            
        Returns:
            Aligned face image
        """
        try:
            # Get eye coordinates
            left_eye = landmarks['left_eye']
            right_eye = landmarks['right_eye']
            
            # Calculate angle between eyes
            dY = right_eye[1] - left_eye[1]
            dX = right_eye[0] - left_eye[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # Calculate center point between eyes
            eyes_center = ((left_eye[0] + right_eye[0]) // 2, 
                          (left_eye[1] + right_eye[1]) // 2)
            
            # Get rotation matrix
            M = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
            
            # Perform affine transformation
            aligned = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]),
                                    flags=cv2.INTER_CUBIC)
            
            return aligned
            
        except Exception as e:
            logger.error(f"Error aligning face: {str(e)}")
            return image
    
    def extract_face_roi(self, image_path, bbox, margin=20):
        """
        Extract face region of interest with margin
        
        Args:
            image_path: Path to image
            bbox: Bounding box [x1, y1, x2, y2]
            margin: Margin to add around face
            
        Returns:
            Face ROI as numpy array
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            height, width = img.shape[:2]
            
            # Add margin and ensure within image bounds
            x1 = max(0, bbox[0] - margin)
            y1 = max(0, bbox[1] - margin)
            x2 = min(width, bbox[2] + margin)
            y2 = min(height, bbox[3] + margin)
            
            # Extract face ROI
            face_roi = img[int(y1):int(y2), int(x1):int(x2)]
            
            return face_roi
            
        except Exception as e:
            logger.error(f"Error extracting face ROI: {str(e)}")
            return None
