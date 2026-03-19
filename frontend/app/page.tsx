'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Student, DashboardStats } from '@/lib/types';
import { Users, UserCheck, UserX, TrendingUp, Trash2 } from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  const loadData = async () => {
    try {
      setLoading(true);
      const statsData = await apiClient.getDashboardStats();
      setStats(statsData);
      // Use students from stats if available, otherwise fetch separately
      if (statsData.students && Array.isArray(statsData.students)) {
        setStudents(statsData.students);
      } else {
        const studentsData = await apiClient.getStudents();
        setStudents(Array.isArray(studentsData) ? studentsData : []);
      }
      setError('');
    } catch (err) {
      setError('Failed to load dashboard data. Make sure the backend is running.');
      console.error(err);
      setStudents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStudent = async (studentId: number, studentName: string) => {
    if (confirm(`Are you sure you want to delete ${studentName}?`)) {
      try {
        await apiClient.deleteStudent(studentId);
        await loadData();
      } catch (err) {
        alert('Failed to delete student');
        console.error(err);
      }
    }
  };

  const handleMarkAttendance = async (studentId: number, status: 'present' | 'absent', studentName: string) => {
    try {
      await apiClient.markAttendance(studentId, status);
      await loadData();
    } catch (err) {
      alert(`Failed to mark ${studentName} as ${status}`);
      console.error(err);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Show loading spinner while checking authentication
  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-700">{error}</p>
          <button onClick={loadData} className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-600 mt-1">Overview of attendance metrics and student records</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border border-gray-200 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Students</p>
              <p className="text-2xl font-semibold text-gray-900 mt-2">{stats?.total_students || 0}</p>
            </div>
            <div className="p-2 bg-gray-50">
              <Users className="text-gray-600" size={20} />
            </div>
          </div>
        </div>
        <div className="bg-white border border-gray-200 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Present Today</p>
              <p className="text-2xl font-semibold text-gray-900 mt-2">{stats?.present_today || 0}</p>
            </div>
            <div className="p-2 bg-emerald-50">
              <UserCheck className="text-emerald-600" size={20} />
            </div>
          </div>
        </div>
        <div className="bg-white border border-gray-200 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Absent Today</p>
              <p className="text-2xl font-semibold text-gray-900 mt-2">{stats?.absent_today || 0}</p>
            </div>
            <div className="p-2 bg-red-50">
              <UserX className="text-red-600" size={20} />
            </div>
          </div>
        </div>
        <div className="bg-white border border-gray-200 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Attendance Rate</p>
              <p className="text-2xl font-semibold text-gray-900 mt-2">{stats?.attendance_rate.toFixed(1)}%</p>
            </div>
            <div className="p-2 bg-blue-50">
              <TrendingUp className="text-blue-600" size={20} />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Student Records</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Roll No</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {students.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No students registered yet. Add your first student from the Register page.
                  </td>
                </tr>
              ) : (
                students.map((student) => (
                  <tr key={student.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{student.id}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{student.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{student.roll_no}</td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2.5 py-0.5 text-xs font-medium ${
                          student.attendance_status === 'present' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                          student.attendance_status === 'absent' ? 'bg-red-50 text-red-700 border border-red-200' :
                          'bg-gray-50 text-gray-700 border border-gray-200'
                        }`}>
                          {student.attendance_status || 'N/A'}
                        </span>
                        {student.attendance_confidence != null && (
                          <span
                            className={`text-xs font-mono ${
                              student.attendance_confidence < 0.75
                                ? 'text-amber-600'
                                : 'text-gray-400'
                            }`}
                            title={student.attendance_confidence < 0.75 ? 'Low confidence — verify manually' : 'Recognition confidence'}
                          >
                            {(student.attendance_confidence * 100).toFixed(0)}%
                            {student.attendance_confidence < 0.75 && ' ⚠'}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleMarkAttendance(student.id, 'present', student.name)}
                          className="px-2 py-1 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                          title="Mark Present"
                        >
                          P
                        </button>
                        <button
                          onClick={() => handleMarkAttendance(student.id, 'absent', student.name)}
                          className="px-2 py-1 text-xs bg-red-50 text-red-700 border border-red-200 hover:bg-red-100"
                          title="Mark Absent"
                        >
                          A
                        </button>
                        <button
                          onClick={() => handleDeleteStudent(student.id, student.name)}
                          className="text-gray-500 hover:text-red-600"
                          title="Delete Student"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
