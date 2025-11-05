#!/usr/bin/env python3
"""
Quick fix for embedding format issues in the database
Converts dict embeddings to proper numpy array bytes
"""

import sqlite3
import json
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def fix_student_embeddings():
    """Fix student embeddings that are stored as JSON dicts instead of numpy bytes"""
    
    db_path = 'db/attendance.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all students with embeddings
        cursor.execute("SELECT id, name, embedding FROM students WHERE embedding IS NOT NULL")
        students = cursor.fetchall()
        
        logger.info(f"Found {len(students)} students with embeddings to check")
        
        fixed_count = 0
        
        for student_id, name, embedding_data in students:
            try:
                # Try to parse as JSON (dict format)
                if isinstance(embedding_data, str):
                    embedding_dict = json.loads(embedding_data)
                    if isinstance(embedding_dict, dict) and 'embedding' in embedding_dict:
                        # Extract the actual embedding array
                        embedding_array = np.array(embedding_dict['embedding'], dtype=np.float32)
                        
                        # Convert to bytes
                        embedding_bytes = embedding_array.tobytes()
                        
                        # Update the database
                        cursor.execute(
                            "UPDATE students SET embedding = ? WHERE id = ?",
                            (embedding_bytes, student_id)
                        )
                        
                        logger.info(f"Fixed embedding for student {name} (ID: {student_id})")
                        fixed_count += 1
                    else:
                        logger.warning(f"Student {name} has unexpected embedding format")
                elif isinstance(embedding_data, bytes):
                    # Already in correct format
                    logger.info(f"Student {name} embedding already in correct format")
                else:
                    logger.warning(f"Student {name} has unknown embedding type: {type(embedding_data)}")
                    
            except Exception as e:
                logger.error(f"Error processing student {name}: {e}")
                continue
        
        # Also check additional embeddings table if it exists
        try:
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='embeddings'")
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT id, student_id, embedding FROM embeddings")
                additional_embeddings = cursor.fetchall()
                
                logger.info(f"Found {len(additional_embeddings)} additional embeddings to check")
                
                for emb_id, student_id, embedding_data in additional_embeddings:
                    try:
                        if isinstance(embedding_data, str):
                            embedding_dict = json.loads(embedding_data)
                            if isinstance(embedding_dict, dict) and 'embedding' in embedding_dict:
                                embedding_array = np.array(embedding_dict['embedding'], dtype=np.float32)
                                embedding_bytes = embedding_array.tobytes()
                                
                                cursor.execute(
                                    "UPDATE embeddings SET embedding = ? WHERE id = ?",
                                    (embedding_bytes, emb_id)
                                )
                                
                                logger.info(f"Fixed additional embedding {emb_id} for student {student_id}")
                                fixed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing additional embedding {emb_id}: {e}")
                        continue
        except Exception as e:
            logger.info("No additional embeddings table found or error accessing it")
        
        # Commit all changes
        conn.commit()
        logger.info(f"Successfully fixed {fixed_count} embeddings")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting embedding format fix...")
    fix_student_embeddings()
    logger.info("Embedding fix completed!")