from PyQt6.QtCore import QCoreApplication
from PyQt6.QtMultimedia import QMediaDevices

app = QCoreApplication([])  # Initialize Qt Core application

available_cameras = QMediaDevices.videoInputs()

if available_cameras:
    print("Available Cameras:")
    for camera in available_cameras:
        print(camera.description())
else:
    print("No camera found!")
