package com.attendance.controller;

import com.attendance.service.ApiService;
import com.attendance.util.Logger;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.concurrent.Task;
import javafx.embed.swing.SwingFXUtils;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.control.*;
import javafx.scene.image.ImageView;
import javafx.scene.image.WritableImage;
import javafx.scene.paint.Color;
import javafx.scene.text.Font;
import javafx.scene.input.MouseEvent;
import org.opencv.core.*;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import org.opencv.objdetect.CascadeClassifier;
import org.opencv.videoio.VideoCapture;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.net.URL;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class LiveAttendanceController implements Initializable {
    
    // FXML Components
    @FXML private ImageView cameraView;
    @FXML private Canvas overlayCanvas;
    @FXML private Button startButton;
    @FXML private Button stopButton;
    @FXML private Button markPresentButton;
    @FXML private Label statusLabel;
    @FXML private Label fpsLabel;
    @FXML private Label facesLabel;
    @FXML private ListView<String> recognizedList;
    @FXML private Label countLabel;
    
    // OpenCV Components
    private VideoCapture videoCapture;
    private CascadeClassifier faceCascade;
    private ScheduledExecutorService cameraTimer;
    private ScheduledFuture<?> cameraTask;
    
    // Face Detection Variables
    private Mat currentFrame;
    private MatOfRect faceDetections;
    private List<FaceBox> detectedFaces;
    private Set<Integer> recognizedStudentIds;
    
    // UI State
    private ObservableList<String> recognizedStudents;
    private boolean isCameraActive = false;
    private int frameCount = 0;
    private long startTime = 0;
    private ApiService apiService;
    
    // Constants
    private static final double CAMERA_WIDTH = 640;
    private static final double CAMERA_HEIGHT = 480;
    private static final int FPS_UPDATE_INTERVAL = 30; // Update FPS every 30 frames
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        // Initialize OpenCV
        try {
            nu.pattern.OpenCV.loadLocally();
            Logger.info("OpenCV loaded successfully for LiveAttendance");
            Logger.info("OpenCV version: " + Core.VERSION);
        } catch (Exception e) {
            Logger.error("Failed to load OpenCV for LiveAttendance: " + e.getMessage());
            e.printStackTrace();
            // Continue initialization but disable camera functionality
        }
        
        // Initialize components
        initializeComponents();
        setupEventHandlers();
        loadFaceCascade();
        
        // Initialize API service
        apiService = new ApiService();
        
        // Test camera availability
        testCameraAvailability();
    }
    
    private void testCameraAvailability() {
        try {
            VideoCapture testCapture = new VideoCapture(0);
            if (testCapture.isOpened()) {
                Logger.info("Camera is available and accessible");
                testCapture.release();
            } else {
                Logger.warn("Camera is not accessible - may be in use by another application");
            }
        } catch (Exception e) {
            Logger.error("Error testing camera availability: " + e.getMessage());
        }
    }
    
    private void initializeComponents() {
        // Initialize collections
        recognizedStudents = FXCollections.observableArrayList();
        recognizedList.setItems(recognizedStudents);
        recognizedStudentIds = new HashSet<>();
        detectedFaces = new ArrayList<>();
        
        // Initialize OpenCV objects
        faceDetections = new MatOfRect();
        
        // Initialize executor service
        cameraTimer = Executors.newScheduledThreadPool(2);
        
        // Configure ImageView and Canvas
        if (cameraView != null) {
            cameraView.setPreserveRatio(true);
            cameraView.setFitWidth(CAMERA_WIDTH);
            cameraView.setFitHeight(CAMERA_HEIGHT);
            Logger.info("Camera view configured - Width: " + CAMERA_WIDTH + ", Height: " + CAMERA_HEIGHT);
        }
        
        if (overlayCanvas != null) {
            overlayCanvas.setWidth(CAMERA_WIDTH);
            overlayCanvas.setHeight(CAMERA_HEIGHT);
            Logger.info("Overlay canvas configured - Width: " + CAMERA_WIDTH + ", Height: " + CAMERA_HEIGHT);
        }
        
        // Set initial UI state
        updateUI();
    }
    
    private void setupEventHandlers() {
        // Canvas click handler for face selection
        overlayCanvas.setOnMouseClicked(this::handleCanvasClick);
    }
    
    private void loadFaceCascade() {
        try {
            // Try to load cascade from resources
            String cascadePath = "/haarcascades/haarcascade_frontalface_alt.xml";
            URL cascadeUrl = getClass().getResource(cascadePath);
            
            if (cascadeUrl != null) {
                // Convert URL to proper file path, handling Windows path issues
                String cascadeFile = cascadeUrl.getPath();
                // Remove leading slash on Windows if present
                if (cascadeFile.startsWith("/") && cascadeFile.contains(":")) {
                    cascadeFile = cascadeFile.substring(1);
                }
                
                faceCascade = new CascadeClassifier(cascadeFile);
                if (!faceCascade.empty()) {
                    Logger.info("Face cascade loaded successfully from: " + cascadeFile);
                } else {
                    // Try alternative approach with resource stream
                    faceCascade = new CascadeClassifier();
                    Logger.warn("Face cascade file found but failed to load - face detection disabled");
                }
            } else {
                // Create empty classifier as fallback
                faceCascade = new CascadeClassifier();
                Logger.warn("Face cascade not found in resources - face detection disabled");
            }
        } catch (Exception e) {
            faceCascade = new CascadeClassifier();
            Logger.error("Error loading face cascade: " + e.getMessage());
        }
    }
    
    @FXML
    private void handleStartCamera() {
        if (!isCameraActive) {
            startCamera();
        }
    }
    
    @FXML
    private void handleStopCamera() {
        if (isCameraActive) {
            stopCamera();
        }
    }
    
    @FXML
    private void handleMarkPresent() {
        // Mark all recognized students as present
        if (!recognizedStudentIds.isEmpty()) {
            Task<Void> markAttendanceTask = new Task<Void>() {
                @Override
                protected Void call() throws Exception {
                    for (Integer studentId : recognizedStudentIds) {
                        apiService.markAttendance(studentId);
                    }
                    return null;
                }
                
                @Override
                protected void succeeded() {
                    Platform.runLater(() -> {
                        showAlert("Success", "Attendance marked for " + recognizedStudentIds.size() + " students");
                    });
                }
                
                @Override
                protected void failed() {
                    Platform.runLater(() -> {
                        showAlert("Error", "Failed to mark attendance: " + getException().getMessage());
                    });
                }
            };
            
            new Thread(markAttendanceTask).start();
        }
    }
    
    private void startCamera() {
        try {
            Logger.info("Attempting to start camera...");
            videoCapture = new VideoCapture(0);
            
            if (!videoCapture.isOpened()) {
                Logger.error("Camera could not be opened");
                showAlert("Camera Error", "Cannot access camera. Please check camera connection.");
                return;
            }
            
            // Set camera properties
            videoCapture.set(3, CAMERA_WIDTH);  // Width
            videoCapture.set(4, CAMERA_HEIGHT); // Height
            
            Logger.info("Camera properties set - Width: " + CAMERA_WIDTH + ", Height: " + CAMERA_HEIGHT);
            
            isCameraActive = true;
            startTime = System.currentTimeMillis();
            frameCount = 0;
            
            // Start camera capture task
            cameraTask = cameraTimer.scheduleAtFixedRate(this::updateCamera, 0, 33, TimeUnit.MILLISECONDS);
            
            updateUI();
            updateStatus("Camera started successfully");
            Logger.info("Camera started and capture task scheduled");
            
        } catch (Exception e) {
            showAlert("Error", "Failed to start camera: " + e.getMessage());
        }
    }
    
    private void stopCamera() {
        try {
            isCameraActive = false;
            
            if (cameraTask != null && !cameraTask.isCancelled()) {
                cameraTask.cancel(true);
            }
            
            if (videoCapture != null && videoCapture.isOpened()) {
                videoCapture.release();
            }
            
            // Clear displays
            Platform.runLater(() -> {
                cameraView.setImage(null);
                clearCanvas();
                detectedFaces.clear();
                updateFaceCount();
            });
            
            updateUI();
            updateStatus("Camera stopped");
            
        } catch (Exception e) {
            showAlert("Error", "Error stopping camera: " + e.getMessage());
        }
    }
    
    private void updateCamera() {
        if (!isCameraActive || videoCapture == null || !videoCapture.isOpened()) {
            return;
        }
        
        try {
            currentFrame = new Mat();
            if (videoCapture.read(currentFrame) && !currentFrame.empty()) {
                
                // Log frame info occasionally for debugging
                if (frameCount % 100 == 0) {
                    Logger.info("Frame captured - Size: " + currentFrame.cols() + "x" + currentFrame.rows());
                }
                
                // Detect faces
                detectFaces();
                
                // Convert frame to JavaFX image
                WritableImage fxImage = matToWritableImage(currentFrame);
                
                if (fxImage != null) {
                    Platform.runLater(() -> {
                        // Update camera view
                        cameraView.setImage(fxImage);
                        
                        // Draw face overlays
                        drawFaceOverlays();
                        
                        // Update FPS counter
                        frameCount++;
                        if (frameCount % FPS_UPDATE_INTERVAL == 0) {
                            updateFPS();
                        }
                        
                        // Update face count
                        updateFaceCount();
                    });
                } else {
                    Logger.warn("Failed to convert frame to JavaFX image");
                }
            } else {
                if (frameCount % 100 == 0) {
                    Logger.warn("Failed to read frame from camera or frame is empty");
                }
            }
        } catch (Exception e) {
            Logger.error("Camera update error: " + e.getMessage());
            Platform.runLater(() -> updateStatus("Camera error: " + e.getMessage()));
        }
    }
    
    private void detectFaces() {
        if (currentFrame == null || currentFrame.empty() || faceCascade.empty()) {
            detectedFaces.clear();
            return;
        }
        
        try {
            Mat grayFrame = new Mat();
            Imgproc.cvtColor(currentFrame, grayFrame, Imgproc.COLOR_BGR2GRAY);
            Imgproc.equalizeHist(grayFrame, grayFrame);
            
            faceCascade.detectMultiScale(grayFrame, faceDetections, 1.1, 3, 0, new Size(30, 30), new Size());
            
            Rect[] faces = faceDetections.toArray();
            detectedFaces.clear();
            
            for (int i = 0; i < faces.length; i++) {
                FaceBox faceBox = new FaceBox(i, faces[i]);
                detectedFaces.add(faceBox);
            }
            
        } catch (Exception e) {
            System.err.println("Face detection error: " + e.getMessage());
            detectedFaces.clear();
        }
    }
    
    private void drawFaceOverlays() {
        GraphicsContext gc = overlayCanvas.getGraphicsContext2D();
        gc.clearRect(0, 0, overlayCanvas.getWidth(), overlayCanvas.getHeight());
        
        for (FaceBox faceBox : detectedFaces) {
            drawFaceBox(gc, faceBox);
        }
    }
    
    private void drawFaceBox(GraphicsContext gc, FaceBox faceBox) {
        // Set colors based on face state
        Color boxColor;
        Color textColor = Color.WHITE;
        String status = "";
        
        switch (faceBox.getState()) {
            case DETECTED:
                boxColor = Color.LIGHTGREEN;
                status = "Click to identify";
                break;
            case PROCESSING:
                boxColor = Color.YELLOW;
                status = "Processing...";
                break;
            case RECOGNIZED:
                boxColor = Color.GREEN;
                status = faceBox.getRecognizedName();
                break;
            case UNKNOWN:
                boxColor = Color.RED;
                status = "Unknown";
                break;
            default:
                boxColor = Color.LIGHTGREEN;
                status = "Click to identify";
        }
        
        // Draw face rectangle
        gc.setStroke(boxColor);
        gc.setLineWidth(3);
        gc.strokeRect(faceBox.getX(), faceBox.getY(), faceBox.getWidth(), faceBox.getHeight());
        
        // Draw semi-transparent background for text
        gc.setFill(Color.rgb(0, 0, 0, 0.7));
        gc.fillRect(faceBox.getX(), faceBox.getY() - 25, faceBox.getWidth(), 25);
        
        // Draw status text
        gc.setFill(textColor);
        gc.setFont(Font.font(12));
        gc.fillText(status, faceBox.getX() + 5, faceBox.getY() - 8);
    }
    
    private void handleCanvasClick(MouseEvent event) {
        if (!isCameraActive) return;
        
        double clickX = event.getX();
        double clickY = event.getY();
        
        // Find clicked face
        for (FaceBox faceBox : detectedFaces) {
            if (faceBox.contains(clickX, clickY) && faceBox.getState() == FaceState.DETECTED) {
                recognizeFace(faceBox);
                break;
            }
        }
    }
    
    private void recognizeFace(FaceBox faceBox) {
        if (currentFrame == null || currentFrame.empty()) return;
        
        faceBox.setState(FaceState.PROCESSING);
        
        Task<String> recognitionTask = new Task<String>() {
            @Override
            protected String call() throws Exception {
                // Extract face region
                Rect faceRect = faceBox.getRect();
                Mat faceImage = new Mat(currentFrame, faceRect);
                
                // Convert to base64
                MatOfByte matOfByte = new MatOfByte();
                Imgcodecs.imencode(".jpg", faceImage, matOfByte);
                byte[] byteArray = matOfByte.toArray();
                String base64Image = Base64.getEncoder().encodeToString(byteArray);
                
                // Send to backend for recognition
                return apiService.recognizeSingleFace(base64Image);
            }
            
            @Override
            protected void succeeded() {
                String result = getValue();
                Platform.runLater(() -> handleRecognitionResult(faceBox, result));
            }
            
            @Override
            protected void failed() {
                Platform.runLater(() -> {
                    faceBox.setState(FaceState.UNKNOWN);
                    updateStatus("Recognition failed: " + getException().getMessage());
                });
            }
        };
        
        new Thread(recognitionTask).start();
    }
    
    private void handleRecognitionResult(FaceBox faceBox, String result) {
        try {
            if (result != null && !result.trim().isEmpty() && !result.equals("Unknown")) {
                // Parse result (assuming it contains student info)
                faceBox.setState(FaceState.RECOGNIZED);
                faceBox.setRecognizedName(result);
                
                // Add to recognized list if not already present
                String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
                String listItem = result + " (" + timestamp + ")";
                
                if (!recognizedStudents.contains(listItem)) {
                    recognizedStudents.add(listItem);
                    // Extract student ID if possible and add to set
                    // This depends on your backend response format
                }
                
                updateRecognitionCount();
                updateStatus("Recognized: " + result);
            } else {
                faceBox.setState(FaceState.UNKNOWN);
                updateStatus("Person not recognized");
            }
        } catch (Exception e) {
            faceBox.setState(FaceState.UNKNOWN);
            updateStatus("Error processing recognition result");
        }
    }
    
    // Utility Methods
    private WritableImage matToWritableImage(Mat mat) {
        try {
            if (mat == null || mat.empty()) {
                Logger.warn("Cannot convert null or empty Mat to WritableImage");
                return null;
            }
            
            MatOfByte matOfByte = new MatOfByte();
            boolean encoded = Imgcodecs.imencode(".png", mat, matOfByte);
            
            if (!encoded) {
                Logger.error("Failed to encode Mat to PNG");
                return null;
            }
            
            byte[] byteArray = matOfByte.toArray();
            
            if (byteArray.length == 0) {
                Logger.error("Encoded image byte array is empty");
                return null;
            }
            
            java.io.ByteArrayInputStream bis = new java.io.ByteArrayInputStream(byteArray);
            BufferedImage bufferedImage = javax.imageio.ImageIO.read(bis);
            
            if (bufferedImage == null) {
                Logger.error("Failed to create BufferedImage from byte array");
                return null;
            }
            
            WritableImage fxImage = SwingFXUtils.toFXImage(bufferedImage, null);
            
            if (fxImage == null) {
                Logger.error("Failed to convert BufferedImage to WritableImage");
                return null;
            }
            
            return fxImage;
        } catch (Exception e) {
            Logger.error("Error converting Mat to WritableImage: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }
    
    private void clearCanvas() {
        GraphicsContext gc = overlayCanvas.getGraphicsContext2D();
        gc.clearRect(0, 0, overlayCanvas.getWidth(), overlayCanvas.getHeight());
    }
    
    private void updateUI() {
        Platform.runLater(() -> {
            startButton.setDisable(isCameraActive);
            stopButton.setDisable(!isCameraActive);
            markPresentButton.setDisable(!isCameraActive || recognizedStudentIds.isEmpty());
        });
    }
    
    private void updateStatus(String message) {
        Platform.runLater(() -> statusLabel.setText(message));
    }
    
    private void updateFPS() {
        if (startTime > 0) {
            long currentTime = System.currentTimeMillis();
            double fps = (frameCount * 1000.0) / (currentTime - startTime);
            Platform.runLater(() -> fpsLabel.setText(String.format("FPS: %.1f", fps)));
        }
    }
    
    private void updateFaceCount() {
        Platform.runLater(() -> facesLabel.setText("Faces Detected: " + detectedFaces.size()));
    }
    
    private void updateRecognitionCount() {
        Platform.runLater(() -> countLabel.setText("Total: " + recognizedStudents.size()));
    }
    
    private void showAlert(String title, String message) {
        Platform.runLater(() -> {
            Alert alert = new Alert(Alert.AlertType.INFORMATION);
            alert.setTitle(title);
            alert.setHeaderText(null);
            alert.setContentText(message);
            alert.showAndWait();
        });
    }
    
    public void cleanup() {
        stopCamera();
        if (cameraTimer != null && !cameraTimer.isShutdown()) {
            cameraTimer.shutdown();
        }
    }
    
    // Inner Classes
    private static class FaceBox {
        private final int id;
        private final Rect rect;
        private FaceState state;
        private String recognizedName;
        
        public FaceBox(int id, Rect rect) {
            this.id = id;
            this.rect = rect;
            this.state = FaceState.DETECTED;
            this.recognizedName = "";
        }
        
        public boolean contains(double x, double y) {
            return x >= rect.x && x <= rect.x + rect.width &&
                   y >= rect.y && y <= rect.y + rect.height;
        }
        
        // Getters and setters
        public int getId() { return id; }
        public Rect getRect() { return rect; }
        public double getX() { return rect.x; }
        public double getY() { return rect.y; }
        public double getWidth() { return rect.width; }
        public double getHeight() { return rect.height; }
        public FaceState getState() { return state; }
        public void setState(FaceState state) { this.state = state; }
        public String getRecognizedName() { return recognizedName; }
        public void setRecognizedName(String name) { this.recognizedName = name; }
    }
    
    private enum FaceState {
        DETECTED,    // Face detected, ready to be clicked
        PROCESSING,  // Recognition in progress
        RECOGNIZED,  // Successfully recognized
        UNKNOWN      // Recognition failed
    }
}
