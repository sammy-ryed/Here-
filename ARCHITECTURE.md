# 🏗️ System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│                  JavaFX Desktop Application                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Dashboard │  │ Register  │  │Attendance │  │  Reports  │  │
│  │    UI     │  │ Student   │  │   Taking  │  │    UI     │  │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │
│        └────────────────┴───────────────┴──────────────┘        │
│                             │                                    │
│                    ┌────────▼─────────┐                         │
│                    │  API Service     │                         │
│                    │  (REST Client)   │                         │
│                    └────────┬─────────┘                         │
└─────────────────────────────┼──────────────────────────────────┘
                              │
                    HTTP/JSON │ (Port 5000)
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                      SERVICE LAYER                              │
│                    Flask REST API Server                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   API Endpoints                          │  │
│  │  /health | /register_face | /process_attendance         │  │
│  │  /students | /unrecognized | /attendance/report         │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│      ┌───────────────┼───────────────┐                         │
│      │               │               │                         │
│      ▼               ▼               ▼                         │
│  ┌────────┐    ┌──────────┐   ┌───────────┐                  │
│  │ Face   │    │  Face    │   │  Image    │                  │
│  │Detector│    │Recognizer│   │ Processor │                  │
│  └────┬───┘    └────┬─────┘   └─────┬─────┘                  │
└───────┼─────────────┼───────────────┼────────────────────────┘
        │             │               │
        ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI/ML LAYER                                │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│  │  RetinaFace  │   │   ArcFace    │   │   OpenCV     │      │
│  │  Detection   │   │ Recognition  │   │  Processing  │      │
│  │  (Multi-Face)│   │ (Embeddings) │   │   (Utils)    │      │
│  └──────────────┘   └──────────────┘   └──────────────┘      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   SQLite Database                        │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐    │  │
│  │  │  Students  │  │  Embeddings │  │  Attendance  │    │  │
│  │  │   Table    │  │    Table    │  │    Table     │    │  │
│  │  └────────────┘  └─────────────┘  └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    File Storage                          │  │
│  │  [uploads/] [unrecognized/] [models/]                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction Flow

### 1️⃣ Student Registration Flow

```
User → JavaFX UI
         │
         ├─ Enter Name & Roll Number
         ├─ Upload/Capture Photos
         │
         ▼
   ApiService.registerStudent()
         │
         ├─ HTTP POST /register_face
         ├─ Multipart Form Data
         │   ├─ name: "John Doe"
         │   ├─ roll_no: "001"
         │   └─ images: [file1.jpg, file2.jpg, ...]
         │
         ▼
   Flask Backend (app.py)
         │
         ├─ Validate Input
         ├─ Save Temp Files
         │
         ▼
   FaceDetector.detect_faces()
         │
         ├─ RetinaFace Detection
         ├─ Find Face Bounding Boxes
         ├─ Extract Facial Landmarks
         │
         ▼
   FaceRecognizer.get_embedding()
         │
         ├─ Crop Face Region
         ├─ Align Face
         ├─ ArcFace Model
         ├─ Generate 512-dim Embedding
         ├─ Normalize Vector
         │
         ▼
   Database.add_student()
         │
         ├─ Average Multiple Embeddings
         ├─ Store in Students Table
         ├─ Store Individual Embeddings
         ├─ Return Student ID
         │
         ▼
   JSON Response → ApiService → UI
         │
         └─ Display Success Message
```

---

### 2️⃣ Attendance Taking Flow

```
User → JavaFX UI
         │
         ├─ Upload/Capture Classroom Photo
         │
         ▼
   ApiService.processAttendance()
         │
         ├─ HTTP POST /process_attendance
         ├─ Multipart Form Data
         │   ├─ image: classroom.jpg
         │   └─ class_name: "CS101"
         │
         ▼
   Flask Backend (app.py)
         │
         ├─ Validate Image
         ├─ Save Temp File
         │
         ▼
   FaceDetector.detect_faces()
         │
         ├─ RetinaFace Multi-Face Detection
         ├─ Find All Faces in Image
         ├─ Extract Bounding Boxes
         │   Face 1: [x1, y1, x2, y2]
         │   Face 2: [x1, y1, x2, y2]
         │   Face 3: [x1, y1, x2, y2]
         │   ...
         │
         ▼
   For Each Detected Face:
         │
         ├─ FaceRecognizer.get_embedding()
         │   └─ Generate Face Embedding
         │
         ├─ FaceRecognizer.find_match()
         │   ├─ Load All Student Embeddings
         │   ├─ Calculate Cosine Similarity
         │   ├─ Find Best Match
         │   └─ Check Confidence > Threshold
         │
         ├─ IF Match Found:
         │   └─ Add to Present List
         │
         └─ ELSE:
             ├─ Crop Face Image
             └─ Save to unrecognized/
         │
         ▼
   Database.get_all_students()
         │
         ├─ Compare Present vs Registered
         ├─ Generate Absent List
         │
         ▼
   Database.mark_attendance()
         │
         ├─ Update Attendance Table
         ├─ Mark Present Students
         │
         ▼
   JSON Response → ApiService → UI
         │
         ├─ Present: [{"name": "John", "confidence": 0.95}, ...]
         ├─ Absent: [{"name": "Jane", "roll_no": "002"}, ...]
         ├─ Unrecognized: ["face1.jpg", "face2.jpg"]
         └─ Total Faces: 15
         │
         ▼
   UI Display
         │
         ├─ Show Present Table (Green ✓)
         ├─ Show Absent Table (Red ✗)
         ├─ Show Unrecognized Faces
         └─ Allow Retake
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Student   │
│   Photos    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Face Detection │
│   (RetinaFace)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐       ┌──────────────┐
│ Face Alignment  │──────▶│   ArcFace    │
│   & Cropping    │       │   Model      │
└─────────────────┘       └──────┬───────┘
                                 │
                                 ▼
                          ┌──────────────┐
                          │  512-dim     │
                          │  Embedding   │
                          └──────┬───────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
         ┌───────────┐   ┌────────────┐   ┌──────────┐
         │ Students  │   │ Embeddings │   │ Cosine   │
         │  Table    │   │   Table    │   │Similarity│
         └───────────┘   └────────────┘   └─────┬────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  Recognition │
                                          │    Result    │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  Attendance  │
                                          │   Record     │
                                          └──────────────┘
```

---

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │              JavaFX 17                           │  │
│  │  • FXML Layouts  • CSS Styling  • Controls      │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                APPLICATION LAYER                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Java Business Logic                      │  │
│  │  • Controllers  • Models  • Services  • Utils   │  │
│  │  • Maven Build  • Gson JSON  • HttpClient       │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ REST API (HTTP/JSON)
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  API GATEWAY                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Flask 2.3                           │  │
│  │  • Routes  • Request Handling  • Response       │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│               BUSINESS LOGIC LAYER                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Python Processing                        │  │
│  │  • Face Detection  • Recognition  • Validation  │  │
│  │  • Image Processing  • Embedding Management     │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 AI/ML MODELS                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RetinaFace (Detection) + ArcFace (Recognition) │  │
│  │  OpenCV (Processing) + NumPy (Computation)      │  │
│  │  Scikit-learn (Similarity)                      │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                PERSISTENCE LAYER                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           SQLite Database                        │  │
│  │  • Students  • Embeddings  • Attendance         │  │
│  │  • Indexes  • Constraints  • Triggers           │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │           File System Storage                    │  │
│  │  • Uploads  • Unrecognized  • Models  • Logs   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────┐
│              Input Layer                    │
│  ┌─────────────────────────────────────┐   │
│  │  • File Type Validation             │   │
│  │  • Size Limit Check (16MB)          │   │
│  │  • Extension Whitelist              │   │
│  └─────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Processing Layer                  │
│  ┌─────────────────────────────────────┐   │
│  │  • Input Sanitization               │   │
│  │  • SQL Parameterization             │   │
│  │  • Safe File Handling               │   │
│  └─────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            Storage Layer                    │
│  ┌─────────────────────────────────────┐   │
│  │  • Secure Filename Generation       │   │
│  │  • Binary Blob Storage              │   │
│  │  • Access Control Ready             │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## Deployment Architecture (Recommended for Production)

```
┌────────────────────────────────────────────────────────┐
│                    Client Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   Desktop    │  │  Web Browser │  │ Mobile App  │ │
│  │     App      │  │   (Future)   │  │  (Future)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
└─────────┼──────────────────┼──────────────────┼────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    HTTPS (SSL/TLS)
                             │
┌────────────────────────────▼────────────────────────────┐
│                   Load Balancer                         │
│              (Nginx / HAProxy)                          │
└────────────────────────────┬────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  API Server │    │  API Server │    │  API Server │
│   Instance  │    │   Instance  │    │   Instance  │
│   (Flask +  │    │   (Flask +  │    │   (Flask +  │
│  Gunicorn)  │    │  Gunicorn)  │    │  Gunicorn)  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │  File Store  │
│   Database   │  │    Cache     │  │   (S3/Blob)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

**🏗️ Architecture designed for scalability, maintainability, and performance!**
