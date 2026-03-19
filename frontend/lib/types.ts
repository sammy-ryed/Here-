export interface Student {
  id: number;
  name: string;
  roll_no: string;
  section?: string;
  course?: string;
  dept?: string;
  room_no?: string;
  email?: string;
  confidence?: number;
  attendance_confidence?: number; // stored confidence from last attendance mark
  attendance_status?: 'present' | 'absent' | 'N/A';
  last_attendance?: string;
}

export interface User {
  user_id: number;
  username: string;
  role: 'admin' | 'teacher' | 'student';
}

export interface AuthResponse {
  token: string;
  username: string;
  role: string;
  user_id: number;
}

export interface BulkImportStudentResult {
  roll_no: string;
  name: string;
  status: 'success' | 'failed' | 'skipped';
  message: string;
  student_id?: number;
}

export interface BulkImportTokenEntry {
  roll_no: string;
  name: string;
  status: 'pending' | 'failed' | 'skipped';
  message: string;
  token?: string;
  email?: string;
}

export interface BulkImportResult {
  success: boolean;
  mode: 'tokens' | 'drive' | 'mixed';
  total: number;
  // token mode / mixed token portion
  pending?: number;
  tokens?: BulkImportTokenEntry[];
  // drive mode / mixed drive portion
  registered?: number;
  results?: BulkImportStudentResult[];
  failed: number;
  skipped: number;
}

export interface SelfRegisterInfo {
  valid: boolean;
  name: string;
  roll_no: string;
  section?: string;
  course?: string;
  dept?: string;
  room_no?: string;
  email?: string;
  already_registered?: boolean;
}

export interface DashboardStats {
  total_students: number;
  present_today: number;
  absent_today: number;
  attendance_rate: number;
  date: string;
  students?: Student[];
}

export interface AttendanceResult {
  recognized: Student[];
  present: Student[];
  absent: Student[];
  unrecognized: string[];
  total_faces: number;
  message: string;
}

export interface ExtractedFace {
  index: number;
  bbox: [number, number, number, number];
  confidence: number;
  image_base64: string;  // data:image/jpeg;base64,...
  face_filename: string; // temp filename on server
}

export interface ExtractFacesResult {
  faces: ExtractedFace[];
  total_faces: number;
  message?: string;
}

export interface AssignFaceResult {
  success: boolean;
  message: string;
  student_id: number;
  student_name: string;
}

export interface ApiError {
  error: string;
  message?: string;
}

export interface Section {
  id: number;
  name: string;
  year?: string;
  department?: string;
  batch?: string;
}

export interface Subject {
  id: number;
  name: string;
  code: string;
  section_id: number;
}

export interface TeacherSection {
  teacher_id: number;
  section_id: number;
  teacher_name?: string;
  section_name?: string;
}

export interface Session {
  id: number;
  teacher_id: number;
  section_id: number;
  subject_id: number;
  status: 'open' | 'confirmed' | 'voided';
  created_at: string;
  confirmed_at?: string;
  teacher_gps_lat?: number;
  teacher_gps_lon?: number;
}

export interface AttendanceRecord {
  id: number;
  student_id: number;
  date: string;
  status: 'present' | 'absent';
  confidence?: number;
  timestamp: string;
}
