import mediapipe as mp
import cv2
import pyautogui
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import time
import math
import numpy as np

prev_time = 0
cooldown = 1.5

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_control = cast(interface, POINTER(IAudioEndpointVolume))

def volume_up():
    current = volume_control.GetMasterVolumeLevelScalar()
    volume_control.SetMasterVolumeLevelScalar(min(current + 0.05, 1.0), None)

def volume_down():
    current = volume_control.GetMasterVolumeLevelScalar()
    volume_control.SetMasterVolumeLevelScalar(max(current - 0.05, 0.0), None)

def play_pause():
   pyautogui.press('playpause')
def next_song():
   pyautogui.press('nexttrack')
def prev_song():
   pyautogui.press('prevtrack')

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode = False,
    max_num_hands = 2,
    min_detection_confidence = 0.5,
    min_tracking_confidence = 0.5
)

cap = cv2.VideoCapture(0)

while True:
    frame , img = cap.read()
    img_rgb = cv2.cvtColor(img , cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    img = cv2.cvtColor(img_rgb , cv2.COLOR_RGB2BGR)

    if result.multi_hand_landmarks:

        for hand_landmark in result.multi_hand_landmarks:

            lm_list = []
            for id, lm in enumerate(hand_landmark.landmark):
               h,w,_ = img.shape
               lm_list.append((id, int(lm.x*w),int(lm.y*h)))

            fingers = []

            # Thumb
            if lm_list[4][1] > lm_list[3][1]:
               fingers.append(1)
            else:
               fingers.append(0)

            # Finger
            for tip_id in [8,12,16,20]:
               if lm_list[tip_id][2] < lm_list[tip_id-2][2]:
                fingers.append(1)
               else:
                  fingers.append(0)

            print("Fingers", fingers)

            current_time = time.time()

            if current_time - prev_time > cooldown:
                if fingers == [0, 0, 0, 0, 0]:
                    play_pause()
                    print("🎵 Play/Pause")
                    prev_time = current_time

                elif fingers == [0, 1, 0, 0, 0]:
                    next_song()
                    print("⏭️ Next Song")
                    prev_time = current_time

                elif fingers == [0, 1, 1, 0, 0]:
                    prev_song()
                    print("⏮️ Previous Song")
                    prev_time = current_time

                elif fingers == [1, 0, 0, 0, 0]:
                    volume_up()
                    print("🔊 Volume Up")
                    prev_time = current_time

                elif fingers == [0, 0, 0, 0, 1]:  # pinky up, temporary for volume down
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