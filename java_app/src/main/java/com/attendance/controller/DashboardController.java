package com.attendance.controller;

import java.net.URL;
import java.util.ResourceBundle;

import com.attendance.model.DashboardStats;
import com.attendance.model.Student;
import com.attendance.service.ApiService;
import com.attendance.util.Logger;

import javafx.animation.Animation;
import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.Label;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.util.Duration;

/**
 * Controller for dashboard view
 */
public class DashboardController implements Initializable {
    
    @FXML
    private Label totalStudentsLabel;
    
    @FXML
    private Label presentTodayLabel;
    
    @FXML
    private Label attendancePercentLabel;
    
    @FXML
    private TableView<Student> studentsTable;
    
    @FXML
    private TableColumn<Student, String> idColumn;
    
    @FXML
    private TableColumn<Student, String> nameColumn;
    
    @FXML
    private TableColumn<Student, String> rollNoColumn;
    
    @FXML
    private TableColumn<Student, String> presentTodayColumn;
    
    @FXML
    private TableColumn<Student, String> statusColumn;
    
    @FXML
    private TableColumn<Student, String> lastAttendanceColumn;
    
    @FXML
    private TableColumn<Student, Void> actionsColumn;
    
    private ApiService apiService;
    private ObservableList<Student> studentsList;
    private Timeline autoRefreshTimeline;
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        Logger.info("Initializing dashboard controller");
        
        apiService = new ApiService();
        studentsList = FXCollections.observableArrayList();
        
        // Setup table
        setupTable();
        
        // Load dashboard data
        loadDashboardData();
        
        // Setup auto-refresh every 30 seconds
        setupAutoRefresh();
        
        Logger.info("Dashboard controller initialized");
    }
    
    private void setupTable() {
        idColumn.setCellValueFactory(cellData -> 
            new javafx.beans.property.SimpleStringProperty(String.valueOf(cellData.getValue().getId())));
        rollNoColumn.setCellValueFactory(cellData -> 
            new javafx.beans.property.SimpleStringProperty(cellData.getValue().getRollNo()));
        nameColumn.setCellValueFactory(cellData -> 
            new javafx.beans.property.SimpleStringProperty(cellData.getValue().getName()));
        
        // Add context menu for right-click on table rows
        studentsTable.setRowFactory(tv -> {
            javafx.scene.control.TableRow<Student> row = new javafx.scene.control.TableRow<>();
            javafx.scene.control.ContextMenu contextMenu = new javafx.scene.control.ContextMenu();
            
            javafx.scene.control.MenuItem deleteItem = new javafx.scene.control.MenuItem("Delete Student");
            deleteItem.setOnAction(event -> {
                Student student = row.getItem();
                if (student != null) {
                    handleDeleteStudent(student);
                }
            });
            
            contextMenu.getItems().add(deleteItem);
            
            // Only show context menu when row is not empty
            row.contextMenuProperty().bind(
                javafx.beans.binding.Bindings.when(row.emptyProperty())
                .then((javafx.scene.control.ContextMenu) null)
                .otherwise(contextMenu)
            );
            
            return row;
        });
        
        // Present Today column - shows "Present", "Absent", or "N/A"
        presentTodayColumn.setCellValueFactory(cellData -> {
            String status = cellData.getValue().getAttendanceStatus();
            // Capitalize first letter for display
            String displayStatus = status.substring(0, 1).toUpperCase() + status.substring(1);
            return new javafx.beans.property.SimpleStringProperty(displayStatus);
        });
        
        // Style the Present Today column based on status
        presentTodayColumn.setCellFactory(column -> {
            return new javafx.scene.control.TableCell<Student, String>() {
                @Override
                protected void updateItem(String item, boolean empty) {
                    super.updateItem(item, empty);
                    
                    if (empty || item == null) {
                        setText(null);
                        setStyle("");
                    } else {
                        setText(item);
                        
                        // Color code based on status
                        if (item.equalsIgnoreCase("Present")) {
                            setStyle("-fx-text-fill: green; -fx-font-weight: bold;");
                        } else if (item.equalsIgnoreCase("Absent")) {
                            setStyle("-fx-text-fill: red; -fx-font-weight: bold;");
                        } else {
                            setStyle("-fx-text-fill: gray;");
                        }
                    }
                }
            };
        });
        
        statusColumn.setCellValueFactory(cellData -> 
            new javafx.beans.property.SimpleStringProperty("Active"));
        lastAttendanceColumn.setCellValueFactory(cellData -> 
            new javafx.beans.property.SimpleStringProperty("N/A"));
        
        // Actions column with toggle buttons
        actionsColumn.setCellFactory(column -> {
            return new javafx.scene.control.TableCell<Student, Void>() {
                private final javafx.scene.control.Button presentBtn = new javafx.scene.control.Button("Present");
                private final javafx.scene.control.Button absentBtn = new javafx.scene.control.Button("Absent");
                
                {
                    // Style Present button - Modern green with hover effect
                    presentBtn.setStyle(
                        "-fx-background-color: #4CAF50; " +
                        "-fx-text-fill: white; " +
                        "-fx-font-weight: bold; " +
                        "-fx-font-size: 11px; " +
                        "-fx-padding: 5 10; " +
                        "-fx-background-radius: 4; " +
                        "-fx-cursor: hand; " +
                        "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.2), 2, 0, 0, 1);"
                    );
                    
                    // Style Absent button - Modern red with hover effect
                    absentBtn.setStyle(
                        "-fx-background-color: #f44336; " +
                        "-fx-text-fill: white; " +
                        "-fx-font-weight: bold; " +
                        "-fx-font-size: 11px; " +
                        "-fx-padding: 5 10; " +
                        "-fx-background-radius: 4; " +
                        "-fx-cursor: hand; " +
                        "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.2), 2, 0, 0, 1);"
                    );
                    
                    presentBtn.setMinWidth(65);
                    absentBtn.setMinWidth(65);
                    
                    // Hover effects
                    presentBtn.setOnMouseEntered(e -> 
                        presentBtn.setStyle(
                            "-fx-background-color: #45a049; " +
                            "-fx-text-fill: white; " +
                            "-fx-font-weight: bold; " +
                            "-fx-font-size: 11px; " +
                            "-fx-padding: 5 10; " +
                            "-fx-background-radius: 4; " +
                            "-fx-cursor: hand; " +
                            "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.3), 4, 0, 0, 2);"
                        )
                    );
                    
                    presentBtn.setOnMouseExited(e -> 
                        presentBtn.setStyle(
                            "-fx-background-color: #4CAF50; " +
                            "-fx-text-fill: white; " +
                            "-fx-font-weight: bold; " +
                            "-fx-font-size: 11px; " +
                            "-fx-padding: 5 10; " +
                            "-fx-background-radius: 4; " +
                            "-fx-cursor: hand; " +
                            "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.2), 2, 0, 0, 1);"
                        )
                    );
                    
                    absentBtn.setOnMouseEntered(e -> 
                        absentBtn.setStyle(
                            "-fx-background-color: #da190b; " +
                            "-fx-text-fill: white; " +
                            "-fx-font-weight: bold; " +
                            "-fx-font-size: 11px; " +
                            "-fx-padding: 5 10; " +
                            "-fx-background-radius: 4; " +
                            "-fx-cursor: hand; " +
                            "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.3), 4, 0, 0, 2);"
                        )
                    );
                    
                    absentBtn.setOnMouseExited(e -> 
                        absentBtn.setStyle(
                            "-fx-background-color: #f44336; " +
                            "-fx-text-fill: white; " +
                            "-fx-font-weight: bold; " +
                            "-fx-font-size: 11px; " +
                            "-fx-padding: 5 10; " +
                            "-fx-background-radius: 4; " +
                            "-fx-cursor: hand; " +
                            "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.2), 2, 0, 0, 1);"
                        )
                    );
                    
                    // Set actions
                    presentBtn.setOnAction(event -> {
                        Student student = getTableView().getItems().get(getIndex());
                        markAttendance(student, true);
                    });
                    
                    absentBtn.setOnAction(event -> {
                        Student student = getTableView().getItems().get(getIndex());
                        markAttendance(student, false);
                    });
                }
                
                @Override
                protected void updateItem(Void item, boolean empty) {
                    super.updateItem(item, empty);
                    
                    if (empty) {
                        setGraphic(null);
                    } else {
                        javafx.scene.layout.HBox buttons = new javafx.scene.layout.HBox(8);
                        buttons.setAlignment(javafx.geometry.Pos.CENTER);
                        buttons.getChildren().addAll(presentBtn, absentBtn);
                        setGraphic(buttons);
                    }
                }
            };
        });
        
        studentsTable.setItems(studentsList);
    }
    
    private void setupAutoRefresh() {
        // Auto-refresh every 30 seconds
        autoRefreshTimeline = new Timeline(new KeyFrame(Duration.seconds(30), event -> {
            Logger.info("Auto-refreshing dashboard...");
            loadDashboardData();
        }));
        autoRefreshTimeline.setCycleCount(Animation.INDEFINITE);
        autoRefreshTimeline.play();
    }
    
    private void loadDashboardData() {
        new Thread(() -> {
            try {
                // Get dashboard stats with real data
                DashboardStats stats = apiService.getDashboardStats();
                
                if (stats != null) {
                    javafx.application.Platform.runLater(() -> {
                        // Update statistics with real data
                        totalStudentsLabel.setText(String.valueOf(stats.getTotalStudents()));
                        presentTodayLabel.setText(String.valueOf(stats.getPresentToday()));
                        attendancePercentLabel.setText(String.format("%.1f%%", stats.getAttendanceRate()));
                        
                        // Update table with students
                        studentsList.setAll(stats.getStudents());
                        
                        Logger.info(String.format("Dashboard updated: %d students, %d present (%.1f%%)", 
                            stats.getTotalStudents(), stats.getPresentToday(), stats.getAttendanceRate()));
                    });
                }
                
            } catch (Exception e) {
                Logger.error("Error loading dashboard data: " + e.getMessage());
            }
        }).start();
    }
    
    @FXML
    public void handleRefresh() {
        Logger.info("Manual refresh requested");
        loadDashboardData();
    }
    
    @FXML
    public void handleClearTodayAttendance() {
        Logger.info("Clear today's attendance requested");
        
        // Show confirmation dialog
        javafx.scene.control.Alert alert = new javafx.scene.control.Alert(javafx.scene.control.Alert.AlertType.CONFIRMATION);
        alert.setTitle("Clear Today's Attendance");
        alert.setHeaderText("Clear All Attendance Records for Today");
        alert.setContentText("This will reset all students to 'N/A' status for today. This action cannot be undone.\n\nAre you sure you want to continue?");
        
        alert.showAndWait().ifPresent(response -> {
            if (response == javafx.scene.control.ButtonType.OK) {
                clearAttendanceAsync();
            }
        });
    }
    
    private void clearAttendanceAsync() {
        new Thread(() -> {
            try {
                boolean success = apiService.clearTodayAttendance();
                
                javafx.application.Platform.runLater(() -> {
                    if (success) {
                        Logger.info("Today's attendance cleared successfully");
                        showInfo("Success", "All attendance records for today have been cleared.\nAll students are now in 'N/A' status.");
                        
                        // Refresh dashboard to show updated status
                        loadDashboardData();
                    } else {
                        Logger.error("Failed to clear today's attendance");
                        showError("Error", "Failed to clear today's attendance. Please try again.");
                    }
                });
                
            } catch (Exception e) {
                Logger.error("Error clearing today's attendance: " + e.getMessage());
                javafx.application.Platform.runLater(() -> {
                    showError("Error", "An error occurred while clearing attendance: " + e.getMessage());
                });
            }
        }).start();
    }
    
    private void showError(String title, String message) {
        javafx.scene.control.Alert alert = new javafx.scene.control.Alert(javafx.scene.control.Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    private void showInfo(String title, String message) {
        javafx.scene.control.Alert alert = new javafx.scene.control.Alert(javafx.scene.control.Alert.AlertType.INFORMATION);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    private void handleDeleteStudent(Student student) {
        Logger.info("Delete student requested: " + student.getName());
        
        // Show confirmation dialog
        javafx.scene.control.Alert confirmAlert = new javafx.scene.control.Alert(javafx.scene.control.Alert.AlertType.WARNING);
        confirmAlert.setTitle("Confirm Delete Student");
        confirmAlert.setHeaderText("Delete " + student.getName() + "?");
        confirmAlert.setContentText("This will permanently delete:\n" +
                "• Student: " + student.getName() + " (" + student.getRollNo() + ")\n" +
                "• All their face embeddings\n" +
                "• All their attendance records\n\n" +
                "This action CANNOT be undone!\n\n" +
                "Are you sure?");
        
        javafx.scene.control.ButtonType yesButton = new javafx.scene.control.ButtonType("Yes, Delete", javafx.scene.control.ButtonBar.ButtonData.YES);
        javafx.scene.control.ButtonType noButton = new javafx.scene.control.ButtonType("No, Cancel", javafx.scene.control.ButtonBar.ButtonData.NO);
        confirmAlert.getButtonTypes().setAll(yesButton, noButton);
        
        confirmAlert.showAndWait().ifPresent(response -> {
            if (response == yesButton) {
                // User confirmed, proceed with deletion
                new Thread(() -> {
                    try {
                        boolean success = apiService.deleteStudent(student.getId());
                        
                        javafx.application.Platform.runLater(() -> {
                            if (success) {
                                Logger.info("Student deleted successfully: " + student.getName());
                                showInfo("Success", "Student " + student.getName() + " has been deleted.");
                                
                                // Refresh dashboard
                                loadDashboardData();
                            } else {
                                Logger.error("Failed to delete student: " + student.getName());
                                showError("Error", "Failed to delete student.");
                            }
                        });
                        
                    } catch (Exception e) {
                        Logger.error("Error deleting student: " + e.getMessage());
                        javafx.application.Platform.runLater(() -> {
                            showError("Error", "An error occurred: " + e.getMessage());
                        });
                    }
                }).start();
            } else {
                Logger.info("Student deletion cancelled");
            }
        });
    }
    
    private void markAttendance(Student student, boolean isPresent) {
        String status = isPresent ? "present" : "absent";
        Logger.info("Manual attendance: " + student.getName() + " -> " + status);
        
        new Thread(() -> {
            try {
                boolean success = apiService.markStudentAttendance(student.getId(), status);
                
                javafx.application.Platform.runLater(() -> {
                    if (success) {
                        String message = student.getName() + " marked as " + (isPresent ? "Present" : "Absent");
                        Logger.info(message);
                        
                        // Refresh dashboard to show updated status
                        loadDashboardData();
                    } else {
                        Logger.error("Failed to mark attendance for " + student.getName());
                        showError("Error", "Failed to mark attendance. Please try again.");
                    }
                });
                
            } catch (Exception e) {
                Logger.error("Error marking attendance: " + e.getMessage());
                javafx.application.Platform.runLater(() -> {
                    showError("Error", "An error occurred: " + e.getMessage());
                });
            }
        }).start();
    }
    
    public void cleanup() {
        // Stop auto-refresh when controller is destroyed
        if (autoRefreshTimeline != null) {
            autoRefreshTimeline.stop();
        }
    }
}
