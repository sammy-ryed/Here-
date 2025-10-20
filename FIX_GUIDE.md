# ⚡ STEP-BY-STEP FIX GUIDE

## 🎯 Follow These Steps Exactly

### Step 1: Close Current Terminal
```powershell
# Close your current PowerShell and open a fresh one
```

### Step 2: Navigate to Project
```powershell
cd d:\herept2
```

### Step 3: Run Quick Fix Script
```powershell
.\quick_fix.bat
```

**This will take 5-10 minutes and will:**
- ✅ Clean old Python environment
- ✅ Install working package versions
- ✅ Build Java project
- ✅ Test everything

### Step 4: Start Backend (Terminal 1)
```powershell
# In your current terminal
cd d:\herept2
.\start_backend.bat
```

**Wait for this message:**
```
========================================
Backend starting on http://localhost:5000
Press Ctrl+C to stop
========================================
```

### Step 5: Start Frontend (Terminal 2)
```powershell
# Open NEW PowerShell terminal
cd d:\herept2
.\start_frontend.bat
```

**Wait for JavaFX application window to open**

---

## 🎉 Success Indicators

### Backend Running Successfully:
```
* Running on http://0.0.0.0:5000
* Debug mode: on
WARNING: This is a development server
```

### Frontend Running Successfully:
- JavaFX window appears
- No error dialogs
- Tabs are visible (Dashboard, Register, Attendance, Reports)

---

## ⚠️ If Quick Fix Fails

### Alternative: Manual Installation

```powershell
# 1. Clean Python environment
cd d:\herept2\python_backend
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install pip packages
python -m pip install --upgrade pip
pip install Flask==3.0.0
pip install Flask-CORS==4.0.0
pip install opencv-python==4.8.1.78
pip install Pillow==10.1.0
pip install numpy==1.24.3
pip install scikit-learn==1.3.2
pip install python-dotenv==1.0.0
pip install deepface==0.0.92

# 3. Copy env file
copy .env.example .env

# 4. Build Java
cd ..\java_app
mvn clean install -DskipTests
```

---

## 🧪 Test Installation

### Test Backend:
```powershell
cd d:\herept2\python_backend
.\venv\Scripts\Activate.ps1
python -c "import flask; print('Flask OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "import numpy; print('NumPy OK')"
```

All should print "OK" without errors.

### Test Java:
```powershell
cd d:\herept2\java_app
mvn -version
```

Should show Maven version without errors.

---

## 📝 Commands Summary

```powershell
# Quick Fix (Recommended)
cd d:\herept2
.\quick_fix.bat

# Start Backend
.\start_backend.bat

# Start Frontend (new terminal)
.\start_frontend.bat
```

---

## 🔍 Verify Directories

Make sure you have these folders:
```
d:\herept2\
  ├── python_backend\
  │   ├── app.py
  │   ├── requirements.txt
  │   └── venv\ (will be created)
  └── java_app\
      ├── pom.xml
      └── src\
```

---

## ✅ Ready to Use!

Once both terminals show running status:

1. **Register a student:**
   - Click "Register Student" tab
   - Enter name and roll number
   - Upload 3-5 photos
   - Click "Register"

2. **Take attendance:**
   - Click "Take Attendance" tab
   - Upload group photo
   - Click "Process Attendance"
   - Review results

---

**Need Help?** Check `TROUBLESHOOTING.md` for detailed error solutions.
