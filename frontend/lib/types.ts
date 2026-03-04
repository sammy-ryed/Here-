export interface Student {
  id: number;
  name: string;
  roll_no: string;
  confidence?: number;         // live recognition confidence (current frame)
  attendance_confidence?: number; // stored confidence from last attendance mark
  attendance_status?: 'present' | 'absent' | 'N/A';
  last_attendance?: string;
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

export interface ApiError {
  error: string;
  message?: string;
}
