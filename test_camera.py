import cv2
import mediapipe as mp

# Setup MediaPipe Face Mesh — Google's free face tracking AI
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Drawing helper
mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(0, 255, 0))

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)

print("Camera opened. Press Q to quit.")

while True:
    success, frame = cap.read()
    if not success:
        print("Camera failed to read frame")
        break

    # Flip the image so it acts like a mirror
    frame = cv2.flip(frame, 1)

    # MediaPipe needs RGB, OpenCV uses BGR — convert
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run face detection
    results = face_mesh.process(rgb_frame)

    # If a face is detected, draw the mesh on it
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=drawing_spec,
                connection_drawing_spec=drawing_spec
            )

    # Show the result
    cv2.imshow("BlinkLock - Camera Test", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()