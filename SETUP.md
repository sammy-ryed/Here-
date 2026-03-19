# Complete Setup Guide - Face Recognition Attendance System

This guide covers setting up the entire application from scratch.

## Quick Start (Windows)

### 1. Clone/Setup Repository

```bash
cd herept2
```

### 2. Run Backend Setup

```bash
# Run the setup script which installs all dependencies
./setup.bat

# This script:
# - Creates Python virtual environment
# - Installs Python dependencies
# - Installs Node.js dependencies
# - Creates necessary .env files
```

### 3. Configure Environment

#### Backend (.env)

Create `python_backend/.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/here
JWT_SECRET_KEY=your-32-character-secret-key-here
JWT_EXPIRY_HOURS=8
SEED_ADMIN_USER=admin
SEED_ADMIN_PASS=Admin@here1
```

#### Frontend (.env.local)

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 4. Initialize Database

```bash
cd python_backend

# For PostgreSQL
python db/migrate_postgres.py

# Create admin user
python db/seed_admin.py
```

### 5. Start Application

#### Terminal 1 - Backend

```bash
./run_back.bat
# Or manually:
# cd python_backend
# python app.py
```

Backend starts on: `http://localhost:5000`

#### Terminal 2 - Frontend

```bash
./run_front.bat
# Or manually:
# cd frontend
# npm run dev
```

Frontend starts on: `http://localhost:3000`

### 6. Login

Navigate to `http://localhost:3000/login`

**Default Credentials:**
- Username: `admin`
- Password: `Admin@here1`

## Detailed Setup Instructions

### Prerequisites

#### Windows
- Python 3.11+ (from python.org)
- Node.js 18+ LTS (from nodejs.org)
- PostgreSQL 12+ (optional, for production)
- Git (optional)

#### macOS/Linux
```bash
# macOS (using Homebrew)
brew install python@3.11 node postgresql

# Ubuntu/Debian
sudo apt-get install python3.11 nodejs postgresql postgresql-contrib
```

### Backend Setup (Detailed)

#### 1. Create Virtual Environment

```bash
cd python_backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3.11 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages installed:
- Flask 3.0 - Web framework
- DeepFace 0.0.92 - Face recognition
- RetinaFace 0.0.17 - Face detection
- OpenCV 4.10 - Image processing
- psycopg2 - PostgreSQL driver
- PyJWT - JWT authentication
- python-dotenv - Environment variables

#### 3. Setup Database

**Option A: SQLite (Development)**

```bash
# SQLite is automatically created on first run
python app.py
# Database file: attendance.db
```

**Option B: PostgreSQL (Recommended)**

```bash
# 1. Create database
createdb here

# 2. Run migrations
python db/migrate_postgres.py

# 3. Update .env with PostgreSQL URL
```

#### 4. Create Admin User

```bash
python db/seed_admin.py
```

Expected output:
```
==================================================
[seed_admin] ✅ Admin user created successfully
  User ID  : 1
  Username : admin
  Password : Admin@here1
==================================================
```

#### 5. Start Backend

```bash
python app.py
```

Expected output:
```
 * Running on http://localhost:5000
```

#### 6. Verify Backend

```bash
# In another terminal
curl http://localhost:5000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-03-19T10:00:00.000000",
#   "services": {
#     "face_detector": true,
#     "face_recognizer": true,
#     "database": true
#   }
# }
```

### Frontend Setup (Detailed)

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

Key packages:
- Next.js 16 - React framework
- React 19 - UI library
- Tailwind CSS 4 - Styling
- Axios - HTTP client
- react-webcam - Webcam access
- lucide-react - Icons
- SheetJS - Excel export

#### 2. Environment Configuration

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

#### 3. Start Frontend

```bash
npm run dev
```

Expected output:
```
- ready on 0.0.0.0:3000
```

#### 4. Access Application

- Frontend: http://localhost:3000
- Dashboard: http://localhost:3000/
- Login: http://localhost:3000/login

### Verify Integration

#### 1. Check Backend Health

```bash
curl -X GET http://localhost:5000/health
```

#### 2. Login to Frontend

1. Navigate to http://localhost:3000/login
2. Enter credentials:
   - Username: `admin`
   - Password: `Admin@here1`
3. Click "Sign In"

#### 3. Check Dashboard

Should display:
- 4 stat cards (Total Students, Present Today, Absent Today, Attendance Rate)
- Student records table (initially empty)

#### 4. Test API Call

In browser console:

```javascript
// Check stored token
console.log(localStorage.getItem('auth_token'));

// Test API call
fetch('http://localhost:5000/students', {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
}).then(r => r.json()).then(console.log);
```

## Folder Structure

```
herept2/
├── python_backend/                 # Flask backend
│   ├── app.py                      # Main application
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables
│   ├── .env.example                # Example config
│   ├── auth/                       # Authentication
│   │   ├── decorators.py           # @require_auth decorator
│   │   ├── jwt_utils.py            # Token generation/validation
│   │   └── __init__.py
│   ├── db/                         # Database layer
│   │   ├── database.py             # Main database ORM
│   │   ├── auth_db.py              # User management
│   │   ├── sections_db.py          # Classes
│   │   ├── migrate_postgres.py     # PostgreSQL setup
│   │   └── seed_admin.py           # Create admin user
│   ├── utils/                      # Utilities
│   │   ├── face_detector.py        # RetinaFace wrapper
│   │   ├── face_recognizer.py      # Facenet512 wrapper
│   │   └── image_utils.py          # Image processing
│   ├── uploads/                    # Temporary files
│   └── unrecognized/               # Unrecognized face crops
│
├── frontend/                        # Next.js frontend
│   ├── package.json                # Node dependencies
│   ├── .env.local                  # Environment variables
│   ├── next.config.ts              # Next.js config
│   ├── tsconfig.json               # TypeScript config
│   ├── app/                        # Routes
│   │   ├── layout.tsx              # Root layout with Auth
│   │   ├── page.tsx                # Dashboard
│   │   ├── login/page.tsx          # Login page
│   │   ├── register/page.tsx       # Manual registration
│   │   ├── bulk-import/page.tsx    # Bulk import
│   │   ├── attendance/page.tsx     # Attendance marking
│   │   ├── embeddings/page.tsx     # Add embeddings
│   │   └── self-register/[token]/  # Student registration
│   ├── components/                 # Reusable components
│   │   ├── Navigation.tsx          # Top navbar
│   │   └── ProtectedRoute.tsx      # Auth wrapper
│   ├── lib/
│   │   ├── api.ts                  # API client
│   │   ├── types.ts                # TypeScript types
│   │   └── auth-context.tsx        # Auth state
│   └── public/                     # Static assets
│
├── setup.bat                        # Windows setup script
├── run_back.bat                     # Windows backend launcher
├── run_front.bat                    # Windows frontend launcher
├── INTEGRATION_GUIDE.md             # API & auth documentation
└── README.md                        # Project overview
```

## Configuration Files

### Backend Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | sqlite | Database connection string |
| `JWT_SECRET_KEY` | change-me | Token signing secret |
| `JWT_EXPIRY_HOURS` | 8 | Token validity period |
| `FLASK_ENV` | development | Environment |
| `FLASK_DEBUG` | False | Debug mode |

### Frontend Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | http://localhost:5000 | Backend API URL |

## Common Issues & Solutions

### "ImportError: No module named 'flask'"

```bash
# Activate virtual environment
python_backend\venv\Scripts\activate   # Windows
source python_backend/venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r python_backend/requirements.txt
```

### "Connection refused" to backend

```bash
# Check backend is running on port 5000
netstat -ano | findstr :5000     # Windows
lsof -i :5000                     # macOS/Linux

# Kill process if stuck
taskkill /PID <pid> /F            # Windows
kill -9 <pid>                     # macOS/Linux

# Restart backend
python python_backend/app.py
```

### "CORS error" in frontend

```bash
# Backend CORS is not configured correctly
# Ensure this is in python_backend/app.py:
# CORS(app)

# Or restrict origins:
# CORS(app, origins=['http://localhost:3000'])
```

### "Invalid token" after login

```bash
# Clear browser storage
# Open DevTools → Application → Storage → Clear All

# Log in again
```

### PostgreSQL connection failed

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Create database if needed
createdb here

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/here
```

## Production Deployment

### Backend (Gunicorn)

```bash
# Install production server
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With environment file
gunicorn --env-file .env -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend (Next.js)

```bash
# Build for production
npm run build

# Start production server
npm start

# Or use PM2
npm install -g pm2
pm2 start npm --name "frontend" -- start
```

### Docker (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: here
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  backend:
    build: ./python_backend
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/here
      JWT_SECRET_KEY: your-secret-key
    ports:
      - "5000:5000"
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:5000
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

Run with: `docker-compose up`

## Testing

### Backend Health Check

```bash
curl http://localhost:5000/health
```

### Frontend Smoke Test

```bash
curl http://localhost:3000/
```

### API Authentication Test

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@here1"}' | jq -r .token)

# Make authenticated request
curl http://localhost:5000/students \
  -H "Authorization: Bearer $TOKEN"
```

## Next Steps

1. **Register Students**: Use the Register page or Bulk Import
2. **Take Attendance**: Upload classroom photos
3. **View Reports**: Check dashboard for attendance stats
4. **Create Classes**: Set up sections and subjects
5. **Manage Teachers**: Assign teachers to classes

## Support

For help:
1. Check logs:
   ```bash
   # Backend: Check terminal output
   # Frontend: Check browser DevTools Console
   ```

2. Enable debug mode:
   ```bash
   # backend/.env
   FLASK_DEBUG=True
   ```

3. Check integration guide: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

## References

- **Frontend Framework**: https://nextjs.org/docs
- **Backend Framework**: https://flask.palletsprojects.com/
- **Face Recognition**: https://github.com/serengp/DeepFace
- **Face Detection**: https://github.com/biubug6/Retinaface
- **Database**: https://www.postgresql.org/docs/
- **Authentication**: https://jwt.io/
