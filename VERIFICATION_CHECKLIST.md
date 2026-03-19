# Integration Verification Checklist

Use this checklist to verify the backend-frontend integration is working correctly.

## 🔧 Pre-Launch Verification

### Backend Setup

- [ ] Python 3.11+ installed: `python --version`
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] Dependencies installed: `pip list | grep flask`
- [ ] Database configured in `.env`
- [ ] `JWT_SECRET_KEY` set in `.env`
- [ ] Admin user seeded: `python db/seed_admin.py`
- [ ] Backend starts: `python app.py` (no errors)
- [ ] Backend health check: `curl http://localhost:5000/health`

### Frontend Setup

- [ ] Node.js 18+ installed: `node --version`
- [ ] Dependencies installed: `npm list` (no errors)
- [ ] Environment configured: `.env.local` with `NEXT_PUBLIC_API_URL`
- [ ] Frontend builds: `npm run build` (no errors)
- [ ] Frontend starts: `npm run dev` (ready on port 3000)

## 🧪 Runtime Verification

### Backend Health

```bash
# Should return "healthy"
curl http://localhost:5000/health
```

Expected:
```json
{
  "status": "healthy",
  "services": {
    "face_detector": true,
    "face_recognizer": true,
    "database": true
  }
}
```

**Status:** [ ] ✅ [ ] ❌

### Authentication Flow

1. [ ] Login page loads: `http://localhost:3000/login`
2. [ ] Login form displays
3. [ ] Enter credentials: admin / Admin@here1
4. [ ] Click "Sign In"
5. [ ] Redirected to dashboard: `http://localhost:3000/`
6. [ ] No "401 Unauthorized" errors

**Status:** [ ] ✅ [ ] ❌

### API Connectivity

Open browser DevTools → Network tab:

1. [ ] Load dashboard page
2. [ ] Check network requests
3. [ ] Look for `/dashboard/stats` request
4. [ ] Should have `Authorization: Bearer <token>` header
5. [ ] Response status should be 200

**Status:** [ ] ✅ [ ] ❌

### Token Management

In browser console:

```javascript
// Check token exists
console.log(localStorage.getItem('auth_token'));
// Should output JWT token (eyJ0eXAi...)

// Check user info
console.log(JSON.parse(localStorage.getItem('user_info')));
// Should output: { user_id: 1, username: 'admin', role: 'admin' }
```

- [ ] Token exists in localStorage
- [ ] User info correctly stored
- [ ] Token is valid JWT format

**Status:** [ ] ✅ [ ] ❌

### Protected Routes

1. [ ] Clear localStorage: `localStorage.clear()`
2. [ ] Go to dashboard: `http://localhost:3000/`
3. [ ] Should redirect to: `http://localhost:3000/login`
4. [ ] Cannot access dashboard without login

**Status:** [ ] ✅ [ ] ❌

### Route Protection on All Pages

- [ ] `/register` - Requires auth
- [ ] `/bulk-import` - Requires auth
- [ ] `/attendance` - Requires auth
- [ ] `/embeddings` - Requires auth
- [ ] `/login` - Accessible without auth
- [ ] `/self-register/[token]` - Accessible without auth

**Status:** [ ] ✅ [ ] ❌

### Navigation Bar

- [ ] Displays username (admin)
- [ ] Displays role (in lowercase: admin)
- [ ] LogOut button present and clickable
- [ ] Clicking LogOut redirects to login
- [ ] Clears token from localStorage

**Status:** [ ] ✅ [ ] ❌

### API Endpoints (Test Sample)

#### Get Students

Terminal:
```bash
TOKEN=$(curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@here1"}' | jq -r .token)

curl http://localhost:5000/students \
  -H "Authorization: Bearer $TOKEN"
```

- [ ] Returns 200 status
- [ ] Returns valid JSON
- [ ] Contains students array

**Status:** [ ] ✅ [ ] ❌

#### Register Student

```bash
curl -X POST http://localhost:5000/register_face \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=John Doe" \
  -F "roll_no=001" \
  -F "email=john@example.com" \
  -F "images=@photo.jpg"
```

- [ ] Accepts multipart request
- [ ] Validates authentication header
- [ ] Returns success response

**Status:** [ ] ✅ [ ] ❌

### Error Handling

#### Missing Token

```bash
curl http://localhost:5000/students
# Should get: 401 Unauthorized
```

- [ ] Returns 401 status
- [ ] Error message about missing header
- [ ] Does NOT return student data

**Status:** [ ] ✅ [ ] ❌

#### Invalid Token

```bash
curl http://localhost:5000/students \
  -H "Authorization: Bearer invalid.token.here"
# Should get: 401 Unauthorized
```

- [ ] Returns 401 status
- [ ] Error message about invalid token
- [ ] Does NOT return student data

**Status:** [ ] ✅ [ ] ❌

#### Expired Token (if testing)

After JWT expires (8 hours by default):
- [ ] API returns 401
- [ ] Frontend shows error
- [ ] User redirected to login

**Status:** [ ] ✅ [ ] ❌

## 📊 Feature Verification

### Dashboard Features

- [ ] Stats cards display (Total, Present, Absent, Rate)
- [ ] Student records table shows
- [ ] Mark Present/Absent buttons work
- [ ] Delete student button works
- [ ] Data refreshes periodically

**Status:** [ ] ✅ [ ] ❌

### Register Page

- [ ] Form displays all fields
- [ ] File upload works
- [ ] Webcam capture works
- [ ] Photo preview shows
- [ ] Submit button registers student

**Status:** [ ] ✅ [ ] ❌

### Bulk Import

- [ ] Excel file upload works
- [ ] Shows import results
- [ ] Displays success/failure counts
- [ ] Shows registration links for tokens

**Status:** [ ] ✅ [ ] ❌

### Attendance Page

- [ ] Photo upload works
- [ ] Image preview shows
- [ ] Processing works
- [ ] Results display correctly

**Status:** [ ] ✅ [ ] ❌

### Embeddings Page

- [ ] Extract faces from image
- [ ] Shows detected faces
- [ ] Can assign faces to students
- [ ] Updates student embeddings

**Status:** [ ] ✅ [ ] ❌

## 🔒 Security Verification

### Token Security

- [ ] Token stored in localStorage (not in cookie)
- [ ] Token sent in Authorization header
- [ ] Token format is valid JWT
- [ ] Token has expiry time

**Status:** [ ] ✅ [ ] ❌

### Request Security

All authenticated requests should have:
- [ ] `Authorization: Bearer <token>` header
- [ ] HTTPS in production (HTTP acceptable for dev)
- [ ] Content-Type headers correct

**Status:** [ ] ✅ [ ] ❌

### Password Security

- [ ] Passwords hashed in database
- [ ] Demo password only for development
- [ ] Changed in production

**Status:** [ ] ✅ [ ] ❌

## 📱 Cross-Browser Testing

- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works in Edge

**Status:** [ ] ✅ [ ] ❌

## 🌐 CORS Testing

Frontend requests from http://localhost:3000 to http://localhost:5000:

- [ ] Login request succeeds
- [ ] Data requests succeed
- [ ] File uploads work (multipart)

**Status:** [ ] ✅ [ ] ❌

## 📊 Performance Verification

### Load Times

- [ ] Login page loads in < 2s
- [ ] Dashboard loads in < 3s
- [ ] API calls respond in < 5s

**Status:** [ ] ✅ [ ] ❌

### File Uploads

- [ ] Single photo upload: < 10s
- [ ] Batch upload (10 photos): < 30s

**Status:** [ ] ✅ [ ] ❌

## 🐛 Debug Mode

### Backend Debug

```bash
# Start backend with debug
FLASK_DEBUG=True python app.py
```

- [ ] Shows detailed error messages
- [ ] Reloads on code changes
- [ ] Shows request logs

**Status:** [ ] ✅ [ ] ❌

### Frontend Debug

DevTools Console:
```javascript
// Should show useful logs
console.log(localStorage.getItem('auth_token'));
```

- [ ] No console errors
- [ ] API responses visible
- [ ] Token info accessible

**Status:** [ ] ✅ [ ] ❌

## ✅ Final Verification

### System Ready for Use

- [ ] Backend running without errors
- [ ] Frontend running without errors
- [ ] Login works correctly
- [ ] All pages accessible after login
- [ ] All API endpoints responding
- [ ] Authentication working properly
- [ ] Token management correct
- [ ] Error handling in place

### Sign-Off

- [ ] **Integration Status: READY FOR PRODUCTION** 

Signed off by: _________________  
Date: _________________

## Notes

_Use this space for any issues found or notes about the integration:_

```
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________
```

## Next Steps

If all checks pass:
1. ✅ Integration is complete
2. ✅ System is ready for testing
3. ✅ Can proceed to production deployment
4. ✅ Start registering students and taking attendance

If any checks fail:
1. Review the error in the failing check
2. Check [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for solutions
3. Check logs in terminal
4. Review browser DevTools for errors
5. Consult [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for troubleshooting

---

**Verification Date:** _______________  
**System Version:** 1.0  
**Integration Status:** ✅ Complete
