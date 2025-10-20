"""
Quick script to check database connection and contents
"""

import sqlite3
import sys
import os

def check_database():
    db_path = 'db/attendance.db'
    
    print("=" * 60)
    print("DATABASE CONNECTION CHECK")
    print("=" * 60)
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file NOT found at: {os.path.abspath(db_path)}")
        return
    
    print(f"✅ Database file found at: {os.path.abspath(db_path)}")
    print(f"   File size: {os.path.getsize(db_path)} bytes")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print("✅ Database connection: SUCCESS")
        print()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table}")
        print()
        
        # Check students table
        if 'students' in tables:
            cursor.execute("SELECT COUNT(*) FROM students")
            count = cursor.fetchone()[0]
            print(f"👥 Total Students: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, name, roll_no, created_at FROM students")
                students = cursor.fetchall()
                print("\nRegistered Students:")
                print("-" * 60)
                for student in students:
                    print(f"   ID: {student['id']}")
                    print(f"   Name: {student['name']}")
                    print(f"   Roll No: {student['roll_no']}")
                    print(f"   Created: {student['created_at']}")
                    print("-" * 60)
            else:
                print("   ℹ️  No students registered yet")
        
        print()
        
        # Check embeddings table
        if 'embeddings' in tables:
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            count = cursor.fetchone()[0]
            print(f"🔢 Total Embeddings: {count}")
        
        # Check attendance table
        if 'attendance' in tables:
            cursor.execute("SELECT COUNT(*) FROM attendance")
            count = cursor.fetchone()[0]
            print(f"📅 Total Attendance Records: {count}")
            
            if count > 0:
                cursor.execute("""
                    SELECT s.name, s.roll_no, a.date, a.status 
                    FROM attendance a 
                    JOIN students s ON a.student_id = s.id 
                    ORDER BY a.date DESC 
                    LIMIT 5
                """)
                records = cursor.fetchall()
                print("\nRecent Attendance (Last 5):")
                print("-" * 60)
                for record in records:
                    print(f"   {record['name']} ({record['roll_no']}) - {record['date']} - {record['status']}")
        
        print()
        print("=" * 60)
        print("✅ DATABASE CHECK COMPLETE")
        print("=" * 60)
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_database()
