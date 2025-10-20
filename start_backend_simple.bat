@echo off
echo ================================================
echo Starting Python Backend Server  
echo ================================================
echo.

cd /d "%~dp0python_backend"

REM Check if .env exists, create from template if not
if not exist .env (
    echo Creating .env configuration file...
    copy .env.example .env
)

REM Create uploads directory if it doesn't exist
if not exist uploads mkdir uploads

echo Starting Flask server...
echo Backend URL: http://localhost:5000
echo Health check: http://localhost:5000/health
echo.
echo Press Ctrl+C to stop the server
echo ================================================
echo.

REM Start Flask using py launcher (bypasses venv issues)
py -3.13 app.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Flask server failed to start!
    echo.
    echo Troubleshooting:
    echo 1. Check if port 5000 is already in use
    echo 2. Verify all packages are installed: py -3.13 -m pip list
    echo 3. Test imports: py -3.13 -c "import flask, deepface, cv2"
    echo.
    pause
)
