# Frontend-Backend Integration Guide

This document describes the complete integration between the Next.js frontend and the Python Flask backend for the Face Recognition Attendance System.

## Overview

The system now has full authentication and API integration:

- **Authentication**: JWT-based authentication via Bearer tokens
- **Authorization**: Role-based access control (admin, teacher)
- **API Client**: Comprehensive Axios-based API integration
- **Protected Routes**: All authenticated pages redirect to login

## Architecture

### Authentication Flow

```
1. User enters credentials on /login
   ↓
2. Frontend calls apiClient.login(username, password)
   ↓
3. Backend validates credentials and returns JWT token
   ↓
4. Frontend stores token in localStorage
   ↓
5. All subsequent API calls include token in Authorization header
   ↓
6. Backend validates token and grants access
```

### API Integration

#### Frontend API Client (`frontend/lib/api.ts`)

The `apiClient` provides all backend endpoints with:
- Automatic token injection via axios interceptor
- Error handling and 401 redirect
- Timeout configuration per endpoint type
- Full TypeScript support

#### Available Endpoints

**Core Functionality:**
- `checkHealth()` - Server health check
- `getDashboardStats()` - Today's attendance overview
- `getStudents()` - List all registered students

**Registration:**
- `registerStudent(name, rollNo, email, images)` - Manual registration
- `bulkImportStudents(excelFile)` - Excel bulk import
- `addEmbeddings(studentId, images)` - Add photos to existing student

**Attendance:**
- `processAttendance(image)` - Single-image attendance
- `processBatchAttendance(images)` - Multi-image attendance
- `recognizeFace(base64Image)` - Live webcam recognition
- `markAttendance(studentId, status)` - Manual attendance marking
- `getAttendanceReport(startDate, endDate)` - Historical report
- `clearTodayAttendance()` - Clear today's records

**Face Management:**
- `extractFaces(image)` - Detect and extract faces from image
- `assignFace(studentId, faceFilename)` - Map face crop to student
- `getUnrecognizedFace(filename)` - Retrieve unrecognized face image

**Students:**
- `getStudentById(studentId)` - Get student details
- `deleteStudent(studentId)` - Delete a student
- `clearAllStudents()` - Delete all students (admin only)
- `updateStudentSection(studentId, sectionId)` - Assign to section

**Authentication:**
- `login(username, password)` - Get JWT token
- `logout()` - Logout (server-side ack)

**Classes (New):**
- `getSections()` - List all sections
- `createSection(name, year, department, batch)` - Create section
- `getSubjects(sectionId)` - List subjects in section
- `createSubject(name, code, sectionId)` - Create subject

**Teacher-Section Assignment:**
- `getTeacherSections()` - Get teacher's sections
- `assignTeacherSection(teacherId, sectionId)` - Assign teacher to section

**Attendance Sessions:**
- `getSessions()` - List all sessions
- `createSession(sectionId, subjectId, gpsLat, gpsLon)` - Create session
- `confirmSession(sessionId)` - Confirm session attendance
- `voidSession(sessionId)` - Void a session

## Setup Instructions

### 1. Backend Setup

#### Prerequisites
- Python 3.11+
- PostgreSQL 12+ (or SQLite for development)
- Node.js 18+ (for frontend)

#### Steps

```bash
# Clone repository
cd herept2/python_backend

# Create .env file with database config
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/here" > .env
echo "JWT_SECRET_KEY=your-super-secret-key-change-in-production" >> .env
echo "JWT_EXPIRY_HOURS=8" >> .env

# Install dependencies
pip install -r requirements.txt

# Run migrations
python db/migrate_postgres.py

# Seed admin user
python db/seed_admin.py
# This creates:
#   Username: admin
#   Password: Admin@here1
```

#### Environment Variables

```env
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/here

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-minimum-32-chars
JWT_EXPIRY_HOURS=8

# Optional Admin Seed Credentials
SEED_ADMIN_USER=admin
SEED_ADMIN_PASS=Admin@here1
```

#### Running Backend

```bash
# Terminal 1 - Backend
cd python_backend
python app.py
# Server runs on http://localhost:5000
```

### 2. Frontend Setup

#### Prerequisites
- Node.js 18+
- npm or yarn

#### Steps

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > .env.local

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
```

#### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 3. Authentication Setup

The system uses JWT tokens with the following roles:

- **admin**: Full system access including user management
- **teacher**: Attendance taking, student management for their sections
- **student** (beta): Subset of features (not fully implemented yet)

#### Creating Users

```python
# Via seed script
python db/seed_admin.py

# Via Python script
from db.auth_db import AuthDB
import bcrypt

auth_db = AuthDB()
password_hash = bcrypt.hashpw(b'teacher_password', bcrypt.gensalt()).decode('utf-8')
teacher_id = auth_db.create_user('teacher1', password_hash, role='teacher')
```

#### Demo Credentials

After running `seed_admin.py`:
- Username: `admin`
- Password: `Admin@here1`

## Frontend Architecture

### Directory Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── page.tsx                  # Dashboard
│   ├── login/page.tsx            # Login page
│   ├── register/page.tsx         # Manual registration
│   ├── bulk-import/page.tsx      # Excel bulk import
│   ├── attendance/page.tsx       # Attendance marking
│   ├── embeddings/page.tsx       # Add photos to students
│   └── self-register/[token]/    # Student self-registration
├── components/
│   ├── Navigation.tsx            # Top navigation with auth info
│   └── ProtectedRoute.tsx        # Auth protection wrapper
├── lib/
│   ├── api.ts                    # API client with interceptors
│   ├── types.ts                  # TypeScript interfaces
│   └── auth-context.tsx          # Auth state management
└── layout.tsx                    # Root layout with AuthProvider
```

### Authentication Components

#### AuthProvider (`lib/auth-context.tsx`)

Manages authentication state globally:

```typescript
const { user, isAuthenticated, isLoading, logout } = useAuth();
```

**Properties:**
- `user`: Current user object with `user_id`, `username`, `role`
- `isAuthenticated`: Boolean indicating login status
- `isLoading`: Boolean for initial auth check
- `logout()`: Function to logout and redirect to login

#### API Interceptors (`lib/api.ts`)

Automatically:
1. Injects JWT token from localStorage into Authorization header
2. Redirects to login on 401 Unauthorized
3. Clears token on auth failure

#### Protected Pages

All pages except `/login` and `/self-register/[token]` have:

```typescript
useEffect(() => {
  if (!isLoading && !isAuthenticated) {
    router.push('/login');
  }
}, [isAuthenticated, isLoading, router]);
```

## Token Management

### Token Storage

Tokens are stored in browser `localStorage`:

```javascript
localStorage.setItem('auth_token', token);        // JWT token
localStorage.setItem('user_info', JSON.stringify(userObject)); // User metadata
```

### Token Lifecycle

1. **Login**: User submits credentials → receives token (valid for 8 hours)
2. **Usage**: Token automatically included in all authenticated requests
3. **Expiry**: 401 response → token cleared → redirect to login
4. **Logout**: Manual logout clears token and displays login

### Token Refresh

The current implementation doesn't include token refresh. For production:

```typescript
// Add to api.ts interceptor
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const newToken = await apiClient.refreshToken(refreshToken);
          localStorage.setItem('auth_token', newToken);
          return api.request(error.config);
        } catch {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

## Error Handling

### API Errors

All API calls can throw errors. Handle them:

```typescript
try {
  const result = await apiClient.processBatchAttendance(images);
} catch (err: any) {
  if (err.response?.status === 401) {
    // Handled by interceptor - redirects to login
  } else if (err.response?.status === 403) {
    // Forbidden - insufficient permissions
    setError('You do not have permission to perform this action');
  } else if (err.response?.data?.error) {
    // API error message
    setError(err.response.data.error);
  } else {
    // Network or unknown error
    setError('An error occurred. Please try again.');
  }
}
```

### Auth Failures

401 Unauthorized responses automatically trigger:
1. Token cleared from localStorage
2. Redirect to `/login`
3. Log in again to continue

## Cross-Origin (CORS)

Backend CORS configuration:

```python
# app.py
CORS(app)  # Allows all origins (change for production)
```

Frontend can make requests to backend without CORS issues.

## Deployment Checklist

### Backend
- [ ] Set `JWT_SECRET_KEY` to strong random value
- [ ] Use PostgreSQL (not SQLite) for production
- [ ] Set `CORS` to specific frontend domain
- [ ] Enable HTTPS
- [ ] Set env vars in deployment platform

### Frontend
- [ ] Set `NEXT_PUBLIC_API_URL` to backend domain
- [ ] Build with `npm run build`
- [ ] Deploy to Vercel, Netlify, or self-hosted

### Security
- [ ] Change default admin password
- [ ] Use HTTPS for all traffic
- [ ] Set `SameSite=Secure` on cookies
- [ ] Implement token refresh mechanism
- [ ] Add rate limiting to auth endpoints

## Troubleshooting

### "Missing or malformed Authorization header"

**Problem**: API returns 401 with this message
**Cause**: Token not being sent
**Fix**: Check localStorage for auth_token:
```javascript
console.log(localStorage.getItem('auth_token'));
```

### CORS Errors

**Problem**: Browser blocks API request
**Cause**: Backend CORS not configured
**Fix**: Ensure backend has `CORS(app)` and correct origins

### "Invalid token"

**Problem**: 401 with "Invalid token"
**Cause**: Token is expired or corrupted
**Fix**: User must log in again

### Long response times

**Problem**: API calls are slow
**Cause**: Face processing is CPU-intensive
**Fix**: Increase timeout in api.ts:
```typescript
timeout: 300000, // 5 minutes
```

## Next Steps

1. **Implement Token Refresh**: Add refresh token flow
2. **Add Permission System**: Fine-grained access control
3. **Add Rate Limiting**: Protect auth endpoints
4. **Add Logging**: Audit trail for API usage
5. **Add Analytics**: Track system usage
6. **Implement Email**: Notify teachers of system events
7. **Add Mobile App**: React Native client

## References

- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)
- [JWT.io](https://jwt.io/)  
- [Next.js Authentication](https://nextjs.org/docs/authentication)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)

## Support

For issues or questions:
1. Check error messages in browser console
2. Check backend logs: `python_backend/app.py`
3. Verify environment variables
4. Ensure backend is running on correct port
5. Check network tab in DevTools
