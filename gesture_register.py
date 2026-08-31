import cv2
import mediapipe as mp
import pickle
import os
import sys
from collections import Counter

username = sys.argv[1] if len(sys.argv) > 1 else input("Enter username: ").strip()
if not username:
    raise SystemExit("Username is required")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise SystemExit("Camera not accessible")


def get_pattern(hand):
    return [1 if hand.landmark[tip].y < hand.landmark[tip - 2].y else 0 for tip in [8, 12, 16, 20]]

patterns = []
last_pattern = None
stable_frames = 0
try:
    while len(patterns) < 30:
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
            if current == last_pattern:
                stable_frames += 1
            else:
                stable_frames = 1
                last_pattern = current
            if stable_frames >= 3:
                patterns.append(current)
                stable_frames = 0
        cv2.putText(frame, f"Samples: {len(patterns)}/30", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.putText(frame, "Hold one secret hand gesture | Q=finish", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.imshow("Register Gesture", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if len(patterns) < 10:
    raise SystemExit("Not enough gesture samples")

secret = list(Counter(tuple(p) for p in patterns).most_common(1)[0][0])
os.makedirs(os.path.join("models", "gestures"), exist_ok=True)
with open(os.path.join("models", "gestures", f"{username}.pkl"), "wb") as f:
    pickle.dump({"pattern": secret}, f)
print(f"Gesture registered for {username}")
