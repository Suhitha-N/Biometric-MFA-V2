# Biometric Multifactor Authentication - V2

## Authentication factors
1. Username + password (bcrypt)
2. Face recognition with repeated matches
3. Basic blink liveness check
4. Per-user secret hand gesture (MediaPipe)

## Security features
- SQLite database with automatic migration from the original project schema
- 3 failed-password attempts -> 5-minute temporary lock
- Structured authentication audit logs
- Intruder snapshots for repeated unknown faces
- OTP password reset with 5-minute expiry and 3 attempts
- Fernet encrypted personal file vault
- Safer temporary-file opening and cleanup
- Admin user management and security-log viewer

## Important project data
Keep these folders/files from your existing project when upgrading:
- `dataset/`
- `models/`
- `intruders/`
- `secure_files/`
- `secure_storage/`
- `users.db`
- `venv/` (do not copy/share it; recreate if necessary)

The Python source files in this V2 package can replace the matching source files in the existing project.

## Install
```bash
pip install -r requirements.txt
```

## Run
```bash
python gui_login.py
```

## First setup for a new user
Run the admin panel, authenticate as admin, then use **Add User + Register Biometrics**. The process registers the face, trains the face model, and registers the user's secret gesture.

## Face model
If you already have a working `models/faces.pkl`, it can be retained. If you change face datasets, run:
```bash
python train_faces.py
```

## Demo OTP
The OTP is intentionally a local demo. It is printed to the terminal. A production system should deliver OTP through a verified email/SMS provider.

## Notes
- The blink check is a basic liveness demonstration, not a high-assurance anti-spoofing system.
- The per-user Fernet key is stored in that user's vault folder for this academic project. Production systems should use a dedicated key-management system.
