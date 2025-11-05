# Haar Cascade Files

This directory should contain OpenCV Haar cascade XML files for face detection.

## Required Files:
- `haarcascade_frontalface_alt.xml` - Primary face detection cascade
- `haarcascade_frontalface_default.xml` - Alternative face detection cascade

## How to get these files:
1. Download from OpenCV GitHub repository: https://github.com/opencv/opencv/tree/master/data/haarcascades
2. Copy the XML files to this directory
3. Restart the application

## Note:
The application will show a warning if these files are not found, but will still run.
Face detection will be disabled until the cascade files are properly installed.