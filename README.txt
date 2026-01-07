
SENT – Smart Environmental Navigation and Tracking Robot

Graduation project developed to enhance indoor safety using an IoT-based mobile robot.

---

OVERVIEW
SENT is a smart environmental monitoring robot designed to detect gas leaks and water hazards
inside indoor environments. The system provides real-time monitoring, live video streaming,
and instant alerts to users through a centralized dashboard.

The project integrates hardware sensors with a backend server and a mobile dashboard
to support monitoring, control, and alert management.

---

FEATURES

-  Gas and water leak detection
-  Real-time notifications and alert logging
-  Live video streaming using MJPEG
-  Role-based access (Admin / User)
-  Remote photo capture
-  Mobile dashboard for monitoring and control

---

SYSTEM ARCHITECTURE

-  Robot & Sensors: Gas sensor, water sensor, camera module
-  Backend Server: Flask-based API running on Raspberry Pi
-  Frontend Dashboard: Flutter mobile application
-  Alerts: Email and WhatsApp notifications
-  Data Storage: Local JSON-based logging

---

TECHNOLOGIES USED

-  Raspberry Pi 4
-  Python (Flask)
-  Flutter (Dart)
-  MJPEG-Streamer
-  Twilio API (WhatsApp Alerts)
-  SMTP (Email Alerts)

---

PROJECT STRUCTURE

SENT-Graduation-Project
|
|-- Backend
|   |-- server.py
|   |-- requirements.txt
|
|-- Frontend
|   |-- lib
|       |-- main.dart
|       |-- config.dart
|       |-- login_page.dart
|       |-- dashboard_page.dart
|
|-- report
|   |-- SENT_Final_Report.pdf
|
|-- .gitignore
|-- .env.example
|-- README.txt

---

SETUP INSTRUCTIONS

Backend (Flask):

1. Install dependencies:
   pip install -r Backend/requirements.txt

2. Configure environment variables using .env.example

3. Run the server:
   python Backend/server.py

Frontend (Flutter):
Run the application with server configuration:
flutter run --dart-define=SERVER_BASE=http://<SERVER_IP>:5000
--dart-define=STREAM_URL=http://<STREAM_IP>:8080/?action=stream

---

PROJECT TYPE
Graduation Team Project

---

MY ROLE

-  Backend development using Flask
-  Sensor integration and system logic
-  Alert and notification system implementation
-  Flutter dashboard development
-  System testing and validation

---

NOTES

-  Sensitive credentials are not included in this repository.
-  Environment variables must be configured before running the system.
-  This repository is intended for academic and demonstration purposes.
