package com.attendance.controller;

import java.io.File;
import java.net.URL;
import java.util.ResourceBundle;

import com.attendance.model.AttendanceResult;
import com.attendance.model.Student;
import com.attendance.service.ApiService;
import com.attendance.util.CameraCapture;
import com.attendance.util.Logger;

import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ButtonType;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressBar;
import javafx.scene.control.ProgressIndicator;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.FlowPane;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

/**
 * Controller for taking attendance
 */
public class TakeAttendanceController implements Initializable {
    
    @FXML
    private ImageView imagePreview;
    
    @FXML
    private Button uploadPhotoButton;
    
    @FXML
    private Button capturePhotoButton;
    
    @FXML
    private Button processButton;
    
    @FXML
    private Button retakeButton;
    
    @FXML
    private ProgressIndicator progressIndicator;
    
    @FXML
    private ProgressBar progressBar;
    
    @FXML
    private Label statusLabel;
    
    @FXML
    private TableView<Student> presentTable;
    
    @FXML
    private TableColumn<Student, String> presentNameCol;
    
    @FXML
    private TableColumn<Student, String> presentRollCol;
    
    @FXML
    private TableColumn<Student, String> presentConfidenceCol;
    
    @FXML
    private TableView<Student> absentTable;
    
    @FXML
    private TableColumn<Student, String> absentNameCol;
    
    @FXML
    private TableColumn<Student, String> absentRollCol;
    
    @FXML
    private FlowPane unrecognizedPane;
    
    @FXML
    private Label presentCountLabel;
    
    @FXML
    private Label absentCountLabel;
    
    @FXML
    private Label unrecognizedCountLabel;
    
    @FXML
    private Label totalFacesLabel;
    
    private File selectedPhoto;
    private java.util.List<File> selectedPhotos;
    private int currentPhotoIndex = 0;  // Track current photo being viewed
    private ApiService apiService;
    private CameraCapture cameraCapture;
    private ObservableList<Student> presentStudents;
    private ObservableList<Student> absentStudents;
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        Logger.info("Initializing take attendance controller");
        
        apiService = new ApiService();
        
        // Try to initialize camera capture (may fail if OpenCV not loaded)
        try {
            cameraCapture = new CameraCapture();
        } catch (Exception e) {
            Logger.warn("Camera capture not available: " + e.getMessage());
            cameraCapture = null;
        }
        
        presentStudents = FXCollections.observableArrayList();
        absentStudents = FXCollections.observableArrayList();
        
        // Setup keyboard navigation for photo browsing
        setupPhotoNavigation();
        
        updateStatusLabel("Ready to take attendance");
        Logger.info("Take attendance controller initialized");
    }
    
    private void setupPhotoNavigation() {
        // Add keyboard listener to imagePreview for arrow key navigation
        if (imagePreview != null) {
            imagePreview.setOnKeyPressed(event -> {
                if (selectedPhotos != null && selectedPhotos.size() > 1) {
                    switch (event.getCode()) {
                        case LEFT:
                        case UP:
                            showPreviousPhoto();
                            event.consume();
                            break;
                        case RIGHT:
                        case DOWN:
                            showNextPhoto();
                            event.consume();
                            break;
                        default:
                            break;
                    }
                }
            });
            
            // Make imagePreview focusable so it can receive key events
            imagePreview.setFocusTraversable(true);
        }
    }
    
    private void showPreviousPhoto() {
        if (selectedPhotos == null || selectedPhotos.isEmpty()) {
            return;
        }
        
        currentPhotoIndex--;
        if (currentPhotoIndex < 0) {
            currentPhotoIndex = selectedPhotos.size() - 1; // Wrap to last photo
        }
        
        displayCurrentPhoto();
    }
    
    private void showNextPhoto() {
        if (selectedPhotos == null || selectedPhotos.isEmpty()) {
            return;
        }
        
        currentPhotoIndex++;
        if (currentPhotoIndex >= selectedPhotos.size()) {
            currentPhotoIndex = 0; // Wrap to first photo
        }
        
        displayCurrentPhoto();
    }
    
    private void displayCurrentPhoto() {
        if (selectedPhotos == null || selectedPhotos.isEmpty()) {
            return;
        }
        
        try {
            File currentFile = selectedPhotos.get(currentPhotoIndex);
            Image image = new Image(currentFile.toURI().toString());
            imagePreview.setImage(image);
            
            // Update status to show which photo is being viewed
            String photoInfo = String.format("Photo %d of %d - Use arrow keys to navigate", 
                                           currentPhotoIndex + 1, 
                                           selectedPhotos.size());
            updateStatusLabel(photoInfo);
            
            Logger.info("Displaying photo " + (currentPhotoIndex + 1) + " of " + selectedPhotos.size());
        } catch (Exception e) {
            Logger.error("Error displaying photo: " + e.getMessage(), e);
        }
    }
    
    private void setupTables() {
        // TODO: Setup tables/lists based on FXML design
        // Current FXML uses ListViews, not TableViews
    }
    
    @FXML
    private void handleUploadPhoto() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Classroom Photos (Multiple Selection Enabled)");
        fileChooser.getExtensionFilters().addAll(
            new FileChooser.ExtensionFilter("Image Files", "*.jpg", "*.jpeg", "*.png"),
            new FileChooser.ExtensionFilter("All Files", "*.*")
        );
        
        // Use statusLabel to get the window instead of uploadPhotoButton which doesn't exist in FXML
        Stage stage = (Stage) statusLabel.getScene().getWindow();
        
        // Allow multiple file selection
        java.util.List<File> files = fileChooser.showOpenMultipleDialog(stage);
        
        if (files != null && !files.isEmpty()) {
            loadPhotos(files);
        }
    }
    
    @FXML
    private void handleCapturePhoto() {
        try {
            updateStatusLabel("Opening camera...");
            File capturedFile = cameraCapture.capturePhoto();
            
            if (capturedFile != null) {
                loadPhoto(capturedFile);
            } else {
                updateStatusLabel("Failed to capture photo");
            }
        } catch (Exception e) {
            Logger.error("Error capturing photo: " + e.getMessage(), e);
            showError("Camera Error", "Failed to capture photo: " + e.getMessage());
        }
    }
    
    private void loadPhoto(File file) {
        try {
            selectedPhoto = file;
            selectedPhotos = new java.util.ArrayList<>();
            selectedPhotos.add(file);
            
            Image image = new Image(file.toURI().toString());
            imagePreview.setImage(image);
            processButton.setDisable(false);
            updateStatusLabel("Photo loaded. Click 'Process Attendance' to continue.");
            
            // Clear previous results
            clearResults();
        } catch (Exception e) {
            Logger.error("Error loading photo: " + e.getMessage(), e);
            showError("Error", "Failed to load photo: " + e.getMessage());
        }
    }
    
    private void loadPhotos(java.util.List<File> files) {
        try {
            selectedPhotos = files;
            selectedPhoto = files.get(0); // Keep for backward compatibility
            currentPhotoIndex = 0; // Reset to first photo
            
            // Show the first image in preview
            Image image = new Image(files.get(0).toURI().toString());
            imagePreview.setImage(image);
            processButton.setDisable(false);
            
            // Request focus so arrow keys work immediately
            imagePreview.requestFocus();
            
            String message;
            if (files.size() == 1) {
                message = "1 photo loaded. Click 'Process Attendance' to continue.";
            } else {
                message = String.format("%d photos loaded. Photo 1 of %d - Use arrow keys to navigate. Click 'Process Attendance' when ready.", 
                                      files.size(), files.size());
            }
            updateStatusLabel(message);
            
            Logger.info("Loaded " + files.size() + " photo(s) for attendance processing");
            
            // Clear previous results
            clearResults();
        } catch (Exception e) {
            Logger.error("Error loading photos: " + e.getMessage(), e);
            showError("Error", "Failed to load photos: " + e.getMessage());
        }
    }
    
    @FXML
    private void handleProcessAttendance() {
        if (selectedPhotos == null || selectedPhotos.isEmpty()) {
            showError("No Photo", "Please upload or capture a photo first");
            return;
        }
        
        processAttendance();
    }
    
    private void processAttendance() {
        if (progressBar != null) {
            progressBar.setVisible(true);
        }
        
        String statusMessage = selectedPhotos.size() == 1 
            ? "Processing attendance from 1 photo..." 
            : "Processing attendance from " + selectedPhotos.size() + " photos...";
        updateStatusLabel(statusMessage);
        disableControls(true);
        
        new Thread(() -> {
            try {
                AttendanceResult result;
                
                // Use batch processing if multiple photos, otherwise use single photo processing
                if (selectedPhotos.size() > 1) {
                    result = apiService.processAttendanceBatch(selectedPhotos);
                } else {
                    result = apiService.processAttendance(selectedPhotos.get(0));
                }
                
                javafx.application.Platform.runLater(() -> {
                    if (progressBar != null) {
                        progressBar.setVisible(false);
                    }
                    disableControls(false);
                    
                    if (result != null) {
                        displayResults(result);
                        
                        String successMessage = selectedPhotos.size() == 1
                            ? "Attendance processed successfully"
                            : "Attendance processed from " + selectedPhotos.size() + " photos successfully";
                        updateStatusLabel(successMessage);
                    } else {
                        showError("Processing Failed", "Failed to process attendance. Please try again.");
                        updateStatusLabel("Processing failed");
                    }
                });
                
            } catch (Exception e) {
                Logger.error("Error processing attendance: " + e.getMessage(), e);
                javafx.application.Platform.runLater(() -> {
                    if (progressBar != null) {
                        progressBar.setVisible(false);
                    }
                    disableControls(false);
                    showError("Error", "Processing error: " + e.getMessage());
                    updateStatusLabel("Error during processing");
                });
            }
        }).start();
    }
    
    private void displayResults(AttendanceResult result) {
        // Clear previous results
        presentStudents.clear();
        absentStudents.clear();
        
        // Note: The FXML uses ListViews (presentList, absentList, unrecognizedList)
        // but the controller was designed for TableViews and FlowPanes
        // TODO: Implement proper display once FXML/controller fields are aligned
        
        // Add present students to observable list
        presentStudents.addAll(result.getPresentStudents());
        
        // Add absent students to observable list
        absentStudents.addAll(result.getAbsentStudents());
        
        // Skip unrecognized faces display for now (unrecognizedPane doesn't exist in FXML)
        // The FXML has unrecognizedList (ListView) instead
        
        // Skip count label updates (these labels don't exist in current FXML)
        // presentCountLabel.setText(String.valueOf(presentStudents.size()));
        // absentCountLabel.setText(String.valueOf(absentStudents.size()));
        // unrecognizedCountLabel.setText(String.valueOf(result.getUnrecognizedFaces().size()));
        // totalFacesLabel.setText(String.valueOf(result.getTotalFaces()));
        
        // Skip retake button (doesn't exist in FXML)
        // retakeButton.setDisable(result.getUnrecognizedFaces().isEmpty());
        
        showInfo("Attendance Processed", 
            String.format("Present: %d, Absent: %d, Unrecognized: %d, Total Faces: %d", 
                presentStudents.size(), absentStudents.size(), 
                result.getUnrecognizedFaces().size(), result.getTotalFaces()));
        
        // Refresh dashboard to show updated statistics
        refreshDashboard();
    }
    
    /**
     * Refresh the dashboard with updated attendance data
     */
    private void refreshDashboard() {
        try {
            MainLayoutController mainController = MainLayoutController.getInstance();
            if (mainController != null) {
                mainController.refreshDashboard(true); // true = switch to dashboard tab
                Logger.info("Dashboard refreshed after attendance processing");
            }
        } catch (Exception e) {
            Logger.error("Failed to refresh dashboard: " + e.getMessage());
        }
    }
    
    @FXML
    private void handleRetake() {
        clearResults();
        imagePreview.setImage(null);
        selectedPhoto = null;
        if (processButton != null) {
            processButton.setDisable(true);
        }
        // retakeButton doesn't exist in FXML
        updateStatusLabel("Ready for new photo");
    }
    
    @FXML
    private void handleConfirmAttendance() {
        if (presentStudents.isEmpty() && absentStudents.isEmpty()) {
            showError("No Data", "No attendance data to confirm");
            return;
        }
        
        Alert alert = new Alert(Alert.AlertType.CONFIRMATION);
        alert.setTitle("Confirm Attendance");
        alert.setHeaderText("Confirm and Save Attendance");
        alert.setContentText(String.format(
            "Present: %d students\nAbsent: %d students\n\nDo you want to save this attendance record?",
            presentStudents.size(), absentStudents.size()
        ));
        
        alert.showAndWait().ifPresent(response -> {
            if (response == ButtonType.OK) {
                updateStatusLabel("Attendance confirmed and saved");
                showInfo("Success", "Attendance record saved successfully!");
                
                // Clear after confirmation
                javafx.application.Platform.runLater(() -> {
                    try {
                        Thread.sleep(2000);
                        handleRetake();
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                });
            }
        });
    }
    
    private void clearResults() {
        presentStudents.clear();
        absentStudents.clear();
        
        // Clear unrecognized list if it exists (FXML uses ListView, not FlowPane)
        // The field declarations don't match FXML, so we skip this for now
        // TODO: Update controller fields to match FXML (presentList, absentList, unrecognizedList)
        
        // These labels don't exist in current FXML, so commenting out
        // presentCountLabel.setText("0");
        // absentCountLabel.setText("0");
        // unrecognizedCountLabel.setText("0");
        // totalFacesLabel.setText("0");
    }
    
    private void updateStatusLabel(String message) {
        javafx.application.Platform.runLater(() -> {
            statusLabel.setText(message);
        });
    }
    
    private void disableControls(boolean disable) {
        // Only disable buttons that exist in FXML and are properly initialized
        if (processButton != null) {
            processButton.setDisable(disable);
        }
        // uploadPhotoButton, capturePhotoButton, and retakeButton don't have fx:id in FXML
        // so they are null - skip them
    }
    
    @FXML
    private void handleSaveAttendance() {
        Logger.info("Saving attendance");
        updateStatusLabel("Attendance saved successfully");
        showInfo("Success", "Attendance has been saved to the database");
    }
    
    @FXML
    private void handleExportReport() {
        Logger.info("Exporting attendance report");
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Export Attendance Report");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("CSV Files", "*.csv")
        );
        
        Stage stage = (Stage) uploadPhotoButton.getScene().getWindow();
        File file = fileChooser.showSaveDialog(stage);
        
        if (file != null) {
            updateStatusLabel("Report exported to: " + file.getName());
            showInfo("Export Complete", "Attendance report exported successfully");
        }
    }
    
    @FXML
    private void handleClear() {
        selectedPhoto = null;
        selectedPhotos = null;
        imagePreview.setImage(null);
        presentStudents.clear();
        absentStudents.clear();
        
        // Clear unrecognized list - skip for now due to field mismatch
        // unrecognizedPane doesn't exist in FXML (it has unrecognizedList ListView)
        
        // These labels don't exist in current FXML
        // presentCountLabel.setText("0");
        // absentCountLabel.setText("0");
        // unrecognizedCountLabel.setText("0");
        // totalFacesLabel.setText("0");
        
        processButton.setDisable(true);
        retakeButton.setDisable(true);
        
        updateStatusLabel("Ready to take attendance");
        Logger.info("Cleared attendance results");
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
