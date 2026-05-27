import cv2
import mediapipe as mp
import math
import time
import ctypes  # for locking Windows screen

# ── SETUP ──
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Eye landmark indices from MediaPipe's 468-point face mesh
# These are the specific points around each eye
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
LEFT_EYE_LEFT = 33
LEFT_EYE_RIGHT = 133

RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374
RIGHT_EYE_LEFT = 362
RIGHT_EYE_RIGHT = 263


def get_eye_aspect_ratio(landmarks, top, bottom, left, right, img_w, img_h):
    """
    Calculate how 'open' the eye is.
    Returns small number when eye is closed, big when open.
    """
    top_point = (landmarks[top].x * img_w, landmarks[top].y * img_h)
    bottom_point = (landmarks[bottom].x * img_w, landmarks[bottom].y * img_h)
    left_point = (landmarks[left].x * img_w, landmarks[left].y * img_h)
    right_point = (landmarks[right].x * img_w, landmarks[right].y * img_h)

    vertical = math.dist(top_point, bottom_point)
    horizontal = math.dist(left_point, right_point)

    return vertical / horizontal


# ── BLINK TRACKING ──
EAR_THRESHOLD = 0.20      # below this = eye is closed
BLINK_TIME_LIMIT = 2.0    # 3 blinks must happen within 2 seconds
BLINKS_TO_LOCK = 3        # how many blinks needed to lock

blink_timestamps = []     # stores when each blink happened
eye_closed = False        # tracks current state


def lock_screen():
    """Locks Windows screen."""
    print("🔒 LOCKING SCREEN")
    ctypes.windll.user32.LockWorkStation()


# ── MAIN LOOP ──
cap = cv2.VideoCapture(0)
print("BlinkLock running. Blink 3 times fast to lock. Press Q to quit.")

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    blink_count = 0

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        # Calculate eye openness for both eyes
        left_ear = get_eye_aspect_ratio(landmarks, LEFT_EYE_TOP, LEFT_EYE_BOTTOM,
                                         LEFT_EYE_LEFT, LEFT_EYE_RIGHT, w, h)
        right_ear = get_eye_aspect_ratio(landmarks, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM,
                                          RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT, w, h)
        avg_ear = (left_ear + right_ear) / 2

        # Detect blink: eye goes from open → closed → open
        if avg_ear < EAR_THRESHOLD:
            if not eye_closed:
                eye_closed = True   # eye just closed
        else:
            if eye_closed:
                # Eye just opened = a blink happened
                eye_closed = False
                blink_timestamps.append(time.time())
                print(f"BLINK! Total recent: {len([t for t in blink_timestamps if time.time() - t < BLINK_TIME_LIMIT])}")

        # Clean out old blinks (older than 2 sec ago)
        blink_timestamps = [t for t in blink_timestamps if time.time() - t < BLINK_TIME_LIMIT]
        blink_count = len(blink_timestamps)

        # If we hit 3 blinks → LOCK
        if blink_count >= BLINKS_TO_LOCK:
            blink_timestamps.clear()
            lock_screen()

        # Draw eye points on screen so you can see what's tracked
        for idx in [LEFT_EYE_TOP, LEFT_EYE_BOTTOM, LEFT_EYE_LEFT, LEFT_EYE_RIGHT,
                    RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM, RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT]:
            x = int(landmarks[idx].x * w)
            y = int(landmarks[idx].y * h)
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

    # Show blink counter on screen
    cv2.putText(frame, f"Blinks: {blink_count}/{BLINKS_TO_LOCK}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "Blink 3x fast to lock | Q to quit",
                (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("BlinkLock", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()