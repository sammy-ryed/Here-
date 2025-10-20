@echo off
REM Start Java Frontend Application

echo Starting Java Frontend...
echo.

REM Navigate to java_app folder
cd java_app

REM Check if pom.xml exists
if not exist pom.xml (
    echo ERROR: pom.xml not found!
    echo Make sure you're in the correct directory.
    cd ..
    if not exist java_app\pom.xml (
        echo ERROR: java_app directory not found!
        pause
        exit /b 1
    )
    cd java_app
)

REM Check backend connection
echo Checking backend connection...
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo WARNING: Backend server is not running!
    echo ========================================
    echo Please start the backend first:
    echo    start_backend.bat
    echo.
    echo Do you want to continue anyway? (Y/N)
    set /p continue=
    if /i not "%continue%"=="Y" exit /b 1
)

REM Check if target folder exists, if not build first
if not exist target (
    echo Building project for the first time...
    call mvn clean install -DskipTests
    if %errorlevel% neq 0 (
        echo Build failed. Please check Maven installation.
        pause
        exit /b 1
    )
)

REM Run JavaFX application
echo.
echo ========================================
echo Starting Face Recognition Attendance App
echo ========================================
echo.

call mvn javafx:run
