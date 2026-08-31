import face_recognition
import os
import pickle

DATASET = os.path.join("dataset", "authorized_users")
MODEL = os.path.join("models", "faces.pkl")

if not os.path.isdir(DATASET):
    raise SystemExit("No face dataset found")

known_encodings = []
known_names = []

print("Training faces...")
for user in sorted(os.listdir(DATASET)):
    folder = os.path.join(DATASET, user)
    if not os.path.isdir(folder):
        continue
    for img in sorted(os.listdir(folder)):
        if not img.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(folder, img)
        try:
            image = face_recognition.load_image_file(path)
            locations = face_recognition.face_locations(image, model="hog")
            if len(locations) != 1:
                continue
            enc = face_recognition.face_encodings(image, locations)
            if enc:
                known_encodings.append(enc[0])
                known_names.append(user)
        except Exception as exc:
            print(f"Skipping {path}: {exc}")

if not known_encodings:
    raise SystemExit("No usable face encodings found. Register a face first.")

os.makedirs("models", exist_ok=True)
with open(MODEL, "wb") as f:
    pickle.dump({"encodings": known_encodings, "names": known_names}, f)
print(f"Training completed: {len(known_encodings)} face encodings")
