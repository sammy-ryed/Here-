@echo off
REM Quick Fix Script for Common Issues

echo ================================================
echo Face Recognition Attendance System - Quick Fix
echo ================================================
echo.

REM Fix 1: Clean and reinstall Python dependencies
echo [1/3] Fixing Python Backend...
cd python_backend

if exist venv (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

echo Creating fresh virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python 3.13 compatible dependencies...
pip install Flask==3.0.0 Flask-CORS==4.0.0
pip install numpy==1.26.4
pip install Pillow==11.0.0
pip install opencv-python==4.10.0.84
pip install scikit-learn==1.5.2
pip install deepface==0.0.92
pip install python-dotenv==1.0.0

echo.
echo Python dependencies installed!
echo.

REM Fix 2: Build Java project
cd ..
echo [2/3] Building Java Frontend...
cd java_app

if not exist pom.xml (
    echo ERROR: java_app/pom.xml not found!
    cd ..
    pause
    exit /b 1
)

echo Running Maven build...
call mvn clean install -DskipTests
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Maven build had issues
    echo Make sure Java and Maven are installed correctly
    echo.
)

cd ..
echo.

REM Fix 3: Test backend
echo [3/3] Testing Backend Installation...
cd python_backend
call venv\Scripts\activate.bat

echo.
echo Testing imports...
python -c "import flask; print('✓ Flask installed')"
python -c "import cv2; print('✓ OpenCV installed')"
python -c "import numpy; print('✓ NumPy installed')"
python -c "try: from deepface import DeepFace; print('✓ DeepFace installed'); except: print('✗ DeepFace not installed')"

cd ..
echo.
echo ================================================
echo Quick Fix Complete!
echo ================================================
echo.
echo To start the system:
echo 1. Run: start_backend.bat
echo 2. Run: start_frontend.bat (in new terminal)
echo.
pause
