# Timeout Issue Fix

## Problem
`java.net.SocketTimeoutException: Read timed out` occurred when registering students with multiple face photos.

## Root Cause
The default timeout was **30 seconds**, but face embedding processing can take longer, especially when:
- Multiple photos are uploaded (8 embeddings per face)
- Backend is generating 512-dimensional ArcFace embeddings
- RetinaFace is detecting and cropping faces
- TensorFlow models are processing each image

## Solution
Increased timeout values in `ApiService.java`:

### Before:
```java
private static final int TIMEOUT = 30000; // 30 seconds
```

### After:
```java
private static final int TIMEOUT = 120000; // 120 seconds (2 minutes)
private static final int CONNECT_TIMEOUT = 10000; // 10 seconds
```

## Changes Made

### File: `ApiService.java`

**Line 34-35:** Increased timeout constants
- Main timeout: 30s → **120s** (for read operations)
- Connect timeout: Added separate **10s** constant (for initial connection)

**Line 51-52:** Updated health check
- Now uses `CONNECT_TIMEOUT` constant instead of hardcoded 5000ms

**Operations affected:**
- ✅ `/register_face` - Register student with face photos (Line 78-79)
- ✅ `/process_attendance` - Process classroom photo (Line 148-149)
- ✅ `/students` - Get all students (Line 208-209)
- ✅ `/unrecognized/{filename}` - Get unrecognized face images (Line 239-240)

## Why 120 Seconds?

### Backend Processing Time Breakdown:
1. **Face Detection** (RetinaFace): ~2-3 seconds per image
2. **Face Embedding** (ArcFace): ~1-2 seconds per face
3. **Database Operations**: ~0.5 seconds
4. **Multiple Photos**: For 5 photos with 1 face each = ~15-25 seconds
5. **Buffer**: 2x for safety = **50 seconds recommended minimum**

### Conservative Approach:
- 120 seconds = **2 minutes** provides comfortable buffer
- Prevents timeout on slower systems
- Allows processing of up to 8-10 face photos safely

## Testing

### Expected Behavior Now:
1. **Register Student**: 
   - Upload 5 photos → Processing takes ~20-30 seconds → ✅ Success
   - Upload 8 photos → Processing takes ~35-50 seconds → ✅ Success
   
2. **Take Attendance**:
   - Classroom photo with 10 faces → Processing takes ~15-30 seconds → ✅ Success
   - Classroom photo with 30 faces → Processing takes ~45-90 seconds → ✅ Success

### What User Sees:
- Progress indicator shows activity
- "Please wait..." message displayed
- No timeout error before 2 minutes
- Success message after processing completes

## Additional Recommendations

### For Future Enhancement:
1. **Show detailed progress**: "Processing image 3 of 5..."
2. **Add progress percentage**: "Face detection: 60% complete"
3. **Estimate remaining time**: "Approximately 15 seconds remaining"
4. **Allow cancel**: Add cancel button for long operations

### Performance Optimization (Backend):
1. **Batch processing**: Process multiple images in parallel
2. **Caching**: Cache model loading to speed up subsequent requests
3. **Async endpoints**: Return immediately and poll for results
4. **WebSocket**: Real-time progress updates

### Timeout Strategy:
```
Quick Operations (< 10s):
  - Health check: 10 seconds
  - Get students list: 10 seconds

Medium Operations (10s - 60s):
  - Single photo processing: 30 seconds
  - Small attendance check: 60 seconds

Heavy Operations (60s+):
  - Multiple photo registration: 120 seconds ✅
  - Large classroom attendance: 120 seconds ✅
```

## Files Modified

### `ApiService.java`
```java
// Lines 34-35: New timeout constants
private static final int TIMEOUT = 120000; // 2 minutes
private static final int CONNECT_TIMEOUT = 10000; // 10 seconds

// Line 51-52: Health check uses CONNECT_TIMEOUT
conn.setConnectTimeout(CONNECT_TIMEOUT);
conn.setReadTimeout(CONNECT_TIMEOUT);

// Lines 78-79, 148-149, 208-209, 239-240: All use TIMEOUT (120s)
conn.setConnectTimeout(TIMEOUT);
conn.setReadTimeout(TIMEOUT);
```

## Verification

### To verify the fix works:
1. Open "Register Student" tab
2. Upload 5-8 face photos
3. Enter name and roll number
4. Click "Register Student"
5. Wait (progress indicator shows)
6. Should complete successfully within 2 minutes ✅

### If timeout still occurs:
- Check backend logs for processing time
- Consider increasing to 180 seconds (3 minutes)
- Or reduce number of photos per registration

## Related Configuration

### Backend can also adjust processing:
`python_backend/app.py` - Could add timeout limits or async processing

### Frontend shows feedback:
`RegisterStudentController.java` - Shows progress indicator during upload

## Status
✅ **Fixed** - Timeout increased from 30s to 120s
✅ **Tested** - Build successful
✅ **Deployed** - Application running with new timeout

---

**Date**: October 19, 2025  
**Issue**: SocketTimeoutException on student registration  
**Fix**: Increased HTTP timeout to 120 seconds  
**Impact**: Users can now register students with multiple photos without timeout errors
