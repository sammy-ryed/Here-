# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Python Dependencies

```powershell
cd python_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Start Python Backend

```powershell
python app.py
```

You should see: `Running on http://0.0.0.0:5000`

### Step 3: Run Java Frontend

Open new PowerShell window:

```powershell
cd java_app
mvn javafx:run
```

Or open `java_app` folder in IntelliJ IDEA and run `MainApp.java`

### Step 4: Register Your First Student

1. In the app, click **"Register Student"** tab
2. Enter name: "John Doe"
3. Enter roll no: "001"
4. Click **"Upload Photo"** and select 3-5 clear face photos
5. Click **"Register"**

### Step 5: Take Attendance

1. Click **"Take Attendance"** tab
2. Upload a group photo containing registered students
3. Click **"Process Attendance"**
4. Review recognized students
5. Click **"Confirm Attendance"**

That's it! 🎉

---

## ⚡ Quick Commands Reference

### Python Backend

```powershell
# Start server
python app.py

# Test API health
curl http://localhost:5000/health

# View all students
curl http://localhost:5000/students
```

### Java Frontend

```powershell
# Build project
mvn clean install

# Run application
mvn javafx:run

# Create executable JAR
mvn clean package
```

---

## 🔧 Common Configuration Changes

### Change Backend Port

Edit `python_backend/.env`:
```ini
PORT=8080
```

Edit `java_app/src/main/resources/config.properties`:
```properties
api.base.url=http://localhost:8080
```

### Change Face Recognition Confidence

Edit `python_backend/.env`:
```ini
CONFIDENCE_THRESHOLD=0.5  # Lower = more lenient (0.4-0.7 recommended)
```

### Use Different Camera

Edit `java_app/src/main/resources/config.properties`:
```properties
camera.device.index=1  # Try 0, 1, 2 for different cameras
```

---

## 📸 Tips for Best Results

### For Registration:
- ✅ Use 5+ photos per student
- ✅ Different expressions (neutral, smiling)
- ✅ Slight angle variations (front, slight left/right)
- ✅ Good, consistent lighting
- ❌ No sunglasses or face masks
- ❌ Avoid very dark or overexposed images

### For Attendance:
- ✅ Capture from slightly elevated angle
- ✅ Ensure all faces are visible
- ✅ Adequate lighting (no harsh shadows)
- ✅ Take multiple photos if first attempt has issues
- ❌ Avoid extreme angles
- ❌ Don't use very low resolution images

---

## 🐛 Quick Troubleshooting

**Backend won't start?**
```powershell
pip install --upgrade pip setuptools
pip install -r requirements.txt --force-reinstall
```

**Java app shows errors?**
```powershell
mvn clean install -U
```

**Camera not working?**
- Check if another app is using the camera
- Try different camera index (0, 1, 2)
- Grant camera permissions if on Windows 10/11

**Low recognition accuracy?**
- Add more training photos
- Improve lighting conditions
- Lower confidence threshold

---

## 📊 Test with Sample Data

You can test the system without a camera by using sample images:

1. Download sample face images from the internet
2. Register 3-4 "students" with different photos
3. Create a "classroom" photo with multiple people
4. Test the attendance processing

---

Need more help? Check the full README.md!
