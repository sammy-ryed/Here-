"""
Face Recognition using ArcFace
Generates embeddings and matches faces
"""

import cv2
import numpy as np
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class FaceRecognizer:
    """Face recognition using ArcFace embeddings"""
    
    def __init__(self, model_name='ArcFace'):
        """
        Initialize face recognizer
        
        Args:
            model_name: Model to use for embeddings (ArcFace, Facenet, VGG-Face, etc.)
        """
        self.model_name = model_name
        self.ready = True
        logger.info(f"FaceRecognizer initialized with {model_name}")
    
    def is_ready(self):
        """Check if recognizer is ready"""
        return self.ready
    
    def get_embedding(self, image_path, face_data):
        """
        Extract embedding from a face
        
        Args:
            image_path: Path to the image
            face_data: Dictionary containing face bbox and landmarks
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to read image: {image_path}")
                return None
            
            # Extract face region
            bbox = face_data['bbox']
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Calculate face size
            face_width = x2 - x1
            face_height = y2 - y1
            
            # For small faces (from distant photos), add more margin
            if face_width < 100 or face_height < 100:
                margin = 30  # Larger margin for small faces
            else:
                margin = 20
            
            # Add margin
            height, width = img.shape[:2]
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(width, x2 + margin)
            y2 = min(height, y2 + margin)
            
            # Extract face
            face_img = img[y1:y2, x1:x2]
            
            if face_img.size == 0:
                logger.error("Empty face image after cropping")
                return None
            
            # For small faces, upscale them for better embedding quality
            face_h, face_w = face_img.shape[:2]
            if face_w < 112 or face_h < 112:  # ArcFace expects ~112x112
                # Upscale to at least 112x112
                scale = max(112 / face_w, 112 / face_h)
                new_w = int(face_w * scale * 1.5)  # Extra scaling for better quality
                new_h = int(face_h * scale * 1.5)
                face_img = cv2.resize(face_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                
                # Apply denoising for upscaled images
                face_img = cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)
                
                logger.info(f"Upscaled small face from {face_w}x{face_h} to {new_w}x{new_h}")
            
            # Save temporary face image
            temp_path = 'temp_face.jpg'
            cv2.imwrite(temp_path, face_img)
            
            # Get embedding using DeepFace
            embedding_obj = DeepFace.represent(
                img_path=temp_path,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend='skip'  # Skip detection as we already have the face
            )
            
            # Extract embedding vector
            if isinstance(embedding_obj, list) and len(embedding_obj) > 0:
                embedding = np.array(embedding_obj[0]['embedding'])
            else:
                embedding = np.array(embedding_obj['embedding'])
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            logger.info(f"Generated embedding with shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            return None
    
    def get_embedding_from_image(self, image_path):
        """
        Get embedding directly from image (without pre-detected face)
        
        Args:
            image_path: Path to the image
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            embedding_obj = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                enforce_detection=True,
                detector_backend='retinaface'
            )
            
            if isinstance(embedding_obj, list) and len(embedding_obj) > 0:
                embedding = np.array(embedding_obj[0]['embedding'])
            else:
                embedding = np.array(embedding_obj['embedding'])
            
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding from image: {str(e)}")
            return None
    
    def compare_embeddings(self, embedding1, embedding2):
        """
        Compare two embeddings using cosine similarity
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0 to 1, higher is more similar)
        """
        try:
            # Reshape for sklearn
            emb1 = embedding1.reshape(1, -1)
            emb2 = embedding2.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(emb1, emb2)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error comparing embeddings: {str(e)}")
            return 0.0
    
    def find_match(self, query_embedding, student_list, threshold=0.6):
        """
        Find matching student for a query embedding
        Checks both the primary embedding and all additional embeddings for each student
        
        Args:
            query_embedding: Embedding to match
            student_list: List of student dictionaries with embeddings
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (student_id, confidence) or None if no match
        """
        try:
            from db.database import Database
            db = Database()
            
            best_match = None
            best_similarity = threshold
            
            for student in student_list:
                student_id = student['id']
                student_name = student.get('name', 'Unknown')
                
                # Check primary embedding from students table
                if 'embedding' in student and student['embedding'] is not None:
                    student_embedding = np.frombuffer(student['embedding'], dtype=np.float32)
                    similarity = self.compare_embeddings(query_embedding, student_embedding)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = student_id
                        logger.debug(f"Match found (primary): {student_name} with similarity {similarity:.3f}")
                
                # Check additional embeddings from embeddings table
                additional_embeddings = db.get_student_embeddings(student_id)
                for emb_data in additional_embeddings:
                    emb = np.frombuffer(emb_data['embedding'], dtype=np.float32)
                    similarity = self.compare_embeddings(query_embedding, emb)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = student_id
                        logger.debug(f"Match found (additional): {student_name} with similarity {similarity:.3f}")
            
            if best_match:
                logger.info(f"Best match: Student ID {best_match} with confidence {best_similarity:.3f}")
                return (best_match, best_similarity)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding match: {str(e)}", exc_info=True)
            return None
    
    def batch_match(self, query_embeddings, student_list, threshold=0.6):
        """
        Match multiple embeddings at once
        
        Args:
            query_embeddings: List of embeddings to match
            student_list: List of student dictionaries
            threshold: Minimum similarity threshold
            
        Returns:
            List of matches
        """
        matches = []
        
        for idx, embedding in enumerate(query_embeddings):
            match = self.find_match(embedding, student_list, threshold)
            if match:
                matches.append({
                    'query_index': idx,
                    'student_id': match[0],
                    'confidence': match[1]
                })
        
        return matches
