# ONLY COMPATIBLE FOR MACBOOK ! BUT WITH MINOR CHANGES YOU CAN MAKE IT FOR WINDOW ALSO

import mediapipe as mp
import cv2
import subprocess
import time
import math
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# macOS COMPATIBILITY NOTE:
#  • Removed: pycaw, comtypes  (Windows-only audio COM libraries)
#  • Removed: pyautogui media key presses (unreliable on macOS)
#  • Added:   osascript (AppleScript via subprocess) for:
#               - Volume get/set via system volume settings
#               - Play/Pause, Next/Prev via DIRECT Spotify AppleScript commands
#                 (more reliable than System Events key codes on modern macOS)
# ─────────────────────────────────────────────────────────────────────────────

prev_time = 0
cooldown = 1.5

# ── macOS Volume Control via osascript ────────────────────────────────────────

def get_volume():
    """Get current system volume (0–100) using AppleScript."""
    result = subprocess.run(
        ["osascript", "-e", "output volume of (get volume settings)"],
        capture_output=True, text=True
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 50  # fallback

def volume_up():
    """Increase system volume by 5% using AppleScript."""
    current = get_volume()
    new_vol = min(current + 5, 100)
    subprocess.run(["osascript", "-e", f"set volume output volume {new_vol}"])

def volume_down():
    """Decrease system volume by 5% using AppleScript."""
    current = get_volume()
    new_vol = max(current - 5, 0)
    subprocess.run(["osascript", "-e", f"set volume output volume {new_vol}"])

# ── macOS Spotify Control via direct AppleScript ─────────────────────────────
# WHY: System Events key codes are unreliable with Spotify on modern macOS.
#      Talking directly to the Spotify app via AppleScript is the correct fix.

def play_pause():
    """Toggle play/pause directly in Spotify via AppleScript."""
    subprocess.run([
        "osascript", "-e",
        'tell application "Spotify" to playpause'
    ])

def next_song():
    """Skip to next track directly in Spotify via AppleScript."""
    subprocess.run([
        "osascript", "-e",
        'tell application "Spotify" to next track'
    ])

def prev_song():
    """Go to previous track directly in Spotify via AppleScript."""
    subprocess.run([
        "osascript", "-e",
        'tell application "Spotify" to previous track'
    ])

# ── MediaPipe & OpenCV Setup ──────────────────────────────────────────────────

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(1)

# ── Main Loop ─────────────────────────────────────────────────────────────────

while True:
    ret, img = cap.read()
    if not ret:
        print("⚠️  Camera not accessible. Exiting.")
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    if result.multi_hand_landmarks:

        for hand_landmark in result.multi_hand_landmarks:

            lm_list = []
            for id, lm in enumerate(hand_landmark.landmark):
                h, w, _ = img.shape
                lm_list.append((id, int(lm.x * w), int(lm.y * h)))

            fingers = []

            # Thumb (comparing x-coordinates for left/right direction)
            if lm_list[4][1] > lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            # Index, Middle, Ring, Pinky (comparing y-coordinates — tip vs base)
            for tip_id in [8, 12, 16, 20]:
                if lm_list[tip_id][2] < lm_list[tip_id - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            print("Fingers:", fingers)

            current_time = time.time()

            if current_time - prev_time > cooldown:

                if fingers == [0, 0, 0, 0, 0]:
                    play_pause()
                    print("🎵 Play/Pause")
                    prev_time = current_time

                elif fingers == [0, 1, 0, 0, 0]:
                    next_song()
                    print("⏭️  Next Song")
                    prev_time = current_time

                elif fingers == [0, 1, 1, 0, 0]:
                    prev_song()
                    print("⏮️  Previous Song")
                    prev_time = current_time

                elif fingers == [1, 0, 0, 0, 0]:
                    volume_up()
                    print("🔊 Volume Up")
                    prev_time = current_time

                elif fingers == [0, 0, 0, 0, 1]:
                    volume_down()
                    print("🔉 Volume Down")
                    prev_time = current_time

            mp_drawing.draw_landmarks(
                img,
                hand_landmark,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(128, 128, 128), thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=(0, 0, 0), thickness=2, circle_radius=2)
            )

    img = cv2.flip(img, 1)
    cv2.imshow("Hands", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()