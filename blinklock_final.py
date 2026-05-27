"""
BlinkLock — Privacy guard for your laptop
Built by Ulugbek Mirzarustamov · 2026
"""

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

LEFT_EYE = {"top": 159, "bottom": 145, "left": 33, "right": 133}
RIGHT_EYE = {"top": 386, "bottom": 374, "left": 362, "right": 263}

# ── CONFIG ──
EAR_THRESHOLD = 0.20
AWAY_LOCK_SECONDS = 3.0
LONG_BLINK_SECONDS = 2.0

# ── STATE ──
last_face_seen = time.time()
eyes_closed_since = None
status_text = "INITIALIZING"
status_color = (200, 200, 200)
progress = 0.0  # 0.0 to 1.0


def get_ear(landmarks, eye, w, h):
    top = (landmarks[eye["top"]].x * w, landmarks[eye["top"]].y * h)
    bot = (landmarks[eye["bottom"]].x * w, landmarks[eye["bottom"]].y * h)
    lft = (landmarks[eye["left"]].x * w, landmarks[eye["left"]].y * h)
    rgt = (landmarks[eye["right"]].x * w, landmarks[eye["right"]].y * h)
    return math.dist(top, bot) / math.dist(lft, rgt)


def lock_screen(reason):
    print(f"🔒 LOCKED — {reason}")
    ctypes.windll.user32.LockWorkStation()


def draw_overlay(frame, status, color, progress, w, h):
    """Draw a clean professional HUD."""
    # Dark top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 70), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # Logo "BlinkLock"
    cv2.putText(frame, "BlinkLock", (20, 30),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
    cv2.putText(frame, "v1.0", (160, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)

    # Status text
    cv2.putText(frame, status, (20, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

    # Progress bar (right side of top bar)
    bar_x, bar_y = w - 220, 25
    bar_w, bar_h = 200, 8
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h),
                  (60, 60, 60), -1)
    if progress > 0:
        fill_w = int(bar_w * min(progress, 1.0))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h),
                      color, -1)

    # Bottom bar — credit
    cv2.rectangle(overlay, (0, h - 35), (w, h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
    cv2.putText(frame, "Built by Ulugbek Mirzarustamov  ·  Press Q to quit",
                (20, h - 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)


# ── MAIN ──
cap = cv2.VideoCapture(0)
print("BlinkLock running. Press Q in the camera window to quit.")

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
        last_face_seen = now
        landmarks = results.multi_face_landmarks[0].landmark

        left_ear = get_ear(landmarks, LEFT_EYE, w, h)
        right_ear = get_ear(landmarks, RIGHT_EYE, w, h)
        avg_ear = (left_ear + right_ear) / 2

        if avg_ear < EAR_THRESHOLD:
            if eyes_closed_since is None:
                eyes_closed_since = now
            closed_duration = now - eyes_closed_since

            if closed_duration >= LONG_BLINK_SECONDS:
                lock_screen("Long blink")
                eyes_closed_since = None
                progress = 0.0
            else:
                status_text = f"EYES CLOSED — locking soon"
                status_color = (0, 165, 255)  # orange
                progress = closed_duration / LONG_BLINK_SECONDS
        else:
            eyes_closed_since = None
            status_text = "WATCHING — you're protected"
            status_color = (0, 255, 100)  # green
            progress = 0.0

        # Draw eye tracking dots
        for eye in [LEFT_EYE, RIGHT_EYE]:
            for key in ["top", "bottom", "left", "right"]:
                idx = eye[key]
                x = int(landmarks[idx].x * w)
                y = int(landmarks[idx].y * h)
                cv2.circle(frame, (x, y), 2, (0, 255, 100), -1)

    else:
        eyes_closed_since = None
        away_duration = now - last_face_seen

        if away_duration >= AWAY_LOCK_SECONDS:
            lock_screen("Walked away")
            last_face_seen = now
            progress = 0.0
        else:
            status_text = "NO FACE DETECTED — locking soon"
            status_color = (0, 100, 255)  # red-orange
            progress = away_duration / AWAY_LOCK_SECONDS

    draw_overlay(frame, status_text, status_color, progress, w, h)

    cv2.imshow("BlinkLock", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()