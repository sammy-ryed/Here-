package com.attendance.util;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;

import org.opencv.core.Core;
import org.opencv.core.Mat;
import org.opencv.core.MatOfByte;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.videoio.VideoCapture;

import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.VBox;
import javafx.stage.Modality;
import javafx.stage.Stage;

/**
 * Camera capture utility using OpenCV
 */
public class CameraCapture {
    
    private static boolean opencvLoaded = false;
    
    static {
        try {
            // Load OpenCV native library
            System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
            opencvLoaded = true;
            Logger.info("OpenCV loaded successfully");
        } catch (UnsatisfiedLinkError e) {
            Logger.error("Failed to load OpenCV library: " + e.getMessage(), e);
            opencvLoaded = false;
        }
    }
    
    /**
     * Capture photo from camera
     */
    public File capturePhoto() {
        if (!opencvLoaded) {
            Logger.error("OpenCV not loaded, cannot capture photo");
            return null;
        }
        
        try {
            int cameraIndex = ConfigManager.getIntProperty("camera.device.index", 0);
            VideoCapture camera = new VideoCapture(cameraIndex);
            
            if (!camera.isOpened()) {
                Logger.error("Failed to open camera");
                return null;
            }
            
            // Show camera preview and capture
            File capturedFile = showCameraPreview(camera);
            
            camera.release();
            
            return capturedFile;
            
        } catch (Exception e) {
            Logger.error("Error capturing photo: " + e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * Show camera preview window and capture
     */
    private File showCameraPreview(VideoCapture camera) {
        final File[] capturedFile = {null};
        
        Stage stage = new Stage();
        stage.setTitle("Camera Capture");
        stage.initModality(Modality.APPLICATION_MODAL);
        
        ImageView imageView = new ImageView();
        imageView.setFitWidth(640);
        imageView.setFitHeight(480);
        imageView.setPreserveRatio(true);
        
        Button captureButton = new Button("Capture");
        Button cancelButton = new Button("Cancel");
        
        javafx.scene.layout.HBox buttonBox = new javafx.scene.layout.HBox(10);
        buttonBox.setAlignment(Pos.CENTER);
        buttonBox.getChildren().addAll(captureButton, cancelButton);
        
        VBox layout = new VBox(10);
        layout.setAlignment(Pos.CENTER);
        layout.getChildren().addAll(imageView, buttonBox);
        
        Scene scene = new Scene(layout);
        stage.setScene(scene);
        
        // Start camera preview thread
        Thread previewThread = new Thread(() -> {
            Mat frame = new Mat();
            while (stage.isShowing() && capturedFile[0] == null) {
                if (camera.read(frame) && !frame.empty()) {
                    Image image = mat2Image(frame);
                    javafx.application.Platform.runLater(() -> imageView.setImage(image));
                }
                
                try {
                    Thread.sleep(33); // ~30 FPS
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        previewThread.setDaemon(true);
        previewThread.start();
        
        // Capture button handler
        captureButton.setOnAction(e -> {
            Mat frame = new Mat();
            if (camera.read(frame) && !frame.empty()) {
                try {
                    capturedFile[0] = saveMat(frame);
                    stage.close();
                } catch (IOException ex) {
                    Logger.error("Error saving captured image: " + ex.getMessage(), ex);
                }
            }
        });
        
        // Cancel button handler
        cancelButton.setOnAction(e -> stage.close());
        
        stage.showAndWait();
        
        return capturedFile[0];
    }
    
    /**
     * Convert OpenCV Mat to JavaFX Image
     */
    private Image mat2Image(Mat mat) {
        MatOfByte buffer = new MatOfByte();
        Imgcodecs.imencode(".jpg", mat, buffer);
        return new Image(new ByteArrayInputStream(buffer.toArray()));
    }
    
    /**
     * Save Mat to temporary file
     */
    private File saveMat(Mat mat) throws IOException {
        File tempFile = File.createTempFile("capture_", ".jpg");
        Imgcodecs.imwrite(tempFile.getAbsolutePath(), mat);
        Logger.info("Image captured: " + tempFile.getAbsolutePath());
        return tempFile;
    }
    
    /**
     * Check if camera is available
     */
    public boolean isCameraAvailable() {
        if (!opencvLoaded) {
            return false;
        }
        
        try {
            int cameraIndex = ConfigManager.getIntProperty("camera.device.index", 0);
            VideoCapture camera = new VideoCapture(cameraIndex);
            boolean available = camera.isOpened();
            camera.release();
            return available;
        } catch (Exception e) {
            return false;
        }
    }
}
