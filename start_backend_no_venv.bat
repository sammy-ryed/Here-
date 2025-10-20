@echo off
echo ================================================
echo Starting Flask Backend (Without Virtual Environment)
echo ================================================
echo.

cd /d "%~dp0python_backend"

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
)

echo Starting Flask server on port 5000...
echo.
echo Backend will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Start Flask directly (packages installed globally)
py -3.13 app.py

pause
