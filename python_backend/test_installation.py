"""
Test script to verify backend installation and functionality
Run this after installing dependencies
"""

import sys
import importlib

def test_imports():
    """Test if all required packages are installed"""
    print("Testing package imports...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'cv2',
        'numpy',
        'PIL',
        'retinaface',
        'deepface',
        'sklearn'
    ]
    
    failed = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT FOUND")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All packages installed successfully!")
        return True

def test_database():
    """Test database creation"""
    print("\nTesting database...")
    try:
        from db.database import Database
        db = Database('db/test_attendance.db')
        print("✓ Database initialized")
        
        # Test student creation
        test_embedding = [0.1] * 512
        import numpy as np
        student_id = db.add_student("Test Student", "TEST001", np.array(test_embedding))
        print(f"✓ Created test student (ID: {student_id})")
        
        # Test retrieval
        student = db.get_student_by_id(student_id)
        if student:
            print(f"✓ Retrieved student: {student['name']}")
        
        # Cleanup
        db.delete_student(student_id)
        print("✓ Database test completed")
        
        import os
        if os.path.exists('db/test_attendance.db'):
            os.remove('db/test_attendance.db')
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {str(e)}")
        return False

def test_face_detector():
    """Test face detector initialization"""
    print("\nTesting face detector...")
    try:
        from utils.face_detector import FaceDetector
        detector = FaceDetector()
        if detector.is_ready():
            print("✓ Face detector ready")
            return True
        else:
            print("✗ Face detector not ready")
            return False
    except Exception as e:
        print(f"✗ Face detector test failed: {str(e)}")
        return False

def test_face_recognizer():
    """Test face recognizer initialization"""
    print("\nTesting face recognizer...")
    try:
        from utils.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        if recognizer.is_ready():
            print("✓ Face recognizer ready")
            return True
        else:
            print("✗ Face recognizer not ready")
            return False
    except Exception as e:
        print(f"✗ Face recognizer test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Backend Installation Test")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Database", test_database),
        ("Face Detector", test_face_detector),
        ("Face Recognizer", test_face_recognizer)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with error: {str(e)}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Backend is ready to use.")
        print("Run 'python app.py' to start the server.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
