package com.attendance.controller;

import java.io.File;
import java.net.URL;
import java.util.List;
import java.util.ResourceBundle;

import com.attendance.model.Student;
import com.attendance.service.ApiService;
import com.attendance.util.Logger;

import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.geometry.Pos;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressIndicator;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.FlowPane;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

/**
 * Controller for adding face embeddings to existing students
 */
public class AddEmbeddingsController implements Initializable {
    
    @FXML
    private ComboBox<Student> studentComboBox;
    
    @FXML
    private Label photoStatusLabel;
    
    @FXML
    private StackPane photoPreviewPane;
    
    @FXML
    private ImageView photoPreview;
    
    @FXML
    private Button extractFacesButton;
    
    @FXML
    private VBox facesSection;
    
    @FXML
    private Label facesCountLabel;
    
    @FXML
    private FlowPane facesPane;
    
    @FXML
    private ProgressIndicator progressIndicator;
    
    @FXML
    private Label statusLabel;
    
    private ApiService apiService;
    private File selectedPhoto;
    private JsonArray extractedFaces;
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        Logger.info("Initializing Add Embeddings controller");
        
        apiService = new ApiService();
        
        // Setup student combo box
        studentComboBox.setCellFactory(param -> new javafx.scene.control.ListCell<Student>() {
            @Override
            protected void updateItem(Student item, boolean empty) {
                super.updateItem(item, empty);
                if (empty || item == null) {
                    setText(null);
                } else {
                    setText(item.getName() + " (" + item.getRollNo() + ")");
                }
            }
        });
        
        studentComboBox.setButtonCell(new javafx.scene.control.ListCell<Student>() {
            @Override
            protected void updateItem(Student item, boolean empty) {
                super.updateItem(item, empty);
                if (empty || item == null) {
                    setText("Choose student...");
                } else {
                    setText(item.getName() + " (" + item.getRollNo() + ")");
                }
            }
        });
        
        // Load students
        loadStudents();
        
        updateStatus("Ready to update student recognition");
        Logger.info("Add Embeddings controller initialized");
    }
    
    private void loadStudents() {
        new Thread(() -> {
            try {
                List<Student> students = apiService.getAllStudents();
                
                Platform.runLater(() -> {
                    studentComboBox.getItems().clear();
                    studentComboBox.getItems().addAll(students);
                    Logger.info("Loaded " + students.size() + " students");
                });
                
            } catch (Exception e) {
                Logger.error("Error loading students: " + e.getMessage());
                Platform.runLater(() -> {
                    showError("Error", "Failed to load students: " + e.getMessage());
                });
            }
        }).start();
    }
    
    @FXML
    private void handleRefreshStudents() {
        Logger.info("Refreshing student list");
        loadStudents();
        updateStatus("Student list refreshed");
    }
    
    @FXML
    private void handleSelectPhoto() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Photo with Student Face");
        fileChooser.getExtensionFilters().addAll(
            new FileChooser.ExtensionFilter("Image Files", "*.jpg", "*.jpeg", "*.png"),
            new FileChooser.ExtensionFilter("All Files", "*.*")
        );
        
        Stage stage = (Stage) photoStatusLabel.getScene().getWindow();
        File file = fileChooser.showOpenDialog(stage);
        
        if (file != null) {
            selectedPhoto = file;
            
            // Show preview
            Image image = new Image(file.toURI().toString());
            photoPreview.setImage(image);
            photoPreviewPane.setVisible(true);
            
            photoStatusLabel.setText(file.getName());
            extractFacesButton.setDisable(false);
            
            // Hide previous faces
            facesSection.setVisible(false);
            extractedFaces = null;
            
            updateStatus("Photo loaded. Click 'Extract Faces' to continue.");
            Logger.info("Photo selected: " + file.getName());
        }
    }
    
    @FXML
    private void handleExtractFaces() {
        if (selectedPhoto == null) {
            showError("No Photo", "Please select a photo first");
            return;
        }
        
        if (studentComboBox.getValue() == null) {
            showError("No Student", "Please select a student first");
            return;
        }
        
        extractFaces();
    }
    
    private void extractFaces() {
        progressIndicator.setVisible(true);
        extractFacesButton.setDisable(true);
        updateStatus("Extracting faces from photo...");
        
        new Thread(() -> {
            try {
                JsonObject result = apiService.extractFaces(selectedPhoto);
                
                Platform.runLater(() -> {
                    progressIndicator.setVisible(false);
                    extractFacesButton.setDisable(false);
                    
                    if (result != null && result.has("faces")) {
                        extractedFaces = result.getAsJsonArray("faces");
                        Logger.info("Received " + extractedFaces.size() + " faces from API");
                        
                        if (extractedFaces.size() > 0) {
                            try {
                                displayFaces(extractedFaces);
                                updateStatus(extractedFaces.size() + " face(s) detected. Select the face to add.");
                            } catch (Exception e) {
                                Logger.error("Exception in displayFaces: " + e.getMessage());
                                e.printStackTrace();
                                showError("Display Error", "Failed to display faces: " + e.getMessage());
                            }
                        } else {
                            showError("No Faces", "No faces were detected in the photo. Try another photo.");
                            updateStatus("No faces detected");
                        }
                    } else {
                        Logger.error("API returned null or missing 'faces' field");
                        showError("No Faces", "No faces were detected in the photo. Try another photo.");
                        updateStatus("No faces detected");
                    }
                });
                
            } catch (Exception e) {
                Logger.error("Error extracting faces: " + e.getMessage());
                e.printStackTrace();
                Platform.runLater(() -> {
                    progressIndicator.setVisible(false);
                    extractFacesButton.setDisable(false);
                    showError("Error", "Failed to extract faces: " + e.getMessage());
                    updateStatus("Error extracting faces");
                });
            }
        }).start();
    }
    
    private void displayFaces(JsonArray faces) {
        Logger.info("=== START displayFaces() ===");
        Logger.info("Starting to display " + faces.size() + " faces");
        Logger.info("facesPane is null: " + (facesPane == null));
        Logger.info("facesSection is null: " + (facesSection == null));
        
        facesPane.getChildren().clear();
        Logger.info("Cleared facesPane children");
        
        try {
            for (int i = 0; i < faces.size(); i++) {
                JsonObject face = faces.get(i).getAsJsonObject();
                Logger.info("Processing face " + i + ": " + face.toString());
                
                try {
                    // Create face card
                    VBox faceCard = createFaceCard(face, i);
                    facesPane.getChildren().add(faceCard);
                    Logger.info("Added face card " + i + " to pane, total children: " + facesPane.getChildren().size());
                } catch (Exception e) {
                    Logger.error("Error creating face card " + i + ": " + e.getMessage());
                    e.printStackTrace();
                    
                    // Add simple text placeholder
                    Label errorLabel = new Label("Error loading face " + i);
                    errorLabel.setStyle("-fx-background-color: red; -fx-text-fill: white; -fx-padding: 20;");
                    facesPane.getChildren().add(errorLabel);
                    Logger.info("Added error placeholder for face " + i);
                }
            }
            
            Logger.info("About to make facesSection visible");
            facesSection.setVisible(true);
            facesSection.setManaged(true);
            Logger.info("facesSection visible: " + facesSection.isVisible() + ", managed: " + facesSection.isManaged());
            
            facesCountLabel.setText(faces.size() + " face(s) detected - Click on a face to add it");
            
            Logger.info("Successfully displayed " + faces.size() + " faces, facesPane children count: " + facesPane.getChildren().size());
            Logger.info("=== END displayFaces() ===");
        } catch (Exception e) {
            Logger.error("Error displaying faces: " + e.getMessage());
            e.printStackTrace();
            showError("Display Error", "Failed to display faces: " + e.getMessage());
        }
    }
    
    private VBox createFaceCard(JsonObject face, int index) {
        VBox card = new VBox(10);
        card.setAlignment(Pos.CENTER);
        card.setStyle("-fx-border-color: #cccccc; -fx-border-width: 2; -fx-padding: 10; " +
                     "-fx-background-color: white; -fx-effect: dropshadow(gaussian, rgba(0,0,0,0.1), 5, 0, 0, 2);");
        card.setPrefWidth(150);
        card.setMinHeight(200);
        
        try {
            // Face image
            String imageData = face.get("image_base64").getAsString();
            Logger.info("Loading image data for face " + index + ", data length: " + imageData.length());
            
            // Decode base64 - remove data:image/jpeg;base64, prefix if present
            String base64Data = imageData.contains(",") ? imageData.split(",")[1] : imageData;
            byte[] imageBytes = java.util.Base64.getDecoder().decode(base64Data);
            Logger.info("Decoded " + imageBytes.length + " bytes for face " + index);
            
            Image faceImage = new Image(new java.io.ByteArrayInputStream(imageBytes));
            Logger.info("Created Image object for face " + index + ", error: " + faceImage.isError());
            
            ImageView imageView = new ImageView(faceImage);
            imageView.setFitWidth(120);
            imageView.setFitHeight(120);
            imageView.setPreserveRatio(true);
            
            // Face info
            double confidence = face.get("confidence").getAsDouble();
            Label confidenceLabel = new Label(String.format("Face #%d\nConfidence: %.1f%%", index + 1, confidence * 100));
            confidenceLabel.setStyle("-fx-font-size: 10px; -fx-text-fill: #666666; -fx-text-alignment: center;");
            
            // Select button
            Button selectButton = new Button("Select This Face");
            selectButton.setStyle("-fx-background-color: #4CAF50; -fx-text-fill: white; -fx-font-weight: bold;");
            selectButton.setOnAction(e -> handleAddFaceEmbedding(face));
            
            card.getChildren().addAll(imageView, confidenceLabel, selectButton);
            
        } catch (Exception e) {
            Logger.error("Error creating face card " + index + ": " + e.getMessage());
            e.printStackTrace();
            
            // Add error display
            Label errorLabel = new Label("Error loading\nface #" + (index + 1));
            errorLabel.setStyle("-fx-text-fill: red; -fx-font-size: 12px;");
            card.getChildren().add(errorLabel);
        }
        
        // Hover effect
        card.setOnMouseEntered(e -> {
            card.setStyle("-fx-border-color: #4CAF50; -fx-border-width: 3; -fx-padding: 10; " +
                         "-fx-background-color: #f0f8f0; -fx-effect: dropshadow(gaussian, rgba(0,0,0,0.2), 8, 0, 0, 3);");
        });
        
        card.setOnMouseExited(e -> {
            card.setStyle("-fx-border-color: #cccccc; -fx-border-width: 2; -fx-padding: 10; " +
                         "-fx-background-color: white; -fx-effect: dropshadow(gaussian, rgba(0,0,0,0.1), 5, 0, 0, 2);");
        });
        
        return card;
    }
    
    private void handleAddFaceEmbedding(JsonObject face) {
        Student selectedStudent = studentComboBox.getValue();
        
        if (selectedStudent == null) {
            showError("No Student", "Please select a student");
            return;
        }
        
        // Confirm action
        Alert confirmAlert = new Alert(Alert.AlertType.CONFIRMATION);
        confirmAlert.setTitle("Confirm Addition");
        confirmAlert.setHeaderText("Add Face Embedding");
        confirmAlert.setContentText("Add this face to " + selectedStudent.getName() + "'s embeddings?\n\n" +
                                   "This will improve recognition accuracy for this student.");
        
        confirmAlert.showAndWait().ifPresent(response -> {
            if (response == javafx.scene.control.ButtonType.OK) {
                addEmbedding(selectedStudent.getId(), face.get("face_filename").getAsString());
            }
        });
    }
    
    private void addEmbedding(int studentId, String faceFilename) {
        progressIndicator.setVisible(true);
        updateStatus("Adding face embedding...");
        
        new Thread(() -> {
            try {
                boolean success = apiService.addEmbeddingToStudent(studentId, faceFilename);
                
                Platform.runLater(() -> {
                    progressIndicator.setVisible(false);
                    
                    if (success) {
                        showInfo("Success", 
                            "Face embedding added successfully!\n\n" +
                            "This student's recognition accuracy has been improved.");
                        
                        // Reset UI
                        handleCancel();
                        updateStatus("Face embedding added successfully");
                    } else {
                        showError("Failed", "Failed to add face embedding. Please try again.");
                        updateStatus("Failed to add face embedding");
                    }
                });
                
            } catch (Exception e) {
                Logger.error("Error adding embedding: " + e.getMessage());
                Platform.runLater(() -> {
                    progressIndicator.setVisible(false);
                    showError("Error", "Failed to add embedding: " + e.getMessage());
                    updateStatus("Error adding embedding");
                });
            }
        }).start();
    }
    
    @FXML
    private void handleCancel() {
        selectedPhoto = null;
        extractedFaces = null;
        
        photoPreview.setImage(null);
        photoPreviewPane.setVisible(false);
        photoStatusLabel.setText("No photo selected");
        extractFacesButton.setDisable(true);
        
        facesPane.getChildren().clear();
        facesSection.setVisible(false);
        
        // Re-enable extract button if photo is selected (shouldn't happen in cancel, but just in case)
        // The button will be properly enabled again when a new photo is selected
        
        updateStatus("Ready to update student recognition");
        Logger.info("Reset UI - Ready for next update");
    }
    
    private void updateStatus(String message) {
        Platform.runLater(() -> {
            statusLabel.setText(message);
        });
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
