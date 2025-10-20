package com.attendance.controller;

import java.net.URL;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ResourceBundle;

import com.attendance.util.Logger;

import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.control.Alert;
import javafx.scene.control.Label;
import javafx.scene.control.Tab;
import javafx.scene.control.TabPane;
import javafx.scene.layout.BorderPane;

/**
 * Main controller for the application layout
 */
public class MainLayoutController implements Initializable {
    
    @FXML
    private BorderPane rootPane;
    
    @FXML
    private TabPane mainTabPane;
    
    @FXML
    private Tab dashboardTab;
    
    @FXML
    private Tab registerTab;
    
    @FXML
    private Tab attendanceTab;
    
    @FXML
    private Tab addEmbeddingsTab;
    
    @FXML
    private Tab reportsTab;
    
    @FXML
    private Label statusLabel;
    
    @FXML
    private Label timeLabel;
    
    private DashboardController dashboardController;
    private static MainLayoutController instance;
    
    @Override
    public void initialize(URL location, ResourceBundle resources) {
        Logger.info("Initializing main layout controller");
        
        instance = this;
        
        // Load content for each tab
        loadTabContent();
        
        // Setup status bar
        updateStatusBar("Ready");
        
        // Start time updater
        startTimeUpdater();
        
        // Set default tab
        mainTabPane.getSelectionModel().select(dashboardTab);
        
        Logger.info("Main layout initialized successfully");
    }
    
    /**
     * Load FXML content into each tab
     */
    private void loadTabContent() {
        try {
            // Load Dashboard
            FXMLLoader dashboardLoader = new FXMLLoader();
            dashboardLoader.setLocation(getClass().getResource("/fxml/Dashboard.fxml"));
            dashboardTab.setContent(dashboardLoader.load());
            dashboardController = dashboardLoader.getController();
            
            // Load Register Student
            FXMLLoader registerLoader = new FXMLLoader();
            registerLoader.setLocation(getClass().getResource("/fxml/RegisterStudent.fxml"));
            registerTab.setContent(registerLoader.load());
            
            // Load Take Attendance
            FXMLLoader attendanceLoader = new FXMLLoader();
            attendanceLoader.setLocation(getClass().getResource("/fxml/TakeAttendance.fxml"));
            attendanceTab.setContent(attendanceLoader.load());
            
            // Load Add Embeddings
            FXMLLoader addEmbeddingsLoader = new FXMLLoader();
            addEmbeddingsLoader.setLocation(getClass().getResource("/fxml/AddEmbeddings.fxml"));
            addEmbeddingsTab.setContent(addEmbeddingsLoader.load());
            
            Logger.info("All tab content loaded successfully");
        } catch (Exception e) {
            Logger.error("Failed to load tab content: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Update status bar with message
     */
    public void updateStatusBar(String message) {
        if (statusLabel != null) {
            javafx.application.Platform.runLater(() -> {
                statusLabel.setText(message);
            });
        }
    }
    
    /**
     * Start time updater thread
     */
    private void startTimeUpdater() {
        Thread timeThread = new Thread(() -> {
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            while (true) {
                try {
                    String currentTime = LocalDateTime.now().format(formatter);
                    javafx.application.Platform.runLater(() -> {
                        if (timeLabel != null) {
                            timeLabel.setText(currentTime);
                        }
                    });
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        timeThread.setDaemon(true);
        timeThread.start();
    }
    
    @FXML
    private void handleDashboardTab() {
        Logger.info("Dashboard tab selected");
        updateStatusBar("Dashboard");
    }
    
    @FXML
    private void handleRegisterTab() {
        Logger.info("Register student tab selected");
        updateStatusBar("Register Student");
    }
    
    @FXML
    private void handleAttendanceTab() {
        Logger.info("Take attendance tab selected");
        updateStatusBar("Take Attendance");
    }
    
    @FXML
    private void handleReportsTab() {
        Logger.info("Reports tab selected");
        updateStatusBar("Attendance Reports");
    }
    
    @FXML
    private void handleRefresh() {
        Logger.info("Refresh requested");
        updateStatusBar("Refreshing...");
        // Refresh logic would go here
        updateStatusBar("Refreshed");
    }
    
    /**
     * Get the singleton instance of MainLayoutController
     */
    public static MainLayoutController getInstance() {
        return instance;
    }
    
    /**
     * Refresh dashboard data and optionally switch to dashboard tab
     */
    public void refreshDashboard(boolean switchTab) {
        if (dashboardController != null) {
            dashboardController.handleRefresh();
            if (switchTab) {
                Platform.runLater(() -> mainTabPane.getSelectionModel().select(dashboardTab));
            }
        }
    }
    
    @FXML
    private void handleExit() {
        Logger.info("Exit requested");
        Platform.exit();
    }
    
    @FXML
    private void handleAbout() {
        Logger.info("About dialog requested");
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("About");
        alert.setHeaderText("Face Recognition Attendance System");
        alert.setContentText("Version 1.0.0\n\nA desktop application for automated attendance using face recognition.\n\nTechnology Stack:\n- JavaFX (Frontend)\n- Flask + Python (Backend)\n- RetinaFace (Face Detection)\n- ArcFace (Face Recognition)");
        alert.showAndWait();
    }
}
