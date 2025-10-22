"""
Database management for student records and attendance
Using SQLite for simplicity (can be switched to MySQL)
"""

import sqlite3
import numpy as np
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    """Database handler for attendance system"""
    
    def __init__(self, db_path='db/attendance.db'):
        """Initialize database connection"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
        logger.info(f"Database initialized at {db_path}")
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def is_connected(self):
        """Check database connection"""
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def init_database(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT UNIQUE NOT NULL,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Embeddings table (multiple embeddings per student)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        ''')
        
        # Attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, date)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_roll_no ON students(roll_no)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_id ON embeddings(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')
        
        conn.commit()
        conn.close()
        logger.info("Database tables created/verified")
    
    def add_student(self, name, roll_no, embedding):
        """
        Add a new student to the database
        
        Args:
            name: Student name
            roll_no: Student roll number
            embedding: Face embedding as numpy array
            
        Returns:
            Student ID
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert embedding to binary
            embedding_blob = embedding.astype(np.float32).tobytes()
            
            cursor.execute(
                'INSERT INTO students (name, roll_no, embedding) VALUES (?, ?, ?)',
                (name, roll_no, embedding_blob)
            )
            
            student_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Added student: {name} (ID: {student_id})")
            return student_id
            
        except sqlite3.IntegrityError:
            logger.error(f"Student with roll number {roll_no} already exists")
            raise ValueError(f"Student with roll number {roll_no} already exists")
        except Exception as e:
            logger.error(f"Error adding student: {str(e)}")
            raise
    
    def add_embedding(self, student_id, embedding):
        """
        Add an additional embedding for a student
        
        Args:
            student_id: Student ID
            embedding: Face embedding as numpy array
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            embedding_blob = embedding.astype(np.float32).tobytes()
            
            cursor.execute(
                'INSERT INTO embeddings (student_id, embedding) VALUES (?, ?)',
                (student_id, embedding_blob)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding embedding: {str(e)}")
            raise
    
    def get_student_embeddings(self, student_id):
        """
        Get all additional embeddings for a student
        
        Args:
            student_id: Student ID
            
        Returns:
            List of embedding dictionaries
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM embeddings WHERE student_id = ?', (student_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting student embeddings: {str(e)}")
            return []
    
    def get_student_by_id(self, student_id):
        """Get student information by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting student: {str(e)}")
            return None
    
    def get_student_by_roll_no(self, roll_no):
        """Get student information by roll number"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM students WHERE roll_no = ?', (roll_no,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting student: {str(e)}")
            return None
    
    def get_all_students(self):
        """Get all registered students"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM students ORDER BY name')
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting all students: {str(e)}")
            return []
    
    def mark_attendance(self, student_id, date, status):
        """
        Mark attendance for a student
        
        Args:
            student_id: Student ID
            date: Date in YYYY-MM-DD format
            status: 'present' or 'absent'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO attendance (student_id, date, status)
                VALUES (?, ?, ?)
            ''', (student_id, date, status))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Marked student {student_id} as {status} on {date}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking attendance: {str(e)}")
            return False
    
    def get_attendance_by_date(self, date):
        """Get attendance records for a specific date"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.id, s.name, s.roll_no, a.status, a.timestamp
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
                ORDER BY s.name
            ''', (date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting attendance: {str(e)}")
            return []
    
    def get_attendance_report(self, start_date, end_date):
        """
        Get attendance report for a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of attendance records
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    s.id,
                    s.name,
                    s.roll_no,
                    a.date,
                    a.status,
                    a.timestamp
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN ? AND ?
                ORDER BY a.date DESC, s.name
            ''', (start_date, end_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting attendance report: {str(e)}")
            return []
    
    def delete_student(self, student_id):
        """Delete a student and all related records"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
            rows_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if rows_deleted > 0:
                logger.info(f"Deleted student ID {student_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting student: {str(e)}")
            raise
    
    def clear_all_students(self):
        """Delete ALL students and their embeddings - DESTRUCTIVE!"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete all students (embeddings and attendance will cascade delete due to foreign keys)
            cursor.execute('DELETE FROM students')
            students_deleted = cursor.rowcount
            
            # Delete all embeddings explicitly
            cursor.execute('DELETE FROM embeddings')
            embeddings_deleted = cursor.rowcount
            
            # Delete all attendance records
            cursor.execute('DELETE FROM attendance')
            attendance_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.warning(f"⚠️ CLEARED ALL DATA: {students_deleted} students, {embeddings_deleted} embeddings, {attendance_deleted} attendance records")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all students: {str(e)}")
            raise
    
    def get_student_statistics(self, student_id):
        """Get attendance statistics for a student"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_days,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_days
                FROM attendance
                WHERE student_id = ?
            ''', (student_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                result = dict(row)
                if result['total_days'] > 0:
                    result['attendance_percentage'] = (result['present_days'] / result['total_days']) * 100
                else:
                    result['attendance_percentage'] = 0.0
                return result
            
            return {
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'attendance_percentage': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting student statistics: {str(e)}")
            return None
    
    def clear_attendance_by_date(self, date):
        """
        Clear all attendance records for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM attendance WHERE date = ?', (date,))
            rows_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted {rows_deleted} attendance records for {date}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing attendance for {date}: {str(e)}")
            return False
