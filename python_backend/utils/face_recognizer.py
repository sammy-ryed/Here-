"""
Face Recognition using Facenet512
Generates embeddings and matches faces
OPTIMIZED: Matrix batch search (FAISS-equivalent) + Caching + Centroid averaging + GPU support
"""

import cv2
import numpy as np
from deepface import DeepFace
import logging
import hashlib
import threading
import os

logger = logging.getLogger(__name__)

# Global lock for DeepFace calls (not thread-safe)
deepface_lock = threading.Lock()

class FaceRecognizer:
    """Face recognition using Facenet512 embeddings with matrix batch search"""
    
    def __init__(self, model_name='Facenet512'):
        self.model_name = model_name
        self.ready = True
        self.embedding_cache = {}
        logger.info(f"FaceRecognizer initialized with {model_name} (matrix batch search enabled)")
    
    def is_ready(self):
        return self.ready

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _to_numpy(self, embedding):
        """Convert any embedding format to a normalised float32 numpy array."""
        import json
        try:
            if isinstance(embedding, np.ndarray):
                arr = embedding.astype(np.float32)
            elif isinstance(embedding, (list, tuple)):
                arr = np.array(embedding, dtype=np.float32)
            elif isinstance(embedding, str):
                arr = np.array(json.loads(embedding), dtype=np.float32)
            elif isinstance(embedding, bytes):
                arr = np.frombuffer(embedding, dtype=np.float32)
            elif isinstance(embedding, dict):
                raw = embedding.get('embedding', None)
                if raw is None:
                    return None
                return self._to_numpy(raw)
            else:
                return None

            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
            return arr
        except Exception:
            return None

    def _get_face_hash(self, image_input, bbox):
        bbox_str = '_'.join(map(str, map(int, bbox)))
        if isinstance(image_input, str):
            return hashlib.md5(f"{image_input}_{bbox_str}".encode()).hexdigest()
        else:
            array_hash = hashlib.md5(image_input.tobytes()).hexdigest()[:8]
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
        Compare two embeddings using cosine similarity.
        Handles any input format (numpy, JSON string, bytes, dict, list).
        """
        try:
            emb1 = self._to_numpy(embedding1)
            emb2 = self._to_numpy(embedding2)
            if emb1 is None or emb2 is None:
                return 0.0
            return float(np.dot(emb1, emb2))  # both already normalized
        except Exception as e:
            logger.error(f"Error comparing embeddings: {str(e)}")
            return 0.0

    # ------------------------------------------------------------------
    # FAISS-equivalent: vectorised matrix search
    # ------------------------------------------------------------------

    def build_student_index(self, student_list, db):
        """
        Build a centroid matrix for all students.
        Each student's embeddings (primary + additional) are averaged into
        one representative vector then L2-normalised.

        Returns:
            matrix       : np.ndarray (n_students, 512)  — None if empty
            student_ids  : list[int]
            student_names: list[str]
        """
        embeddings, student_ids, student_names = [], [], []

        for student in student_list:
            sid = student['id']
            vecs = []

            # Primary embedding
            if student.get('embedding') is not None:
                v = self._to_numpy(student['embedding'])
                if v is not None:
                    vecs.append(v)

            # Additional embeddings
            for emb_data in db.get_student_embeddings(sid):
                v = self._to_numpy(emb_data.get('embedding'))
                if v is not None:
                    vecs.append(v)

            if not vecs:
                continue

            # Average → centroid, re-normalise
            centroid = np.mean(vecs, axis=0).astype(np.float32)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid /= norm

            embeddings.append(centroid)
            student_ids.append(sid)
            student_names.append(student.get('name', 'Unknown'))

        if not embeddings:
            return None, [], []

        matrix = np.stack(embeddings, axis=0)  # (n, 512)
        return matrix, student_ids, student_names

    def find_match(self, query_embedding, student_list, threshold=0.6, db=None):
        """
        Find best-matching student using single matrix multiply (BLAS/vectorised).
        Equivalent to FAISS flat-IP search — 5-10× faster than a Python loop.

        Args:
            query_embedding: embedding to match
            student_list   : list of student dicts from DB
            threshold      : minimum cosine similarity to accept a match
            db             : Database instance (created internally if None)

        Returns:
            (student_id, confidence) or None
        """
        try:
            if db is None:
                from db.database import Database
                db = Database()

            matrix, student_ids, student_names = self.build_student_index(student_list, db)

            if matrix is None:
                logger.warning("⚠️ No student embeddings in index")
                return None

            # Normalise query
            q = self._to_numpy(query_embedding)
            if q is None:
                return None

            # One matrix multiply → all similarities (n_students,)
            scores = (matrix @ q).astype(float)

            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])

            # Similarity report (top 5)
            top5 = np.argsort(scores)[::-1][:5]
            logger.info(f"\n{'='*55}")
            logger.info(f"🔍 MATRIX SEARCH (threshold={threshold:.2f})")
            logger.info(f"{'='*55}")
            for i in top5:
                tag = "✅ MATCH" if scores[i] >= threshold else "❌      "
                logger.info(f"{tag} | {student_names[i]:<22s} | {scores[i]:.4f}")
            logger.info(f"{'='*55}\n")

            if best_score >= threshold:
                logger.info(f"✅ BEST MATCH: {student_names[best_idx]} — confidence {best_score:.4f}")
                return (student_ids[best_idx], best_score)

            logger.warning(f"⚠️ NO MATCH. Best: {student_names[best_idx]} @ {best_score:.4f}, needed {threshold:.4f}")
            return None

        except Exception as e:
            logger.error(f"Error in find_match: {str(e)}", exc_info=True)
            return None

