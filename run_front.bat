@echo off
echo ============================================
echo Starting Frontend - Face Recognition App
echo ============================================
cd /d "%~dp0\java_app"
C:\maven\apache-maven-3.9.9\bin\mvn.cmd clean compile exec:java "-Dexec.mainClass=com.attendance.MainApp"
pause
