"""
Clear all data from SQLite database tables
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'db', 'attendance.db')

def clear_all_tables():
    """Clear all data from all tables in the database"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Connected to database: {db_path}")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n" + "=" * 60)
        print("CLEARING ALL DATA...")
        print("=" * 60)
        
        # Clear each table
        for table in tables:
            table_name = table[0]
            
            # Count records before deletion
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count_before = cursor.fetchone()[0]
            
            # Delete all records
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Reset autoincrement counter
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
            
            print(f"✓ Cleared {count_before} records from '{table_name}'")
        
        # Commit changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print("VERIFICATION - Records after clearing:")
        print("=" * 60)
        
        # Verify all tables are empty
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count_after = cursor.fetchone()[0]
            print(f"  {table_name}: {count_after} records")
        
        print("\n" + "=" * 60)
        print("✓ ALL DATA CLEARED SUCCESSFULLY!")
        print("=" * 60)
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CLEAR ALL DATABASE TABLES")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete ALL data from ALL tables!")
    print("   - All registered students")
    print("   - All face embeddings")
    print("   - All attendance records")
    print("\nThis action CANNOT be undone!")
    print("=" * 60)
    
    # Ask for confirmation
    confirmation = input("\nType 'YES' to confirm deletion: ").strip()
    
    if confirmation == "YES":
        print("\nProceeding with data deletion...\n")
        success = clear_all_tables()
        
        if success:
            print("\n✓ Database cleared successfully!")
            print("  You can now register new students from scratch.")
        else:
            print("\n❌ Failed to clear database. Check the errors above.")
    else:
        print("\n❌ Operation cancelled. No data was deleted.")
        print("  (You must type 'YES' exactly to confirm)")
