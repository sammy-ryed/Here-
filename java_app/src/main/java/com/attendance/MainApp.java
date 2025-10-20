package com.attendance;

import com.attendance.util.ConfigManager;
import com.attendance.util.Logger;

import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.scene.image.Image;
import javafx.stage.Stage;

/**
 * Main application class for Face Recognition Attendance System
 */
public class MainApp extends Application {
    
    public static final String APP_TITLE = "Face Recognition Attendance System";
    public static final String VERSION = "1.0.0";
    
    @Override
    public void start(Stage primaryStage) {
        try {
            // Load configuration
            ConfigManager.loadConfig();
            Logger.info("Application starting...");
            
            // Load main layout
            FXMLLoader loader = new FXMLLoader();
            loader.setLocation(MainApp.class.getResource("/fxml/MainLayout.fxml"));
            Scene scene = new Scene(loader.load());
            
            // Add CSS stylesheet
            scene.getStylesheets().add(getClass().getResource("/css/style.css").toExternalForm());
            
            // Set stage properties
            primaryStage.setTitle(APP_TITLE + " v" + VERSION);
            primaryStage.setScene(scene);
            primaryStage.setMinWidth(1200);
            primaryStage.setMinHeight(800);
            primaryStage.setMaximized(true);
            
            // Set application icon (if available)
            try {
                primaryStage.getIcons().add(new Image(getClass().getResourceAsStream("/images/icon.png")));
            } catch (Exception e) {
                Logger.warn("Application icon not found");
            }
            
            // Show stage
            primaryStage.show();
            
            Logger.info("Application started successfully");
            
        } catch (Exception e) {
            Logger.error("Failed to start application: " + e.getMessage(), e);
            showErrorAndExit("Failed to start application", e.getMessage());
        }
    }
    
    @Override
    public void stop() {
        Logger.info("Application stopping...");
        // Cleanup resources
        try {
            // Close any open resources
        } catch (Exception e) {
            Logger.error("Error during cleanup: " + e.getMessage(), e);
        }
    }
    
    private void showErrorAndExit(String title, String message) {
        javafx.scene.control.Alert alert = new javafx.scene.control.Alert(
            javafx.scene.control.Alert.AlertType.ERROR
        );
        alert.setTitle(title);
        alert.setHeaderText("Application Error");
        alert.setContentText(message);
        alert.showAndWait();
        System.exit(1);
    }
    
    public static void main(String[] args) {
        launch(args);
    }
}
