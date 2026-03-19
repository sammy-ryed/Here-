import axios from 'axios';
import { Student, DashboardStats, AttendanceResult, BulkImportResult, ExtractFacesResult, AssignFaceResult } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for face processing
});

// Add authorization header to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses by clearing token
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const apiClient = {
  // Health check
  checkHealth: async (): Promise<boolean> => {
    try {
      const response = await api.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  },

  // Get dashboard stats
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },

  // Get all students
  getStudents: async (): Promise<Student[]> => {
    const response = await api.get<{ students: Student[]; total: number }>('/students');
    return response.data.students;
  },

  // Register new student
  registerStudent: async (name: string, rollNo: string, email: string, images: File[]): Promise<void> => {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('roll_no', rollNo);
    formData.append('email', email);
    images.forEach((image) => {
      formData.append('images', image);
    });

    await api.post('/register_face', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minutes for registration
    });
  },

  // Process attendance (single image)
  processAttendance: async (image: File): Promise<AttendanceResult> => {
    const formData = new FormData();
    formData.append('image', image);

    const response = await api.post<AttendanceResult>('/process_attendance', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Process attendance (multiple images — batch endpoint)
  processBatchAttendance: async (images: File[]): Promise<AttendanceResult> => {
    const formData = new FormData();
    images.forEach((image) => formData.append('images', image));

    const response = await api.post<AttendanceResult>('/process_attendance_batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
    return response.data;
  },

  // Add embeddings for existing student
  addEmbeddings: async (studentId: number, images: File[]): Promise<void> => {
    const formData = new FormData();
    images.forEach((image) => {
      formData.append('images', image);
    });

    await api.post(`/add_embedding/${studentId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
  },

  // Delete student
  deleteStudent: async (studentId: number): Promise<void> => {
    await api.delete(`/students/${studentId}`);
  },

  // Manual attendance marking
  markAttendance: async (studentId: number, status: 'present' | 'absent'): Promise<void> => {
    await api.post('/attendance/mark', {
      student_id: studentId,
      status: status,
    });
  },

  // Bulk import students from Excel + Google Drive links
  bulkImportStudents: async (excelFile: File): Promise<BulkImportResult> => {
    const formData = new FormData();
    formData.append('file', excelFile);
    const response = await api.post<BulkImportResult>('/students/bulk-import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 1800000,
    });
    return response.data;
  },

  // Extract all faces from a group/classroom photo
  extractFaces: async (image: File): Promise<ExtractFacesResult> => {
    const formData = new FormData();
    formData.append('image', image);
    const response = await api.post<ExtractFacesResult>('/extract_faces', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return response.data;
  },

  // Assign an extracted face crop to an existing student
  assignFace: async (studentId: number, faceFilename: string): Promise<AssignFaceResult> => {
    const response = await api.post<AssignFaceResult>(`/assign_face/${studentId}`, {
      face_filename: faceFilename,
    });
    return response.data;
  },

  // Self-registration: get student info from token
  getSelfRegisterInfo: async (token: string) => {
    const response = await api.get<import('./types').SelfRegisterInfo>(`/self-register/${token}`);
    return response.data;
  },

  // Self-registration: submit photos
  submitSelfRegistration: async (token: string, images: File[]) => {
    const formData = new FormData();
    images.forEach((img) => formData.append('images', img));
    const response = await api.post(`/self-register/${token}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
    return response.data;
  },

  // ── AUTHENTICATION ──────────────────────────────────────────
  login: async (username: string, password: string): Promise<{ token: string; username: string; role: string; user_id: number }> => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  // ── ATTENDANCE REPORTS ──────────────────────────────────────
  getAttendanceReport: async (startDate?: string, endDate?: string): Promise<any> => {
    const params = {
      start_date: startDate,
      end_date: endDate,
    };
    const response = await api.get('/attendance/report', { params });
    return response.data;
  },

  clearTodayAttendance: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/attendance/clear-today', {});
    return response.data;
  },

  // ── STUDENT MANAGEMENT ──────────────────────────────────────
  getStudentById: async (studentId: number): Promise<Student> => {
    const response = await api.get<Student>(`/students/${studentId}`);
    return response.data;
  },

  clearAllStudents: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete('/students/clear-all');
    return response.data;
  },

  // ── UNRECOGNIZED FACES ──────────────────────────────────────
  getUnrecognizedFace: async (filename: string): Promise<Blob> => {
    const response = await api.get(`/unrecognized/${filename}`, { responseType: 'blob' });
    return response.data;
  },

  // ── LIVE FACE RECOGNITION ──────────────────────────────────
  recognizeFace: async (base64Image: string): Promise<{ name: string | null; student_id?: number; roll_no?: string; similarity?: number; attendance_marked?: boolean; processing_time_ms?: number }> => {
    const response = await api.post('/recognize/face', { image: base64Image });
    return response.data;
  },

  // ── SECTIONS ────────────────────────────────────────────────
  getSections: async (): Promise<{ sections: any[]; total: number }> => {
    const response = await api.get('/sections');
    return response.data;
  },

  createSection: async (name: string, year?: string, department?: string, batch?: string): Promise<{ success: boolean; section_id: number; name: string }> => {
    const response = await api.post('/sections', { name, year, department, batch });
    return response.data;
  },

  // ── SUBJECTS ────────────────────────────────────────────────
  getSubjects: async (sectionId: number): Promise<{ subjects: any[]; section_id: number; total: number }> => {
    const response = await api.get(`/sections/${sectionId}/subjects`);
    return response.data;
  },

  createSubject: async (name: string, code: string, sectionId: number): Promise<{ success: boolean; subject_id: number }> => {
    const response = await api.post('/subjects', { name, code, section_id: sectionId });
    return response.data;
  },

  // ── TEACHER-SECTION ASSIGNMENTS ────────────────────────────
  getTeacherSections: async (): Promise<{ teacher_sections: any[]; total: number }> => {
    const response = await api.get('/teacher-sections');
    return response.data;
  },

  assignTeacherSection: async (teacherId: number, sectionId: number): Promise<{ success: boolean; teacher_id: number; section_id: number }> => {
    const response = await api.post('/teacher-sections', { teacher_id: teacherId, section_id: sectionId });
    return response.data;
  },

  // ── SESSIONS ────────────────────────────────────────────────
  getSessions: async (): Promise<{ sessions: any[]; total: number }> => {
    const response = await api.get('/sessions');
    return response.data;
  },

  createSession: async (sectionId: number, subjectId: number, gpsLat?: number, gpsLon?: number): Promise<{ success: boolean; session_id: number; status: string }> => {
    const response = await api.post('/sessions', {
      section_id: sectionId,
      subject_id: subjectId,
      teacher_gps_lat: gpsLat,
      teacher_gps_lon: gpsLon,
    });
    return response.data;
  },

  confirmSession: async (sessionId: number): Promise<{ success: boolean; session_id: number; status: string }> => {
    const response = await api.put(`/sessions/${sessionId}/confirm`, {});
    return response.data;
  },

  voidSession: async (sessionId: number): Promise<{ success: boolean; session_id: number; status: string }> => {
    const response = await api.put(`/sessions/${sessionId}/void`, {});
    return response.data;
  },

  // ── STUDENT-SECTION ASSIGNMENT ──────────────────────────────
  updateStudentSection: async (studentId: number, sectionId: number): Promise<{ success: boolean }> => {
    const response = await api.put(`/students/${studentId}/section`, { section_id: sectionId });
    return response.data;
  },
};
