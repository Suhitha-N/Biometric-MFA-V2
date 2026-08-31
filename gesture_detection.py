"""Reusable gesture helper kept for compatibility with the original project.
The main authentication flow uses app.py and per-user models/gestures/<username>.pkl.
"""
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)


def get_finger_state(hand_landmarks):
    return [1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y else 0 for tip in [8, 12, 16, 20]]


def detect_pattern(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    if results.multi_hand_landmarks:
        return get_finger_state(results.multi_hand_landmarks[0])
    return None
