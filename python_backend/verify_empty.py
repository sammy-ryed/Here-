"""
Quick verification that database is empty
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'db', 'attendance.db')

print("\n" + "=" * 60)
print("DATABASE STATUS CHECK")
print("=" * 60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n✓ Connected to: {db_path}\n")
    
    # Check each table
    tables = ['students', 'embeddings', 'attendance']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        status = "✓ EMPTY" if count == 0 else f"⚠ {count} records"
        print(f"  {table:20s}: {status}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ Database is ready for use!")
    print("=" * 60 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}\n")
