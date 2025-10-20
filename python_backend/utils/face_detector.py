"""
Face Detection using RetinaFace
Detects multiple faces in images with high accuracy
"""

import cv2
import numpy as np
import os
try:
    from retinaface import RetinaFace
except ImportError:
    from retina_face import RetinaFace
import logging

logger = logging.getLogger(__name__)

class FaceDetector:
    """Face detection using RetinaFace"""
    
    def __init__(self):
        """Initialize RetinaFace detector"""
        self.detector = None
        self.ready = True
        logger.info("FaceDetector initialized with RetinaFace")
    
    def is_ready(self):
        """Check if detector is ready"""
        return self.ready
    
    def detect_faces(self, image_path):
        """
        Detect faces in an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected faces with bounding boxes and landmarks
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to read image: {image_path}")
                return []
            
            # For distant photos, upscale the image for better detection
            height, width = img.shape[:2]
            
            # If image is large (>1000px), it's likely a distant group photo
            # Upscale it for better face detection
            if width > 1000 or height > 1000:
                # Increase resolution by 1.5x for better small face detection
                scale_factor = 1.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img_upscaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                
                # Apply sharpening to enhance face features
                kernel = np.array([[-1,-1,-1],
                                   [-1, 9,-1],
                                   [-1,-1,-1]])
                img_upscaled = cv2.filter2D(img_upscaled, -1, kernel)
                
                # Save temporarily
                temp_path = image_path.replace('.jpg', '_upscaled.jpg')
                cv2.imwrite(temp_path, img_upscaled)
                detection_path = temp_path
                
                logger.info(f"Upscaled image from {width}x{height} to {new_width}x{new_height} for better detection")
            else:
                detection_path = image_path
            
            # Detect faces using RetinaFace with lower threshold for distant photos
            faces = RetinaFace.detect_faces(
                detection_path,
                threshold=0.3,  # Lower threshold (default is 0.9) to detect more faces
                allow_upscaling=True  # Allow RetinaFace to upscale if needed
            )
            
            # Clean up temp file if created
            if detection_path != image_path:
                try:
                    os.remove(detection_path)
                except:
                    pass
            
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
                if detection_path != image_path:
                    scale_factor = 1.5
                    bbox = [coord / scale_factor for coord in bbox]
                
                # Extract landmarks
                landmarks = face_data['landmarks']
                if detection_path != image_path:
                    # Scale landmarks back too
                    scale_factor = 1.5
                    for landmark_key in landmarks:
                        landmarks[landmark_key] = tuple(coord / scale_factor for coord in landmarks[landmark_key])
                
                # Calculate confidence score
                confidence = face_data.get('score', 0.99)
                
                detected_faces.append({
                    'bbox': bbox,
                    'landmarks': landmarks,
                    'confidence': confidence
                })
            
            logger.info(f"Detected {len(detected_faces)} face(s) in {image_path}")
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
