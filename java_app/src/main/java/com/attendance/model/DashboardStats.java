package com.attendance.model;

import java.util.List;

/**
 * Model for dashboard statistics
 */
public class DashboardStats {
    private int totalStudents;
    private int presentToday;
    private int absentToday;
    private double attendanceRate;
    private String date;
    private List<Student> students;
    
    public DashboardStats() {
    }
    
    public int getTotalStudents() {
        return totalStudents;
    }
    
    public void setTotalStudents(int totalStudents) {
        this.totalStudents = totalStudents;
    }
    
    public int getPresentToday() {
        return presentToday;
    }
    
    public void setPresentToday(int presentToday) {
        this.presentToday = presentToday;
    }
    
    public int getAbsentToday() {
        return absentToday;
    }
    
    public void setAbsentToday(int absentToday) {
        this.absentToday = absentToday;
    }
    
    public double getAttendanceRate() {
        return attendanceRate;
    }
    
    public void setAttendanceRate(double attendanceRate) {
        this.attendanceRate = attendanceRate;
    }
    
    public String getDate() {
        return date;
    }
    
    public void setDate(String date) {
        this.date = date;
    }
    
    public List<Student> getStudents() {
        return students;
    }
    
    public void setStudents(List<Student> students) {
        this.students = students;
    }
    
    @Override
    public String toString() {
        return "DashboardStats{" +
                "totalStudents=" + totalStudents +
                ", presentToday=" + presentToday +
                ", absentToday=" + absentToday +
                ", attendanceRate=" + attendanceRate +
                ", date='" + date + '\'' +
                '}';
    }
}
