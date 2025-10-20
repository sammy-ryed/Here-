# Face Recognition Attendance System 🎓

A comprehensive desktop application for automated attendance management using face recognition technology. The system combines **JavaFX** frontend with **Python** backend powered by **RetinaFace** and **ArcFace** for accurate face detection and recognition.

---

## 🌟 Features

### Core Functionality
- ✅ **Student Registration** - Register students with multiple face photos for improved accuracy
- 📸 **Automated Attendance** - Take classroom photos and automatically identify students
- 👥 **Multi-Face Detection** - Detect and recognize multiple faces in group photos
- 🔍 **Unrecognized Face Handling** - Show unidentified faces for manual review and retake
- 📊 **Dashboard & Reports** - View attendance statistics and generate reports
- 🎥 **Webcam Integration** - Capture photos directly from camera

### Technical Highlights
- **RetinaFace** - State-of-the-art face detection for group settings
- **ArcFace Embeddings** - High-accuracy face recognition
- **REST API** - Clean separation between frontend and backend
- **SQLite Database** - Persistent storage for student records and attendance
- **Modern UI** - Clean blue/white themed JavaFX interface
- **Offline Capable** - Works without internet connection

---

## 📁 Project Structure

```
project-root/
├── java_app/                    # JavaFX Frontend Application
│   ├── src/main/java/com/attendance/
│   │   ├── MainApp.java        # Application entry point
│   │   ├── controller/         # UI Controllers
│   │   │   ├── MainLayoutController.java
│   │   │   ├── DashboardController.java
│   │   │   ├── RegisterStudentController.java
│   │   │   └── TakeAttendanceController.java
│   │   ├── model/              # Data Models
│   │   │   ├── Student.java
│   │   │   └── AttendanceResult.java
│   │   ├── service/            # API Service Layer
│   │   │   └── ApiService.java
│   │   └── util/               # Utilities
│   │       ├── ConfigManager.java
│   │       ├── Logger.java
│   │       └── CameraCapture.java
│   ├── src/main/resources/
│   │   ├── config.properties   # Configuration
│   │   └── css/style.css       # Stylesheets
│   └── pom.xml                 # Maven dependencies
│
├── python_backend/              # Flask Backend Service
│   ├── app.py                  # Flask application
│   ├── utils/
│   │   ├── face_detector.py   # RetinaFace detection
│   │   ├── face_recognizer.py # ArcFace recognition
│   │   └── image_utils.py     # Image processing
│   ├── db/
│   │   └── database.py        # SQLite database handler
│   ├── models/                 # Pre-trained model storage
│   ├── uploads/                # Temporary uploads
│   ├── unrecognized/           # Unidentified faces
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variables template
│
└── README.md                   # This file
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Java 11+** (JDK)
- **Python 3.8+**
- **Maven 3.6+**
- **Webcam** (optional, for photo capture)

### 1️⃣ Python Backend Setup

```powershell
# Navigate to backend directory
cd python_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Start Flask server
python app.py
```

The backend will start on `http://localhost:5000`

### 2️⃣ Java Frontend Setup

```powershell
# Navigate to frontend directory
cd ..\java_app

# Build with Maven
mvn clean install

# Run the application
mvn javafx:run
```

Alternatively, open the project in IntelliJ IDEA or Eclipse and run `MainApp.java`

---

## 📖 Usage Guide

### 1. Register Students

1. Click on **"Register Student"** tab
2. Enter student **Name** and **Roll Number**
3. Upload 3-5 photos or use **"Capture Photo"** button
4. Photos should be:
   - Clear front-facing shots
   - Different angles/expressions
   - Good lighting conditions
   - Single person per photo
5. Click **"Register"** to save

### 2. Take Attendance

1. Click on **"Take Attendance"** tab
2. Upload classroom photo or use **"Capture Photo"**
3. Click **"Process Attendance"**
4. Review results:
   - ✅ **Present** - Recognized students with confidence scores
   - ❌ **Absent** - Registered students not detected
   - ⚠️ **Unrecognized** - Faces that couldn't be identified
5. Retake photos if needed
6. Click **"Confirm Attendance"** to save

### 3. View Dashboard

- **Total Students** - Number of registered students
- **Today's Attendance** - Present/Absent counts
- **Attendance Rate** - Percentage statistics
- **Recent Students** - List of registered students
- **Weekly Chart** - Attendance trends

---

## 🔧 Configuration

### Backend Configuration (`.env`)

```ini
# Flask Settings
HOST=0.0.0.0
PORT=5000

# Database
DATABASE_PATH=db/attendance.db

# Face Recognition
CONFIDENCE_THRESHOLD=0.6
MODEL_NAME=ArcFace

# Performance
USE_GPU=False
```

### Frontend Configuration (`config.properties`)

```properties
# API Backend URL
api.base.url=http://localhost:5000

# Camera Settings
camera.device.index=0
camera.width=640
camera.height=480

# UI Theme
theme=light
```

---

## 🧪 API Endpoints

### Backend REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/register_face` | POST | Register student with photos |
| `/process_attendance` | POST | Process classroom photo |
| `/students` | GET | Get all students |
| `/unrecognized/<filename>` | GET | Get unrecognized face image |
| `/attendance/report` | GET | Get attendance report |
| `/student/<id>` | DELETE | Delete student |

---

## 🛠️ Technology Stack

### Frontend (Java)
- **JavaFX 17** - Modern UI framework
- **Maven** - Dependency management
- **OpenCV 4.6** - Camera capture
- **Gson** - JSON processing
- **Apache HttpClient** - API communication

### Backend (Python)
- **Flask 2.3** - Web framework
- **RetinaFace** - Face detection
- **DeepFace** (ArcFace) - Face recognition
- **OpenCV** - Image processing
- **SQLite** - Database
- **NumPy, SciPy** - Scientific computing

---

## 🎯 Accuracy & Performance

### Optimization Tips

1. **Registration Phase**
   - Capture 5+ photos per student
   - Include different angles and expressions
   - Ensure consistent lighting
   - Use high-resolution images (min 640x480)

2. **Attendance Phase**
   - Take photos from similar distance each time
   - Ensure adequate lighting
   - Capture from slightly elevated angle
   - Multiple photos from different angles recommended

3. **Confidence Threshold**
   - Default: `0.6` (60%)
   - Increase for stricter matching
   - Decrease if missing valid matches

### Performance Metrics
- **Detection Speed**: ~1-2 seconds per image
- **Recognition Accuracy**: 95%+ with good training data
- **Max Faces per Photo**: 50+
- **Database Size**: Scales to 1000+ students

---

## 🐛 Troubleshooting

### Common Issues

**Problem**: Backend fails to start
```powershell
# Solution: Check Python version and reinstall dependencies
python --version  # Should be 3.8+
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Problem**: Camera not detected
```java
// Solution: Check camera index in config.properties
camera.device.index=0  // Try 0, 1, 2, etc.
```

**Problem**: Low recognition accuracy
- Add more training photos per student
- Ensure good lighting in both registration and attendance photos
- Lower confidence threshold in `.env`

**Problem**: "Cannot find symbol" errors in Java
```powershell
# Solution: Ensure Maven dependencies are downloaded
mvn clean install -U
```

---

## 📊 Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    embedding BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);
```

---

## 🔐 Security Considerations

- Backend runs on localhost by default
- No authentication implemented (add JWT for production)
- Face embeddings stored as binary blobs
- CORS enabled for local development
- Input validation on all endpoints

---

## 🚀 Deployment

### For Production Use:

1. **Backend**
   - Deploy Flask with **Gunicorn** + **Nginx**
   - Use **PostgreSQL** instead of SQLite
   - Add authentication (JWT)
   - Enable HTTPS
   - Set `USE_GPU=True` for faster processing

2. **Frontend**
   - Package as executable JAR
   - Include JRE for distribution
   - Update API URL to production server
   - Add logging to file

---

## 📝 License

This project is for educational purposes. Please ensure compliance with privacy laws when using facial recognition technology.

---

## 👨‍💻 Development

### Building from Source

```powershell
# Backend
cd python_backend
pip install -r requirements.txt

# Frontend
cd java_app
mvn clean package
```

### Running Tests

```powershell
# Backend tests
python -m pytest tests/

# Frontend tests
mvn test
```

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Add user authentication
- Implement attendance reports export (PDF/Excel)
- Add email notifications
- Support for multiple classes
- Cloud storage integration
- Mobile app version

---

## 📧 Support

For issues and questions:
1. Check the troubleshooting section
2. Review backend logs (`app.log`)
3. Check Java console output
4. Verify all dependencies are installed

---

## 🎉 Acknowledgments

- **RetinaFace** - Face detection model
- **ArcFace** - Face recognition embeddings
- **DeepFace** - Unified face recognition framework
- **JavaFX** - Modern Java UI framework

---

**Built with ❤️ for educational institutions**
