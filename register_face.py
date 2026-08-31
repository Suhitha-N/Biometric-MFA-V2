import cv2
import face_recognition
import os
import sys
import time

SAMPLES = 20
username = sys.argv[1] if len(sys.argv) > 1 else input("Enter username for face registration: ").strip()
if not username:
    raise SystemExit("Username is required")

path = os.path.join("dataset", "authorized_users", username)
os.makedirs(path, exist_ok=True)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise SystemExit("Camera not accessible")

count = 0
last_capture = 0.0
start = time.time()
try:
    while count < SAMPLES and time.time() - start < 60:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb, model="hog")
        display = frame.copy()
        for top, right, bottom, left in faces:
            cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(display, f"Face registration: {count}/{SAMPLES}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,255,0), 2)
        cv2.putText(display, "Keep exactly one face visible | ESC=cancel", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2)
        cv2.imshow("Register Face", display)

        now = time.time()
        if len(faces) == 1 and now - last_capture >= 0.35:
            cv2.imwrite(os.path.join(path, f"{count}.jpg"), frame)
            count += 1
            last_capture = now
        if cv2.waitKey(1) & 0xFF == 27:
            break
finally:
    cap.release()
    cv2.destroyAllWindows()

if count < SAMPLES:
    print("Face registration cancelled/incomplete")
    sys.exit(1)
print("Face registration complete")
