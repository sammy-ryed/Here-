@echo off
REM Setup script for Face Recognition Attendance System
REM Run this script to set up the project

echo ================================================
echo Face Recognition Attendance System - Setup
echo ================================================
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Check Java installation
echo [2/5] Checking Java installation...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Java is not installed or not in PATH
    echo Please install Java 11+ from https://adoptium.net/
    pause
    exit /b 1
)
java -version
echo.

REM Check Maven installation
echo [3/5] Checking Maven installation...
mvn -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Maven is not installed or not in PATH
    echo Please install Maven from https://maven.apache.org/
    pause
    exit /b 1
)
mvn -version
echo.

REM Setup Python backend
echo [4/5] Setting up Python backend...
cd python_backend

echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo Creating environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file
)

echo Testing backend installation...
python test_installation.py
if %errorlevel% neq 0 (
    echo WARNING: Some backend tests failed
)

cd ..
echo.

REM Setup Java frontend
echo [5/5] Setting up Java frontend...
cd java_app

echo Building Java project...
call mvn clean install
if %errorlevel% neq 0 (
    echo ERROR: Failed to build Java project
    pause
    exit /b 1
)

cd ..
echo.

echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo To start the system:
echo.
echo 1. Start Python backend:
echo    cd python_backend
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 2. Start Java frontend (in new terminal):
echo    cd java_app
echo    mvn javafx:run
echo.
echo Or run: start_backend.bat and start_frontend.bat
echo.
pause
