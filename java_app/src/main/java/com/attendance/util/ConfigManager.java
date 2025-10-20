package com.attendance.util;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Configuration manager for application settings
 */
public class ConfigManager {
    
    private static Properties properties = new Properties();
    private static final String CONFIG_FILE = "config.properties";
    
    /**
     * Load configuration from file
     */
    public static void loadConfig() {
        try {
            // Try to load from classpath
            InputStream is = ConfigManager.class.getClassLoader().getResourceAsStream(CONFIG_FILE);
            
            if (is != null) {
                properties.load(is);
                is.close();
                Logger.info("Configuration loaded from classpath");
            } else {
                // Try to load from file system
                try (FileInputStream fis = new FileInputStream(CONFIG_FILE)) {
                    properties.load(fis);
                    Logger.info("Configuration loaded from file system");
                } catch (IOException e) {
                    Logger.warn("Configuration file not found, using defaults");
                    loadDefaults();
                }
            }
            
        } catch (IOException e) {
            Logger.error("Error loading configuration: " + e.getMessage(), e);
            loadDefaults();
        }
    }
    
    /**
     * Load default configuration values
     */
    private static void loadDefaults() {
        properties.setProperty("api.base.url", "http://localhost:5000");
        properties.setProperty("camera.device.index", "0");
        properties.setProperty("camera.width", "640");
        properties.setProperty("camera.height", "480");
        properties.setProperty("theme", "light");
        Logger.info("Default configuration loaded");
    }
    
    /**
     * Get property value
     */
    public static String getProperty(String key) {
        return properties.getProperty(key);
    }
    
    /**
     * Get property value with default
     */
    public static String getProperty(String key, String defaultValue) {
        return properties.getProperty(key, defaultValue);
    }
    
    /**
     * Get property as integer
     */
    public static int getIntProperty(String key, int defaultValue) {
        String value = properties.getProperty(key);
        if (value != null) {
            try {
                return Integer.parseInt(value);
            } catch (NumberFormatException e) {
                Logger.warn("Invalid integer value for key: " + key);
            }
        }
        return defaultValue;
    }
    
    /**
     * Set property value
     */
    public static void setProperty(String key, String value) {
        properties.setProperty(key, value);
    }
    
    /**
     * Save configuration to file
     */
    public static void saveConfig() {
        try (java.io.FileOutputStream fos = new java.io.FileOutputStream(CONFIG_FILE)) {
            properties.store(fos, "Face Recognition Attendance System Configuration");
            Logger.info("Configuration saved");
        } catch (IOException e) {
            Logger.error("Error saving configuration: " + e.getMessage(), e);
        }
    }
}
