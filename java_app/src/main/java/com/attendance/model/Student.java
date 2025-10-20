package com.attendance.model;

/**
 * Student model class
 */
public class Student {
    private int id;
    private String name;
    private String rollNo;
    private double confidence;
    private String attendanceStatus; // "present", "absent", or "N/A"
    
    public Student() {
        this.attendanceStatus = "N/A"; // Default
    }
    
    public Student(int id, String name, String rollNo) {
        this.id = id;
        this.name = name;
        this.rollNo = rollNo;
        this.confidence = 0.0;
        this.attendanceStatus = "N/A"; // Default
    }
    
    public Student(int id, String name, String rollNo, double confidence) {
        this.id = id;
        this.name = name;
        this.rollNo = rollNo;
        this.confidence = confidence;
        this.attendanceStatus = "N/A"; // Default
    }
    
    // Getters and setters
    public int getId() {
        return id;
    }
    
    public void setId(int id) {
        this.id = id;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String getRollNo() {
        return rollNo;
    }
    
    public void setRollNo(String rollNo) {
        this.rollNo = rollNo;
    }
    
    public double getConfidence() {
        return confidence;
    }
    
    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }
    
    public String getAttendanceStatus() {
        return attendanceStatus;
    }
    
    public void setAttendanceStatus(String attendanceStatus) {
        this.attendanceStatus = attendanceStatus;
    }
    
    @Override
    public String toString() {
        return "Student{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", rollNo='" + rollNo + '\'' +
                ", confidence=" + confidence +
                ", attendanceStatus='" + attendanceStatus + '\'' +
                '}';
    }
}
