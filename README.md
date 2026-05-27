# 🔒 BlinkLock

> A privacy guard for your laptop. Auto-locks when you walk away or close your eyes.

Built with Python + MediaPipe + OpenCV. Runs entirely on your laptop — no cloud, no API keys, no internet required.

## What it does

BlinkLock watches your webcam in real-time and locks your screen automatically when:

- 👀 **You walk away** — no face detected for 3 seconds
- 😴 **You close your eyes** — manual lock by closing eyes for 2 seconds

It uses Google's MediaPipe Face Mesh to track 468 landmarks on your face in real-time, calculates the Eye Aspect Ratio (EAR) to detect closed eyes, and triggers a Windows system call to lock the workstation.

## Why I built this

I wanted to learn computer vision and build something actually useful. Most people leave their laptops unlocked when they get up. At cafes, libraries, and even at home, around guests. BlinkLock fixes that without any extra hardware. Just your webcam, doing what it's already doing, but smarter.

This is also my first real engineering project. I had zero coding experience when I started. I still have zero experience in coding. 

## How it works

**1. Webcam capture** — OpenCV reads frames from your camera in real-time.

**2. Face detection** — MediaPipe Face Mesh detects your face and maps 468 3D landmarks.

**3. Eye Aspect Ratio (EAR)** — We use the eye landmarks to calculate a ratio:
   - Open eye → high EAR (~0.30)
   - Closed eye → low EAR (~0.10)
   - Below threshold of 0.20 = closed

**4. State tracking** — The program tracks how long eyes have been closed or how long no face has been visible.

**5. Lock trigger** — When thresholds are hit, a Windows API call (`LockWorkStation`) locks the screen.

## Files in this repo

| File | What it does |
|------|--------------|
| `test_camera.py` | Hello world — opens webcam, draws full face mesh. Use this to verify setup works. |
| `blink_lock.py` | v1 — locks on 3 fast blinks (turned out to be triggered accidentally) |
| `blinklock_v2.py` | v2 — long blink + walk-away detection |
| `blinklock_final.py` | Final version with polished UI overlay |

## Run it yourself

### Requirements
- Python 3.13
- Windows (the lock function uses Windows API)
- A webcam

### Install

### Run

Press **Q** in the camera window to quit.

## Tunable settings

In `blinklock_final.py`:

```python
EAR_THRESHOLD = 0.20         # raise if blinks aren't detected
AWAY_LOCK_SECONDS = 3.0      # how long without a face before lock
LONG_BLINK_SECONDS = 2.0     # how long eyes must stay closed for manual lock
```


## What I learned

- Computer vision basics (face landmarks, image processing)
- Real-time state tracking in Python
- Calling system APIs (`ctypes`) to interact with the OS
- Iterating based on user testing (v1 → v2 → final)
- Reading library docs and debugging error messages

## What's next

- [ ] Face recognition — recognize the owner vs strangers
- [ ] Configurable settings via a small UI instead of editing code
- [ ] Mac and Linux support (different lock APIs)
- [ ] Package as a standalone .exe so non-coders can use it

## Built by

**Ulugbek Mirzarustamov** · 2026 · Tashkent, Uzbekistan

Part of my journey to ship 30 projects in 30 days, inspired by [Buildcored](https://buildcored.com).

[LinkedIn](https://www.linkedin.com/in/ulugbekmirzarustamov) · [Telegram](https://t.me/lifewithbekk) · [Email](mailto:umirzarustamov@gmail.com)

*MIT Licensed — free to use, modify, share.*
