# 🚨 TROUBLESHOOTING GUIDE

## Issues You Encountered and Solutions

### ❌ Issue 1: RetinaFace Version Not Found
**Error**: `ERROR: Could not find a version that satisfies the requirement retinaface==0.0.14`

**Solution**: 
- Updated to use `retina-face==0.0.17` (note the dash)
- Also provided `requirements-minimal.txt` with only essential packages

### ❌ Issue 2: Wrong Directory for Maven
**Error**: `Cannot find path 'D:\herept2\python_backend\java_app'`

**Solution**:
- You need to navigate to `d:\herept2\java_app` (not from python_backend)
- Updated `start_frontend.bat` to handle directory navigation

### ❌ Issue 3: Flask Not Installed
**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
- Installation failed due to package version conflicts
- Use the new `quick_fix.bat` script to reinstall properly

---

## 🔧 Quick Fix Steps

### **Option 1: Run the Quick Fix Script (Recommended)**

```powershell
cd d:\herept2
.\quick_fix.bat
```

This will:
1. ✅ Remove old virtual environment
2. ✅ Create fresh Python environment
3. ✅ Install minimal working dependencies
4. ✅ Build Java project
5. ✅ Test installations

### **Option 2: Manual Fix**

#### Fix Python Backend:

```powershell
cd d:\herept2\python_backend

# Remove old venv
Remove-Item -Recurse -Force venv

# Create new venv
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install packages one by one
pip install Flask==3.0.0 Flask-CORS==4.0.0
pip install deepface==0.0.92
pip install opencv-python==4.8.1.78
pip install Pillow==10.1.0
pip install numpy==1.24.3
pip install scikit-learn==1.3.2
pip install python-dotenv==1.0.0
```

#### Fix Java Frontend:

```powershell
cd d:\herept2\java_app
mvn clean install -DskipTests
```

---

## ✅ Correct Startup Procedure

### Step 1: Start Backend

```powershell
# Open PowerShell Terminal 1
cd d:\herept2
.\start_backend.bat

# Wait for: "Running on http://0.0.0.0:5000"
```

### Step 2: Start Frontend (New Terminal)

```powershell
# Open PowerShell Terminal 2
cd d:\herept2
.\start_frontend.bat

# Wait for JavaFX window to appear
```

---

## 🐛 Common Errors and Fixes

### Error: "No module named 'flask'"
**Fix**: Virtual environment not activated or packages not installed
```powershell
cd python_backend
.\venv\Scripts\Activate.ps1
pip install Flask Flask-CORS
```

### Error: "No plugin found for prefix 'javafx'"
**Fix**: Not in correct directory or POM.xml missing
```powershell
cd d:\herept2\java_app  # Make sure you're here!
mvn clean install
```

### Error: "tensorflow" installation fails
**Fix**: Use minimal requirements
```powershell
pip install -r requirements-minimal.txt
```

### Error: Camera not working
**Fix**: OpenCV native libs missing
```powershell
pip uninstall opencv-python
pip install opencv-python==4.8.1.78
```

---

## 📦 Package Version Reference

### Working Versions (Tested):

| Package | Version | Notes |
|---------|---------|-------|
| Flask | 3.0.0 | Latest stable |
| deepface | 0.0.92 | Includes face detection |
| opencv-python | 4.8.1.78 | Stable version |
| numpy | 1.24.3 | Compatible with TensorFlow |
| scikit-learn | 1.3.2 | Latest compatible |
| tensorflow | Auto-installed by deepface | CPU version |

---

## 🧪 Test Your Installation

### Test Backend:

```powershell
cd python_backend
.\venv\Scripts\Activate.ps1
python test_installation.py
```

Expected output:
```
✓ flask
✓ cv2
✓ numpy
✓ deepface
✅ All packages installed successfully!
```

### Test Frontend:

```powershell
cd java_app
mvn clean test
```

### Test Backend API:

```powershell
# Start backend first, then in new terminal:
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {...}
}
```

---

## 🎯 Simplified Installation (Start Fresh)

If everything is broken, start from scratch:

```powershell
# 1. Navigate to project
cd d:\herept2

# 2. Run quick fix
.\quick_fix.bat

# 3. Start backend
.\start_backend.bat

# 4. In new terminal, start frontend
.\start_frontend.bat
```

---

## 💡 Understanding the Error Messages

### "Could not find a version"
- Package name or version doesn't exist on PyPI
- Check package name spelling (e.g., `retina-face` vs `retinaface`)

### "No module named X"
- Package not installed in current environment
- Virtual environment not activated
- Wrong Python interpreter being used

### "No plugin found for prefix 'javafx'"
- Not in correct directory (need to be in `java_app/`)
- POM.xml missing or corrupted
- Maven not finding plugin definition

---

## 🆘 Still Having Issues?

### Check Prerequisites:

```powershell
# Python version (should be 3.8+)
python --version

# Java version (should be 11+)
java -version

# Maven version (should be 3.6+)
mvn -version

# Pip version
pip --version
```

### Clean Everything:

```powershell
cd d:\herept2

# Remove Python environment
Remove-Item -Recurse -Force python_backend\venv

# Remove Maven build
Remove-Item -Recurse -Force java_app\target

# Run quick fix
.\quick_fix.bat
```

---

## 📞 Final Resort

If nothing works, try this minimal setup:

```powershell
# Install only core packages
cd python_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install Flask flask-cors opencv-python pillow numpy

# Create minimal app.py for testing
# Then add packages one by one
```

---

**Remember**: 
- ✅ Always activate virtual environment: `.\venv\Scripts\Activate.ps1`
- ✅ Use correct directory: `java_app` for Maven, `python_backend` for Python
- ✅ Start backend BEFORE frontend
- ✅ Check logs for specific error messages

---

*Updated: October 18, 2025*
*Status: Issues Identified and Fixed*
