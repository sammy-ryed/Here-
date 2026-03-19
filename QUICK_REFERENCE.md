# Quick Reference Guide

## ⚡ Fast Setup (5 minutes)

```bash
# 1. Backend
cd python_backend
pip install -r requirements.txt
python db/migrate_postgres.py          # Or skip for SQLite
python db/seed_admin.py                 # Create admin user
python app.py                           # Start on :5000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                             # Start on :3000

# 3. Login
# Visit http://localhost:3000/login
# Username: admin
# Password: Admin@here1
```

## 🔐 Authentication

```javascript
// Automatic in all API calls
const apiClient = {
  login: (username, password) => Promise<{ token, username, role, user_id }>,
  logout: () => Promise<void>,
  // ... all other methods automatically include token
}

// Token stored in localStorage
localStorage.getItem('auth_token')      // JWT token
localStorage.getItem('user_info')       // User object
```

## 📡 API Client Methods

### Authentication
```javascript
await apiClient.login('admin', 'Admin@here1')
await apiClient.logout()
```

### Students
```javascript
await apiClient.getStudents()                           // List all
await apiClient.getStudentById(id)                      // Get one
await apiClient.registerStudent(name, roll_no, email, images)
await apiClient.deleteStudent(id)
await apiClient.updateStudentSection(studentId, sectionId)
```

### Attendance
```javascript
await apiClient.getDashboardStats()                     // Today's stats
await apiClient.processAttendance(image)                // Single photo
await apiClient.processBatchAttendance([images])        // Multiple photos
await apiClient.recognizeFace(base64Image)              // Live webcam
await apiClient.markAttendance(studentId, 'present'|'absent')
await apiClient.getAttendanceReport(startDate, endDate)
await apiClient.clearTodayAttendance()
```

### Face Management
```javascript
await apiClient.extractFaces(image)                     // Detect faces
await apiClient.assignFace(studentId, faceFilename)     // Map face to student
await apiClient.addEmbeddings(studentId, [images])      // Add photos
```

### Bulk Import
```javascript
await apiClient.bulkImportStudents(excelFile)           // Excel upload
```

### Sections
```javascript
await apiClient.getSections()
await apiClient.createSection(name, year, department, batch)
await apiClient.getSubjects(sectionId)
await apiClient.createSubject(name, code, sectionId)
```

### Sessions
```javascript
await apiClient.getSessions()
await apiClient.createSession(sectionId, subjectId, gpsLat, gpsLon)
await apiClient.confirmSession(sessionId)
await apiClient.voidSession(sessionId)
```

## 🛡️ Protected Routes

All routes except `/login` and `/self-register/[token]` require authentication:

```typescript
// In any page component:
const { isAuthenticated, isLoading } = useAuth();

useEffect(() => {
  if (!isLoading && !isAuthenticated) {
    router.push('/login');
  }
}, [isAuthenticated, isLoading, router]);
```

## 🌍 Environment Variables

### Backend (`python_backend/.env`)
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/here
JWT_SECRET_KEY=your-32-character-secret-here
JWT_EXPIRY_HOURS=8
SEED_ADMIN_USER=admin
SEED_ADMIN_PASS=Admin@here1
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## 🐛 Debugging

```javascript
// Check login status
const auth = useAuth();
console.log(auth.isAuthenticated, auth.user);

// Check token
console.log(localStorage.getItem('auth_token'));

// Check API errors
try {
  await apiClient.getStudents();
} catch (err) {
  console.error(err.response?.status);  // 401? 403? 500?
  console.error(err.response?.data?.error);
}

// Check backend logs
# Run with DEBUG
FLASK_DEBUG=True python app.py
```

## 📋 Common Tasks

### Add New API Endpoint

**Backend** (Flask):
```python
@app.route('/my-endpoint', methods=['GET'])
@require_auth
def my_endpoint():
    return jsonify({'data': 'value'})
```

**Frontend** (API client):
```typescript
myEndpoint: async () => {
  const response = await api.get('/my-endpoint');
  return response.data;
}
```

### Create a Protected Page

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function MyPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) return <LoadingSpinner />;

  return <PageContent />;
}
```

### Make API Call with Error Handling

```typescript
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');

const handleAction = async () => {
  try {
    setLoading(true);
    setError('');
    const result = await apiClient.getStudents();
    console.log('Success:', result);
  } catch (err: any) {
    if (err.response?.status === 401) {
      // Handled by interceptor
    } else if (err.response?.data?.error) {
      setError(err.response.data.error);
    } else {
      setError('An error occurred. Please try again.');
    }
  } finally {
    setLoading(false);
  }
};
```

## 🚀 Deployment Commands

```bash
# Build frontend
npm run build

# Start with Gunicorn (backend)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Start Next.js (frontend)
npm start
```

## 📱 Response Types

```typescript
// Login response
{
  token: string;
  username: string;
  role: 'admin' | 'teacher';
  user_id: number;
}

// Attendance result
{
  present: Student[];
  absent: Student[];
  unrecognized: string[];       // face filenames
  total_faces: number;
  processing_time: string;
  timestamp: string;
}

// Dashboard stats
{
  total_students: number;
  present_today: number;
  absent_today: number;
  attendance_rate: number;
  date: string;
  students: Student[];
}
```

## ❌ Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check parameters |
| 401 | Unauthorized | Login first |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Check backend logs |

## 🔗 Quick Links

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Docs: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- Setup Guide: [SETUP.md](SETUP.md)
- Status: [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md)

## 📞 Support

**Frontend Issues:**
- Check `npx eslint .`
- Check browser DevTools Console
- Check Network tab for API responses

**Backend Issues:**
- Check terminal output
- Enable `FLASK_DEBUG=True`
- Check database connection

**Auth Issues:**
- Clear `localStorage`
- Check `JWT_SECRET_KEY` matches
- Check token expiry time

---

**Last Updated:** March 19, 2026  
**Version:** 1.0  
**Status:** ✅ Complete
