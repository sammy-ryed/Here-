@echo off
echo ================================================
echo Starting Java Frontend Application
echo ================================================
echo.
echo IMPORTANT: Make sure backend is running first!
echo Backend should be at: http://localhost:5000
echo.

cd /d "%~dp0java_app"

REM Check if we're in the right directory
if not exist pom.xml (
    echo ERROR: pom.xml not found!
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if already built
if not exist target\face-recognition-attendance-1.0.0.jar (
    echo Building project...
    call mvn clean install -DskipTests
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Build failed!
        pause
        exit /b 1
    )
)

echo.
echo Starting JavaFX application...
echo.

REM Run the application
call mvn javafx:run

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start!
    echo.
    echo Troubleshooting:
    echo 1. Check if Java is installed: java -version
    echo 2. Check if backend is running at http://localhost:5000
    echo 3. Check logs above for errors
    echo.
    pause
)
