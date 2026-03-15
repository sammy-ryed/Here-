export interface Student {
  id: number;
  name: string;
  roll_no: string;
  section?: string;
  course?: string;
  dept?: string;
  room_no?: string;
  confidence?: number;         // live recognition confidence (current frame)
  attendance_confidence?: number; // stored confidence from last attendance mark
  attendance_status?: 'present' | 'absent' | 'N/A';
  last_attendance?: string;
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
