import cv2
import mediapipe as mp
import pickle
import os
import sys
import time
import database

if len(sys.argv) < 2:
    sys.exit(2)
username = sys.argv[1]
model_path = os.path.join("models", "gestures", f"{username}.pkl")
if not os.path.exists(model_path):
    database.log_auth(username, "GESTURE", "ERROR", "Gesture not registered")
    print("Gesture not registered")
    sys.exit(1)

with open(model_path, "rb") as f:
    saved = pickle.load(f)
secret = saved.get("pattern")
if not isinstance(secret, list) or len(secret) != 4:
    database.log_auth(username, "GESTURE", "ERROR", "Invalid gesture model")
    sys.exit(1)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    database.log_auth(username, "GESTURE", "FAILED", "Camera unavailable")
    sys.exit(1)

REQUIRED_FRAMES = 8
TIMEOUT_SECONDS = 30
count = 0
start = time.time()


def get_pattern(hand):
    return [1 if hand.landmark[tip].y < hand.landmark[tip - 2].y else 0 for tip in [8,12,16,20]]

try:
    while time.time() - start < TIMEOUT_SECONDS:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)
        current = None
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            current = get_pattern(hand)
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            if current == secret:
                count += 1
            else:
                count = max(0, count - 1)

        cv2.putText(frame, "Show your registered gesture", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        cv2.putText(frame, f"Detected: {current}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255,255,255), 2)
        cv2.putText(frame, f"Progress: {count}/{REQUIRED_FRAMES}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame, "ESC = cancel", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.imshow("Gesture Verification", frame)

        if count >= REQUIRED_FRAMES:
            database.log_auth(username, "GESTURE", "SUCCESS", "Registered gesture matched")
            sys.exit(0)
        if cv2.waitKey(1) & 0xFF == 27:
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

database.log_auth(username, "GESTURE", "FAILED", "Verification timed out or cancelled")
sys.exit(1)
