@echo off
REM Start Python Backend Server

echo Starting Python Backend...
echo.

cd python_backend

REM Skip virtual environment - use system Python directly
REM if not exist venv (
REM     echo ERROR: Virtual environment not found!
REM     echo Creating virtual environment...
REM     python -m venv venv
REM     if %errorlevel% neq 0 (
REM         echo Failed to create virtual environment
REM         pause
REM         exit /b 1
REM     )
REM     
REM     echo Installing dependencies...
REM     call venv\Scripts\activate.bat
REM     python -m pip install --upgrade pip
REM     pip install -r requirements-minimal.txt
REM     if %errorlevel% neq 0 (
REM         echo Warning: Some packages may have failed to install
REM         echo Trying alternative installation...
REM         pip install Flask Flask-CORS deepface opencv-python Pillow numpy scikit-learn python-dotenv
REM     )
REM )

REM Direct start without venv
echo Starting Flask backend...
python app.py
