import cv2
import os
import sys
import pickle
import time
import numpy as np
import face_recognition
import database


# ============================================================
# INPUT
# ============================================================

if len(sys.argv) < 2:
    print("Usage: python face_auth.py <username>")
    sys.exit(2)

username = sys.argv[1].strip()

os.makedirs("intruders", exist_ok=True)


# ============================================================
# LOAD TRAINED FACE MODEL
# ============================================================

try:
    model_path = os.path.join("models", "faces.pkl")

    with open(model_path, "rb") as f:
        data = pickle.load(f)

    known_encodings = data.get("encodings", [])
    known_names = data.get("names", [])

except Exception as exc:

    print("ERROR: Face model could not be loaded.")
    print(exc)

    database.log_auth(
        username,
        "FACE",
        "ERROR",
        f"Face model unavailable: {exc}"
    )

    sys.exit(1)


if not known_encodings or len(known_encodings) != len(known_names):

    print("ERROR: No valid trained face model.")

    database.log_auth(
        username,
        "FACE",
        "ERROR",
        "No valid trained face model"
    )

    sys.exit(1)


# ============================================================
# SETTINGS
# ============================================================

# Lower value = stricter face matching
FACE_THRESHOLD = 0.45

# Number of successful face frames required
REQUIRED_MATCHES = 5

# Maximum verification time
TIMEOUT_SECONDS = 30

# Blink detection thresholds
#
# Normal open eyes should generally be above EAR_OPEN.
# Closed eyes should generally fall below EAR_CLOSED.
#
# Your previous readings were around:
# 0.13 - 0.18 normally
# 0.21 - 0.24 when eyes were more open.
#
# Therefore we use a conservative threshold.
EAR_CLOSED = 0.17
EAR_OPEN = 0.20


# ============================================================
# EYE ASPECT RATIO
# ============================================================

def calculate_ear(eye):
    """
    Calculate Eye Aspect Ratio.

    The 'large' face landmark model provides
    6 points for each eye.
    """

    if len(eye) != 6:
        return 1.0

    p = np.asarray(eye, dtype=np.float32)

    vertical1 = np.linalg.norm(p[1] - p[5])
    vertical2 = np.linalg.norm(p[2] - p[4])

    horizontal = np.linalg.norm(p[0] - p[3])

    if horizontal == 0:
        return 1.0

    return float(
        (vertical1 + vertical2) /
        (2.0 * horizontal)
    )


# ============================================================
# GET EYE EAR
# ============================================================

def get_eye_ear(rgb, face_location):
    """
    Get average EAR using the LARGE landmark model.

    Important:
    face_recognition 'small' model gives only 2 points
    per eye, so it cannot be used for EAR calculation.

    The 'large' model gives 6 points per eye.
    """

    try:

        marks = face_recognition.face_landmarks(
            rgb,
            [face_location],
            model="large"
        )

        if not marks:
            return None

        face = marks[0]

        left_eye = face.get("left_eye", [])
        right_eye = face.get("right_eye", [])

        if len(left_eye) != 6 or len(right_eye) != 6:
            return None

        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)

        avg_ear = (left_ear + right_ear) / 2.0

        return avg_ear

    except Exception as exc:

        print(f"Landmark error: {exc}")

        return None


# ============================================================
# OPEN CAMERA
# ============================================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():

    print("Camera 0 could not be opened.")
    print("Trying camera 1...")

    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)


if not cap.isOpened():

    print("ERROR: Camera unavailable.")

    database.log_auth(
        username,
        "FACE",
        "FAILED",
        "Camera unavailable"
    )

    sys.exit(1)


# ============================================================
# VARIABLES
# ============================================================

matches = 0

unknown_frames = 0

blink_closed_seen = False

# Used to make sure we saw an OPEN eye state
# before accepting a CLOSED state as a blink.
blink_was_open = False

start = time.time()

last_frame = None


# ============================================================
# FACE VERIFICATION
# ============================================================

try:

    while time.time() - start < TIMEOUT_SECONDS:

        ret, frame = cap.read()

        if not ret:
            continue

        last_frame = frame.copy()

        # ----------------------------------------------------
        # Convert BGR -> RGB
        # ----------------------------------------------------

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # ----------------------------------------------------
        # Detect faces
        # ----------------------------------------------------

        locations = face_recognition.face_locations(
            rgb,
            model="hog"
        )

        encodings = face_recognition.face_encodings(
            rgb,
            locations
        )

        name = "Unknown"

        best_distance = None

        best_location = None


        # ====================================================
        # FACE MATCHING
        # ====================================================

        if encodings:

            distances = face_recognition.face_distance(
                known_encodings,
                encodings[0]
            )

            best = int(np.argmin(distances))

            best_distance = float(distances[best])

            best_location = locations[0]

            if best_distance <= FACE_THRESHOLD:

                name = known_names[best]


        # ====================================================
        # AUTHORIZED USER DETECTED
        # ====================================================

        if name == username:

            matches += 1

            unknown_frames = 0


            # ------------------------------------------------
            # BLINK / LIVENESS DETECTION
            # ------------------------------------------------

            if best_location is not None:

                avg_ear = get_eye_ear(
                    rgb,
                    best_location
                )

                if avg_ear is not None:

                    print(
                        f"EAR: {avg_ear:.3f}"
                    )

                    # ----------------------------------------
                    # Eyes are OPEN
                    # ----------------------------------------

                    if avg_ear >= EAR_OPEN:

                        blink_was_open = True


                    # ----------------------------------------
                    # Eyes are CLOSED after being OPEN
                    # ----------------------------------------

                    if (
                        blink_was_open
                        and avg_ear < EAR_CLOSED
                    ):

                        blink_closed_seen = True


        # ====================================================
        # UNKNOWN USER
        # ====================================================

        else:

            matches = 0

            if encodings:

                unknown_frames += 1


        # ====================================================
        # INTRUDER DETECTION
        # ====================================================

        if (
            unknown_frames >= 15
            and last_frame is not None
        ):

            filename = (
                f"intruder_"
                f"{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            )

            filepath = os.path.join(
                "intruders",
                filename
            )

            cv2.imwrite(
                filepath,
                last_frame
            )

            database.log_auth(
                username,
                "FACE",
                "INTRUDER",
                filename
            )

            print(
                f"Intruder snapshot saved: {filename}"
            )

            unknown_frames = 0


        # ====================================================
        # STATUS
        # ====================================================

        if name == username:

            user_status = f"User: {name}"

        else:

            user_status = "User: Unknown"


        if blink_closed_seen:

            live_status = "Liveness detected"

        elif blink_was_open:

            live_status = "Blink once"

        else:

            live_status = "Open eyes"


        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.putText(
            frame,
            user_status,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            f"Face matches: {matches}/{REQUIRED_MATCHES}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )


        cv2.putText(
            frame,
            f"Liveness: {live_status}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            "Blink once while facing camera",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            "ESC = Cancel",
            (20, 175),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )


        # ----------------------------------------------------
        # Show camera
        # ----------------------------------------------------

        cv2.imshow(
            "Face Verification",
            frame
        )


        # ====================================================
        # SUCCESS CONDITION
        # ====================================================

        if (
            matches >= REQUIRED_MATCHES
            and blink_closed_seen
        ):

            print()
            print("================================")
            print("FACE AUTHENTICATION SUCCESSFUL")
            print("Face match: PASSED")
            print("Blink liveness: PASSED")
            print("================================")
            print()

            database.log_auth(
                username,
                "FACE",
                "SUCCESS",
                "Face match and blink liveness passed"
            )

            sys.exit(0)


        # ====================================================
        # ESC CANCEL
        # ====================================================

        key = cv2.waitKey(1) & 0xFF

        if key == 27:

            print("Face verification cancelled.")

            break


finally:

    cap.release()

    cv2.destroyAllWindows()


# ============================================================
# VERIFICATION FAILED
# ============================================================

database.log_auth(
    username,
    "FACE",
    "FAILED",
    "Verification timed out or cancelled"
)

print()
print("================================")
print("FACE AUTHENTICATION FAILED")
print("================================")
print()

sys.exit(1)