package com.attendance.controller;

import java.io.File;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.ResourceBundle;

import com.attendance.service.ApiService;
import com.attendance.util.CameraCapture;
import com.attendance.util.Logger;

import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ListView;
import javafx.scene.control.ProgressBar;
import javafx.scene.control.TextField;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

/**
 * Controller for student registration
 */
public class RegisterStudentController implements Initializable {
    
    @FXML
    private TextField nameField;
    
    @FXML
    private TextField rollNoField;
    
    @FXML
    private ListView<String> photoListView;
    
    @FXML
    private ImageView previewImageView;
    
    @FXML
    private Button uploadButton;
    
    @FXML
    private Button captureButton;
    
    @FXML
    private Button removeButton;
    
    @FXML
    private Button clearButton;
    
    @FXML
    private Button registerButton;
    
    @FXML
    private ProgressBar progressBar;
    
    @FXML
    private Label statusLabel;
    
    private List<File> selectedPhotos = new ArrayList<>();
    private ApiService apiService;
    private CameraCapture cameraCapture;
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        Logger.info("Initializing register student controller");
        
        apiService = new ApiService();
        
        // Try to initialize camera capture (may fail if OpenCV not loaded)
        try {
            cameraCapture = new CameraCapture();
        } catch (Exception e) {
            Logger.warn("Camera capture not available: " + e.getMessage());
            cameraCapture = null;
        }
        
        // Setup UI
        progressBar.setVisible(false);
        
        updateUI();
        
        Logger.info("Register student controller initialized");
    }
    
    @FXML
    private void handleUploadPhotos() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Face Photos");
        fileChooser.getExtensionFilters().addAll(
            new FileChooser.ExtensionFilter("Image Files", "*.jpg", "*.jpeg", "*.png"),
            new FileChooser.ExtensionFilter("All Files", "*.*")
        );
        
        Stage stage = (Stage) nameField.getScene().getWindow();
        List<File> files = fileChooser.showOpenMultipleDialog(stage);
        
        if (files != null && !files.isEmpty()) {
            for (File file : files) {
                if (!selectedPhotos.contains(file)) {
                    selectedPhotos.add(file);
                }
            }
            
            updateStatusLabel("Added " + files.size() + " photo(s)");
            updateUI();
        }
    }
    
    @FXML
    private void handleCapturePhoto() {
        try {
            if (cameraCapture == null) {
                showError("Camera Error", "Camera capture is not available (OpenCV not loaded)");
                return;
            }
            
            updateStatusLabel("Opening camera...");
            File capturedFile = cameraCapture.capturePhoto();
            
            if (capturedFile != null) {
                selectedPhotos.add(capturedFile);
                updateStatusLabel("Photo captured successfully");
                updateUI();
            } else {
                updateStatusLabel("Failed to capture photo");
            }
        } catch (Exception e) {
            Logger.error("Error capturing photo: " + e.getMessage(), e);
            showError("Camera Error", "Failed to capture photo: " + e.getMessage());
        }
    }
    
    @FXML
    private void handleRemovePhoto() {
        // TODO: Implement remove photo functionality
        Logger.info("Remove photo requested");
    }
    
    @FXML
    private void handleClear() {
        selectedPhotos.clear();
        if (nameField != null) nameField.clear();
        if (rollNoField != null) rollNoField.clear();
        updateStatusLabel("Form cleared");
        updateUI();
    }
    
    @FXML
    private void handleRegister() {
        // Validate inputs
        String name = nameField.getText().trim();
        String rollNo = rollNoField.getText().trim();
        
        if (name.isEmpty()) {
            showError("Validation Error", "Please enter student name");
            return;
        }
        
        if (rollNo.isEmpty()) {
            showError("Validation Error", "Please enter roll number");
            return;
        }
        
        if (selectedPhotos.isEmpty()) {
            showError("Validation Error", "Please add at least one photo");
            return;
        }
        
        // Register student
        registerStudent(name, rollNo);
    }
    
    private void registerStudent(String name, String rollNo) {
        progressBar.setVisible(true);
        updateStatusLabel("Registering student...");
        disableControls(true);
        
        new Thread(() -> {
            try {
                boolean success = apiService.registerStudent(name, rollNo, selectedPhotos);
                
                javafx.application.Platform.runLater(() -> {
                    progressBar.setVisible(false);
                    disableControls(false);
                    
                    if (success) {
                        showInfo("Success", "Student registered successfully!");
                        clearForm();
                        updateStatusLabel("Student registered: " + name);
                    } else {
                        showError("Registration Failed", "Failed to register student. Please try again.");
                        updateStatusLabel("Registration failed");
                    }
                });
                
            } catch (Exception e) {
                Logger.error("Error registering student: " + e.getMessage(), e);
                javafx.application.Platform.runLater(() -> {
                    progressBar.setVisible(false);
                    disableControls(false);
                    showError("Error", "Registration error: " + e.getMessage());
                    updateStatusLabel("Error during registration");
                });
            }
        }).start();
    }
    
    private void updatePreview() {
        int selectedIndex = photoListView.getSelectionModel().getSelectedIndex();
        if (selectedIndex >= 0 && selectedIndex < selectedPhotos.size()) {
            File file = selectedPhotos.get(selectedIndex);
            try {
                Image image = new Image(file.toURI().toString());
                previewImageView.setImage(image);
            } catch (Exception e) {
                Logger.error("Error loading preview: " + e.getMessage(), e);
                previewImageView.setImage(null);
            }
        }
    }
    
    private void updateUI() {
        // TODO: Update UI based on state
        // Note: Some fields from original design may not exist in current FXML
        /*
        boolean hasPhotos = !selectedPhotos.isEmpty();
        boolean hasInput = !nameField.getText().trim().isEmpty() && 
                          !rollNoField.getText().trim().isEmpty();
        
        removeButton.setDisable(!hasPhotos);
        clearButton.setDisable(!hasPhotos);
        registerButton.setDisable(!hasPhotos || !hasInput);
        */
    }
    
    private void updateStatusLabel(String message) {
        javafx.application.Platform.runLater(() -> {
            statusLabel.setText(message);
        });
    }
    
    private void disableControls(boolean disable) {
        // TODO: Disable controls - some fields may not exist in current FXML
        if (nameField != null) nameField.setDisable(disable);
        if (rollNoField != null) rollNoField.setDisable(disable);
    }
    
    private void clearForm() {
        if (nameField != null) nameField.clear();
        if (rollNoField != null) rollNoField.clear();
        selectedPhotos.clear();
        updateUI();
    }
    
    private void showError(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    private void showInfo(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
}
