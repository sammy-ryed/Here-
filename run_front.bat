@echo off
echo ============================================
echo Starting Frontend - Next.js App
echo ============================================
echo Opening browser at http://localhost:3000
echo ============================================
cd /d "%~dp0\frontend"
npm run dev
pause
