package com.attendance.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Attendance result model
 */
public class AttendanceResult {
    private List<Student> presentStudents;
    private List<Student> absentStudents;
    private List<String> unrecognizedFaces;
    private int totalFaces;
    private String timestamp;
    
    public AttendanceResult() {
        this.presentStudents = new ArrayList<>();
        this.absentStudents = new ArrayList<>();
        this.unrecognizedFaces = new ArrayList<>();
        this.totalFaces = 0;
    }
    
    // Getters and setters
    public List<Student> getPresentStudents() {
        return presentStudents;
    }
    
    public void setPresentStudents(List<Student> presentStudents) {
        this.presentStudents = presentStudents;
    }
    
    public List<Student> getAbsentStudents() {
        return absentStudents;
    }
    
    public void setAbsentStudents(List<Student> absentStudents) {
        this.absentStudents = absentStudents;
    }
    
    public List<String> getUnrecognizedFaces() {
        return unrecognizedFaces;
    }
    
    public void setUnrecognizedFaces(List<String> unrecognizedFaces) {
        this.unrecognizedFaces = unrecognizedFaces;
    }
    
    public int getTotalFaces() {
        return totalFaces;
    }
    
    public void setTotalFaces(int totalFaces) {
        this.totalFaces = totalFaces;
    }
    
    public String getTimestamp() {
        return timestamp;
    }
    
    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
    
    @Override
    public String toString() {
        return "AttendanceResult{" +
                "present=" + presentStudents.size() +
                ", absent=" + absentStudents.size() +
                ", unrecognized=" + unrecognizedFaces.size() +
                ", totalFaces=" + totalFaces +
                '}';
    }
}
