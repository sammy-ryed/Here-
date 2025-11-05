package com.attendance.service;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.attendance.model.AttendanceResult;
import com.attendance.model.Student;
import com.attendance.util.ConfigManager;
import com.attendance.util.Logger;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import javafx.scene.image.Image;

/**
 * Service for communicating with Python backend API
 */
public class ApiService {
    
    private final String baseUrl;
    private final Gson gson;
    private static final int TIMEOUT = 120000; // 120 seconds (2 minutes) - for face embedding processing
    private static final int REGISTER_TIMEOUT = 300000; // 300 seconds (5 minutes) - for student registration with multiple photos
    private static final int CONNECT_TIMEOUT = 10000; // 10 seconds for initial connection
    
    public ApiService() {
        this.baseUrl = ConfigManager.getProperty("api.base.url", "http://localhost:5000");
        this.gson = new Gson();
        Logger.info("ApiService initialized with base URL: " + baseUrl);
    }
    
    /**
     * Check if backend is healthy
     */
    public boolean checkHealth() {
        try {
            URL url = new URL(baseUrl + "/health");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(CONNECT_TIMEOUT);
            conn.setReadTimeout(CONNECT_TIMEOUT);
            
            int responseCode = conn.getResponseCode();
            conn.disconnect();
            
            return responseCode == 200;
            
        } catch (Exception e) {
            Logger.error("Health check failed: " + e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Register a new student with face images
     */
    public boolean registerStudent(String name, String rollNo, List<File> images) {
        try {
            String endpoint = baseUrl + "/register_face";
            String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
            
            URL url = new URL(endpoint);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            conn.setConnectTimeout(CONNECT_TIMEOUT);
            conn.setReadTimeout(REGISTER_TIMEOUT); // Use longer timeout for registration (5 minutes for multiple photos)
            
            try (OutputStream os = conn.getOutputStream();
                 OutputStreamWriter writer = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                
                // Add name field
                writer.write("--" + boundary + "\r\n");
                writer.write("Content-Disposition: form-data; name=\"name\"\r\n\r\n");
                writer.write(name + "\r\n");
                
                // Add roll_no field
                writer.write("--" + boundary + "\r\n");
                writer.write("Content-Disposition: form-data; name=\"roll_no\"\r\n\r\n");
                writer.write(rollNo + "\r\n");
                
                writer.flush();
                
                // Add image files
                for (File image : images) {
                    writer.write("--" + boundary + "\r\n");
                    writer.write("Content-Disposition: form-data; name=\"images\"; filename=\"" + 
                                image.getName() + "\"\r\n");
                    writer.write("Content-Type: image/jpeg\r\n\r\n");
                    writer.flush();
                    
                    try (FileInputStream fis = new FileInputStream(image)) {
                        byte[] buffer = new byte[4096];
                        int bytesRead;
                        while ((bytesRead = fis.read(buffer)) != -1) {
                            os.write(buffer, 0, bytesRead);
                        }
                    }
                    
                    writer.write("\r\n");
                    writer.flush();
                }
                
                // End boundary
                writer.write("--" + boundary + "--\r\n");
                writer.flush();
            }
            
            int responseCode = conn.getResponseCode();
            String response = readResponse(conn);
            
            Logger.info("Register response (" + responseCode + "): " + response);
            
            conn.disconnect();
            return responseCode == 201;
            
        } catch (Exception e) {
            Logger.error("Error registering student: " + e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Process attendance from classroom photo
     */
    public AttendanceResult processAttendance(File image) {
        try {
            String endpoint = baseUrl + "/process_attendance";
            String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
            
            URL url = new URL(endpoint);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            conn.setConnectTimeout(TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            try (OutputStream os = conn.getOutputStream();
                 OutputStreamWriter writer = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                
                // Add class_name field
                writer.write("--" + boundary + "\r\n");
                writer.write("Content-Disposition: form-data; name=\"class_name\"\r\n\r\n");
                writer.write("default\r\n");
                
                // Add image file
                writer.write("--" + boundary + "\r\n");
                writer.write("Content-Disposition: form-data; name=\"image\"; filename=\"" + 
                            image.getName() + "\"\r\n");
                writer.write("Content-Type: image/jpeg\r\n\r\n");
                writer.flush();
                
                try (FileInputStream fis = new FileInputStream(image)) {
                    byte[] buffer = new byte[4096];
                    int bytesRead;
                    while ((bytesRead = fis.read(buffer)) != -1) {
                        os.write(buffer, 0, bytesRead);
                    }
                }
                
                writer.write("\r\n");
                writer.write("--" + boundary + "--\r\n");
                writer.flush();
            }
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                String response = readResponse(conn);
                AttendanceResult result = parseAttendanceResult(response);
                Logger.info("Attendance processed: " + result);
                conn.disconnect();
                return result;
            } else {
                String error = readResponse(conn);
                Logger.error("Attendance processing failed (" + responseCode + "): " + error);
                conn.disconnect();
                return null;
            }
            
        } catch (Exception e) {
            Logger.error("Error processing attendance: " + e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * Process attendance from multiple photos (batch processing)
     */
    public AttendanceResult processAttendanceBatch(List<File> images) {
        try {
            String endpoint = baseUrl + "/process_attendance_batch";
            String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
            
            URL url = new URL(endpoint);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            conn.setConnectTimeout(TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            try (OutputStream os = conn.getOutputStream();
                 OutputStreamWriter writer = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                
                // Add class_name field
                writer.write("--" + boundary + "\r\n");
                writer.write("Content-Disposition: form-data; name=\"class_name\"\r\n\r\n");
                writer.write("default\r\n");
                writer.flush();
                
                // Add each image file
                for (File image : images) {
                    writer.write("--" + boundary + "\r\n");
                    writer.write("Content-Disposition: form-data; name=\"images\"; filename=\"" + 
                                image.getName() + "\"\r\n");
                    writer.write("Content-Type: image/jpeg\r\n\r\n");
                    writer.flush();
                    
                    try (FileInputStream fis = new FileInputStream(image)) {
                        byte[] buffer = new byte[4096];
                        int bytesRead;
                        while ((bytesRead = fis.read(buffer)) != -1) {
                            os.write(buffer, 0, bytesRead);
                        }
                    }
                    
                    writer.write("\r\n");
                    writer.flush();
                }
                
                writer.write("--" + boundary + "--\r\n");
                writer.flush();
            }
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                String response = readResponse(conn);
                AttendanceResult result = parseAttendanceResult(response);
                Logger.info("Batch attendance processed: " + images.size() + " photos, " + result);
                conn.disconnect();
                return result;
            } else {
                String error = readResponse(conn);
                Logger.error("Batch attendance processing failed (" + responseCode + "): " + error);
                conn.disconnect();
                return null;
            }
            
        } catch (Exception e) {
            Logger.error("Error processing batch attendance: " + e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * Get all registered students
     */
    public List<Student> getAllStudents() {
        try {
            URL url = new URL(baseUrl + "/students");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                String response = readResponse(conn);
                List<Student> students = parseStudentsList(response);
                Logger.info("Retrieved " + students.size() + " students");
                conn.disconnect();
                return students;
            } else {
                Logger.error("Failed to get students: " + responseCode);
                conn.disconnect();
                return new ArrayList<>();
            }
            
        } catch (Exception e) {
            Logger.error("Error getting students: " + e.getMessage(), e);
            return new ArrayList<>();
        }
    }
    
    /**
     * Get dashboard statistics including today's attendance
     */
    public com.attendance.model.DashboardStats getDashboardStats() {
        try {
            URL url = new URL(baseUrl + "/dashboard/stats");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                String response = readResponse(conn);
                com.attendance.model.DashboardStats stats = parseDashboardStats(response);
                Logger.info("Retrieved dashboard stats: " + stats);
                conn.disconnect();
                return stats;
            } else {
                Logger.error("Failed to get dashboard stats: " + responseCode);
                conn.disconnect();
                return null;
            }
            
        } catch (Exception e) {
            Logger.error("Error getting dashboard stats: " + e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * Get unrecognized face image
     */
    public Image getUnrecognizedFaceImage(String filename) {
        try {
            URL url = new URL(baseUrl + "/unrecognized/" + filename);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                InputStream is = conn.getInputStream();
                Image image = new Image(is);
                is.close();
                conn.disconnect();
                return image;
            } else {
                Logger.error("Failed to get unrecognized face: " + responseCode);
                conn.disconnect();
                return null;
            }
            
        } catch (Exception e) {
            Logger.error("Error getting unrecognized face: " + e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * Clear all attendance records for today
     * @return true if successful, false otherwise
     */
    public boolean clearTodayAttendance() {
        try {
            URL url = new URL(baseUrl + "/attendance/clear-today");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setConnectTimeout(CONNECT_TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            conn.setRequestProperty("Content-Type", "application/json");
            
            int responseCode = conn.getResponseCode();
            String response = readResponse(conn);
            conn.disconnect();
            
            if (responseCode == 200) {
                Logger.info("Today's attendance cleared successfully");
                return true;
            } else {
                Logger.error("Failed to clear today's attendance: " + response);
                return false;
            }
            
        } catch (Exception e) {
            Logger.error("Error clearing today's attendance: " + e.getMessage(), e);
            return false;
        }
    }
    
    private String readResponse(HttpURLConnection conn) throws IOException {
        InputStream is = conn.getResponseCode() < 400 ? conn.getInputStream() : conn.getErrorStream();
        BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        reader.close();
        return response.toString();
    }
    
    private AttendanceResult parseAttendanceResult(String json) {
        AttendanceResult result = new AttendanceResult();
        
        try {
            JsonObject obj = gson.fromJson(json, JsonObject.class);
            
            // Parse present students
            JsonArray presentArray = obj.getAsJsonArray("present");
            List<Student> presentList = new ArrayList<>();
            for (int i = 0; i < presentArray.size(); i++) {
                JsonObject studentObj = presentArray.get(i).getAsJsonObject();
                Student student = new Student(
                    studentObj.get("id").getAsInt(),
                    studentObj.get("name").getAsString(),
                    studentObj.get("roll_no").getAsString(),
                    studentObj.get("confidence").getAsDouble()
                );
                presentList.add(student);
            }
            result.setPresentStudents(presentList);
            
            // Parse absent students
            JsonArray absentArray = obj.getAsJsonArray("absent");
            List<Student> absentList = new ArrayList<>();
            for (int i = 0; i < absentArray.size(); i++) {
                JsonObject studentObj = absentArray.get(i).getAsJsonObject();
                Student student = new Student(
                    studentObj.get("id").getAsInt(),
                    studentObj.get("name").getAsString(),
                    studentObj.get("roll_no").getAsString()
                );
                absentList.add(student);
            }
            result.setAbsentStudents(absentList);
            
            // Parse unrecognized faces
            JsonArray unrecognizedArray = obj.getAsJsonArray("unrecognized");
            List<String> unrecognizedList = new ArrayList<>();
            for (int i = 0; i < unrecognizedArray.size(); i++) {
                unrecognizedList.add(unrecognizedArray.get(i).getAsString());
            }
            result.setUnrecognizedFaces(unrecognizedList);
            
            // Get total faces
            result.setTotalFaces(obj.get("total_faces").getAsInt());
            
            // Get timestamp
            if (obj.has("timestamp")) {
                result.setTimestamp(obj.get("timestamp").getAsString());
            }
            
        } catch (Exception e) {
            Logger.error("Error parsing attendance result: " + e.getMessage(), e);
        }
        
        return result;
    }
    
    private List<Student> parseStudentsList(String json) {
        List<Student> students = new ArrayList<>();
        
        try {
            JsonObject obj = gson.fromJson(json, JsonObject.class);
            JsonArray studentsArray = obj.getAsJsonArray("students");
            
            for (int i = 0; i < studentsArray.size(); i++) {
                JsonObject studentObj = studentsArray.get(i).getAsJsonObject();
                Student student = new Student(
                    studentObj.get("id").getAsInt(),
                    studentObj.get("name").getAsString(),
                    studentObj.get("roll_no").getAsString()
                );
                students.add(student);
            }
            
        } catch (Exception e) {
            Logger.error("Error parsing students list: " + e.getMessage(), e);
        }
        
        return students;
    }
    
    private com.attendance.model.DashboardStats parseDashboardStats(String json) {
        com.attendance.model.DashboardStats stats = new com.attendance.model.DashboardStats();
        
        try {
            JsonObject obj = gson.fromJson(json, JsonObject.class);
            
            stats.setTotalStudents(obj.get("total_students").getAsInt());
            stats.setPresentToday(obj.get("present_today").getAsInt());
            stats.setAbsentToday(obj.get("absent_today").getAsInt());
            stats.setAttendanceRate(obj.get("attendance_rate").getAsDouble());
            stats.setDate(obj.get("date").getAsString());
            
            // Parse students list with attendance status
            List<Student> students = new ArrayList<>();
            JsonArray studentsArray = obj.getAsJsonArray("students");
            
            for (int i = 0; i < studentsArray.size(); i++) {
                JsonObject studentObj = studentsArray.get(i).getAsJsonObject();
                Student student = new Student(
                    studentObj.get("id").getAsInt(),
                    studentObj.get("name").getAsString(),
                    studentObj.get("roll_no").getAsString()
                );
                
                // Set attendance status if available
                if (studentObj.has("attendance_status")) {
                    student.setAttendanceStatus(studentObj.get("attendance_status").getAsString());
                }
                
                students.add(student);
            }
            
            stats.setStudents(students);
            
        } catch (Exception e) {
            Logger.error("Error parsing dashboard stats: " + e.getMessage(), e);
        }
        
        return stats;
    }
    
    /**
     * Extract faces from an image
     */
    public JsonObject extractFaces(File image) throws Exception {
        String endpoint = baseUrl + "/extract_faces";
        String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
        
        URL url = new URL(endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        conn.setConnectTimeout(TIMEOUT);
        conn.setReadTimeout(TIMEOUT);
        
        try (OutputStream out = conn.getOutputStream();
             OutputStreamWriter writer = new OutputStreamWriter(out, StandardCharsets.UTF_8)) {
            
            // Add image file
            writer.append("--").append(boundary).append("\r\n");
            writer.append("Content-Disposition: form-data; name=\"image\"; filename=\"").append(image.getName()).append("\"\r\n");
            writer.append("Content-Type: image/jpeg\r\n");
            writer.append("\r\n");
            writer.flush();
            
            try (FileInputStream fis = new FileInputStream(image)) {
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = fis.read(buffer)) != -1) {
                    out.write(buffer, 0, bytesRead);
                }
            }
            out.flush();
            
            writer.append("\r\n");
            writer.append("--").append(boundary).append("--\r\n");
            writer.flush();
        }
        
        int responseCode = conn.getResponseCode();
        
        if (responseCode == 200) {
            String response = readResponse(conn);
            conn.disconnect();
            
            JsonObject result = gson.fromJson(response, JsonObject.class);
            Logger.info("Extracted " + result.get("total_faces").getAsInt() + " faces from image");
            return result;
        } else {
            String errorMsg = readResponse(conn);
            conn.disconnect();
            Logger.error("Failed to extract faces: " + errorMsg);
            throw new Exception("Failed to extract faces: " + errorMsg);
        }
    }
    
    /**
     * Add face embedding to existing student
     */
    public boolean addEmbeddingToStudent(int studentId, String faceFilename) throws Exception {
        String endpoint = baseUrl + "/add_embedding/" + studentId;
        
        URL url = new URL(endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setConnectTimeout(TIMEOUT);
        conn.setReadTimeout(TIMEOUT);
        
        // Send face_filename in JSON body
        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("face_filename", faceFilename);
        
        try (OutputStream out = conn.getOutputStream();
             OutputStreamWriter writer = new OutputStreamWriter(out, StandardCharsets.UTF_8)) {
            writer.write(gson.toJson(requestBody));
            writer.flush();
        }
        
        int responseCode = conn.getResponseCode();
        
        if (responseCode == 200) {
            String response = readResponse(conn);
            conn.disconnect();
            
            JsonObject result = gson.fromJson(response, JsonObject.class);
            boolean success = result.get("success").getAsBoolean();
            
            if (success) {
                Logger.info("Added embedding to student ID " + studentId);
            } else {
                Logger.warn("Failed to add embedding to student ID " + studentId);
            }
            
            return success;
        } else {
            String errorMsg = readResponse(conn);
            conn.disconnect();
            Logger.error("Failed to add embedding: " + errorMsg);
            throw new Exception("Failed to add embedding: " + errorMsg);
        }
    }
    
    /**
     * Mark a student's attendance manually
     */
    public boolean markStudentAttendance(int studentId, String status) throws Exception {
        String endpoint = baseUrl + "/attendance/mark";
        
        URL url = new URL(endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setConnectTimeout(TIMEOUT);
        conn.setReadTimeout(TIMEOUT);
        
        // Send request body
        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("student_id", studentId);
        requestBody.addProperty("status", status);
        
        try (OutputStream out = conn.getOutputStream();
             OutputStreamWriter writer = new OutputStreamWriter(out, StandardCharsets.UTF_8)) {
            writer.write(gson.toJson(requestBody));
            writer.flush();
        }
        
        int responseCode = conn.getResponseCode();
        
        if (responseCode == 200) {
            String response = readResponse(conn);
            conn.disconnect();
            
            JsonObject result = gson.fromJson(response, JsonObject.class);
            boolean success = result.get("success").getAsBoolean();
            
            if (success) {
                Logger.info("Marked student ID " + studentId + " as " + status);
            } else {
                Logger.warn("Failed to mark attendance for student ID " + studentId);
            }
            
            return success;
        } else {
            String errorMsg = readResponse(conn);
            conn.disconnect();
            Logger.error("Failed to mark attendance: " + errorMsg);
            throw new Exception("Failed to mark attendance: " + errorMsg);
        }
    }
    
    /**
     * Delete a specific student and their embeddings
     */
    public boolean deleteStudent(int studentId) throws Exception {
        String url = baseUrl + "/students/" + studentId;
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("DELETE");
        conn.setRequestProperty("Content-Type", "application/json");
        
        int responseCode = conn.getResponseCode();
        
        if (responseCode == 200) {
            String response = readResponse(conn);
            conn.disconnect();
            
            JsonObject result = gson.fromJson(response, JsonObject.class);
            boolean success = result.get("success").getAsBoolean();
            
            if (success) {
                Logger.info("Deleted student ID " + studentId);
            }
            
            return success;
        } else {
            String errorMsg = readResponse(conn);
            conn.disconnect();
            Logger.error("Failed to delete student: " + errorMsg);
            throw new Exception("Failed to delete student: " + errorMsg);
        }
    }
    
    /**
     * Clear ALL students and embeddings - DESTRUCTIVE!
     */
    public boolean clearAllStudents() throws Exception {
        String url = baseUrl + "/students/clear-all";
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("DELETE");
        conn.setRequestProperty("Content-Type", "application/json");
        
        int responseCode = conn.getResponseCode();
        
        if (responseCode == 200) {
            String response = readResponse(conn);
            conn.disconnect();
            
            JsonObject result = gson.fromJson(response, JsonObject.class);
            boolean success = result.get("success").getAsBoolean();
            
            if (success) {
                Logger.info("⚠️ ALL STUDENTS AND EMBEDDINGS CLEARED");
            }
            
            return success;
        } else {
            String errorMsg = readResponse(conn);
            conn.disconnect();
            Logger.error("Failed to clear all data: " + errorMsg);
            throw new Exception("Failed to clear all data: " + errorMsg);
        }
    }
    
    /**
     * Recognize a single face from base64 image data
     */
    public String recognizeSingleFace(String base64Image) throws Exception {
        try {
            URL url = new URL(baseUrl + "/recognize/face");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(CONNECT_TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            // Create JSON payload
            JsonObject payload = new JsonObject();
            payload.addProperty("image", base64Image);
            
            // Send request
            try (OutputStream os = conn.getOutputStream();
                 OutputStreamWriter writer = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                writer.write(payload.toString());
                writer.flush();
            }
            
            // Read response
            if (conn.getResponseCode() == HttpURLConnection.HTTP_OK) {
                String response = readResponse(conn);
                conn.disconnect();
                
                // DEBUG: Log the raw response
                Logger.info("🔍 Backend response: " + response);
                
                JsonObject result = gson.fromJson(response, JsonObject.class);
                
                if (result.has("name") && !result.get("name").isJsonNull()) {
                    String name = result.get("name").getAsString();
                    
                    // Check if attendance was marked
                    boolean attendanceMarked = result.has("attendance_marked") && 
                                              result.get("attendance_marked").getAsBoolean();
                    
                    if (attendanceMarked) {
                        Logger.info("✅ Face recognized: " + name + " - Attendance marked!");
                    } else {
                        Logger.info("Face recognized: " + name);
                    }
                    
                    Logger.info("🎯 Returning name to display: '" + name + "'");
                    return name;
                } else {
                    Logger.info("Face not recognized - 'name' field is null or missing");
                    return "Unknown";
                }
            } else {
                String errorMsg = readResponse(conn);
                conn.disconnect();
                Logger.error("Face recognition failed: " + errorMsg);
                return "Unknown";
            }
            
        } catch (Exception e) {
            Logger.error("Error in face recognition: " + e.getMessage());
            throw new Exception("Face recognition failed: " + e.getMessage());
        }
    }
    
    /**
     * Mark attendance for a specific student
     */
    public boolean markAttendance(int studentId) throws Exception {
        try {
            URL url = new URL(baseUrl + "/attendance/mark");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(CONNECT_TIMEOUT);
            conn.setReadTimeout(TIMEOUT);
            
            // Create JSON payload
            JsonObject payload = new JsonObject();
            payload.addProperty("student_id", studentId);
            
            // Send request
            try (OutputStream os = conn.getOutputStream();
                 OutputStreamWriter writer = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                writer.write(payload.toString());
                writer.flush();
            }
            
            // Read response
            if (conn.getResponseCode() == HttpURLConnection.HTTP_OK) {
                String response = readResponse(conn);
                conn.disconnect();
                
                JsonObject result = gson.fromJson(response, JsonObject.class);
                boolean success = result.get("success").getAsBoolean();
                
                if (success) {
                    Logger.info("Attendance marked for student ID: " + studentId);
                } else {
                    Logger.warn("Failed to mark attendance for student ID: " + studentId);
                }
                
                return success;
            } else {
                String errorMsg = readResponse(conn);
                conn.disconnect();
                Logger.error("Failed to mark attendance: " + errorMsg);
                return false;
            }
            
        } catch (Exception e) {
            Logger.error("Error marking attendance: " + e.getMessage());
            throw new Exception("Failed to mark attendance: " + e.getMessage());
        }
    }
}


