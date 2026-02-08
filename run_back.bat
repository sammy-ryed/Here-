@echo off
echo ============================================
echo Starting Backend - Python Flask Server
echo ============================================
echo Backend URL: http://localhost:5000
echo Health check: http://localhost:5000/health
echo ============================================
cd /d "%~dp0\python_backend"
py -3.11 app.py
pause
