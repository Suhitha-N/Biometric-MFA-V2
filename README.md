# 🔐 Biometric Multifactor Authentication - V2

A secure desktop-based **Multifactor Authentication (MFA)** system using password authentication, face recognition, blink-based liveness detection, and a user-specific secret hand gesture.

The project also provides a secure biometric file vault, OTP-based password reset, authentication logging, intruder detection, and administrator controls.

---

## ✨ Features

### Authentication Factors

1. Username + Password using bcrypt
2. Face Recognition with repeated matches
3. Basic Blink Liveness Detection
4. Per-user Secret Hand Gesture using MediaPipe

All authentication factors must be successfully verified before access is granted.

---

## 🛡️ Security Features

- SQLite database with automatic migration from the original project schema
- bcrypt password hashing
- 3 failed-password attempts → 5-minute temporary lock
- Structured authentication audit logs
- Intruder snapshots for repeated unknown faces
- OTP password reset with 5-minute expiry
- Maximum 3 OTP verification attempts
- Fernet-encrypted personal file vault
- Safer temporary-file opening and cleanup
- Admin user management
- Security-log viewer

---

## 🏗️ Project Structure

```text
Biometric-MFA-V2/
│
├── screenshots/
│   ├── 01_login_screen.png
│   ├── 02_face_verification.png
│   ├── 03_gesture_verification.png
│   ├── 04_successful_authentication.png
│   ├── 05_secure_biometric_vault.png
│   ├── 06_gesture_failed.png
│   └── 07_face_failed.png
│
├── admin_panel.py
├── app.py
├── dashboard.py
├── database.py
├── face_auth.py
├── gesture_detection.py
├── gesture_register.py
├── gui_login.py
├── password_reset.py
├── register_face.py
├── reset_user.py
├── run.py
├── test_camera.py
├── train_faces.py
│
├── haarcascade_frontalface_default.xml
├── requirements.txt
├── .gitignore
└── README.md