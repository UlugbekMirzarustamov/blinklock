import cv2
import mediapipe as mp
import math
import time
import ctypes

# ── SETUP ──
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Eye landmark indices
LEFT_EYE = {"top": 159, "bottom": 145, "left": 33, "right": 133}
RIGHT_EYE = {"top": 386, "bottom": 374, "left": 362, "right": 263}

# ── CONFIG (tune these) ──
EAR_THRESHOLD = 0.20            # below this = eye closed
AWAY_LOCK_SECONDS = 3.0         # lock if no face seen for this long
LONG_BLINK_SECONDS = 1.4     # lock if eyes closed for this long

# ── STATE TRACKING ──
last_face_seen = time.time()
eyes_closed_since = None
locked = False
status = "INITIALIZING"


def get_ear(landmarks, eye, w, h):
    """Eye Aspect Ratio — how open the eye is."""
    top = (landmarks[eye["top"]].x * w, landmarks[eye["top"]].y * h)
    bot = (landmarks[eye["bottom"]].x * w, landmarks[eye["bottom"]].y * h)
    lft = (landmarks[eye["left"]].x * w, landmarks[eye["left"]].y * h)
    rgt = (landmarks[eye["right"]].x * w, landmarks[eye["right"]].y * h)
    return math.dist(top, bot) / math.dist(lft, rgt)


def lock_screen(reason):
    """Lock Windows."""
    print(f"🔒 LOCKING SCREEN — Reason: {reason}")
    ctypes.windll.user32.LockWorkStation()


# ── MAIN LOOP ──
cap = cv2.VideoCapture(0)
print("BlinkLock v2 running.")
print(f"  → Auto-lock if you look away for {AWAY_LOCK_SECONDS}s")
print(f"  → Manual lock: close eyes for {LONG_BLINK_SECONDS}s")
print(f"  → Press Q to quit")

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    now = time.time()

    if results.multi_face_landmarks:
        # FACE DETECTED
        last_face_seen = now
        landmarks = results.multi_face_landmarks[0].landmark

        left_ear = get_ear(landmarks, LEFT_EYE, w, h)
        right_ear = get_ear(landmarks, RIGHT_EYE, w, h)
        avg_ear = (left_ear + right_ear) / 2

        # Check if eyes closed
        if avg_ear < EAR_THRESHOLD:
            if eyes_closed_since is None:
                eyes_closed_since = now  # eyes just closed
            closed_duration = now - eyes_closed_since

            if closed_duration >= LONG_BLINK_SECONDS:
                lock_screen("Long blink")
                eyes_closed_since = None
            else:
                status = f"😴 EYES CLOSED ({closed_duration:.1f}s / {LONG_BLINK_SECONDS}s)"
        else:
            eyes_closed_since = None
            status = "👀 WATCHING YOU"

        # Draw eye dots
        for eye in [LEFT_EYE, RIGHT_EYE]:
            for key in ["top", "bottom", "left", "right"]:
                idx = eye[key]
                x = int(landmarks[idx].x * w)
                y = int(landmarks[idx].y * h)
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

    else:
        # NO FACE
        eyes_closed_since = None
        away_duration = now - last_face_seen

        if away_duration >= AWAY_LOCK_SECONDS:
            lock_screen("Walked away")
            last_face_seen = now  # reset so it doesn't spam
        else:
            status = f"🚪 NO FACE ({away_duration:.1f}s / {AWAY_LOCK_SECONDS}s)"

    # ── HUD overlay ──
    # Top status bar
    cv2.rectangle(frame, (0, 0), (w, 50), (0, 0, 0), -1)
    cv2.putText(frame, status, (15, 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Bottom hint
    cv2.rectangle(frame, (0, h - 30), (w, h), (0, 0, 0), -1)
    cv2.putText(frame, "BlinkLock v2 — Q to quit",
                (15, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("BlinkLock v2", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()