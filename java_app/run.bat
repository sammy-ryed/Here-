@echo off
cd /d "%~dp0"
echo Starting Face Recognition Attendance System...
mvn clean compile exec:java -Dexec.mainClass=com.attendance.MainApp
pause