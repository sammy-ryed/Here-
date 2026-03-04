import axios from 'axios';
import { Student, DashboardStats, AttendanceResult } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for face processing
});

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
  registerStudent: async (name: string, rollNo: string, images: File[]): Promise<void> => {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('roll_no', rollNo);
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

  // Recognize face from base64 image (for live attendance)
  recognizeFace: async (imageBase64: string): Promise<Student | null> => {
    try {
      const response = await api.post<{
        name: string | null;
        student_id?: number;
        roll_no?: string;
        similarity?: number;
      }>('/recognize/face', {
        image: imageBase64,
      });
      
      if (response.data.name && response.data.student_id) {
        return {
          id: response.data.student_id,
          name: response.data.name,
          roll_no: response.data.roll_no || '',
          confidence: response.data.similarity,
        };
      }
      return null;
    } catch {
      return null;
    }
  },

  // Manual attendance marking
  markAttendance: async (studentId: number, status: 'present' | 'absent'): Promise<void> => {
    await api.post('/attendance/mark', {
      student_id: studentId,
      status: status,
    });
  },
};
