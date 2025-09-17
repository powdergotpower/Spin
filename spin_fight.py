import random
from moviepy.editor import *
from PIL import Image, ImageDraw
import numpy as np

# ----- CONFIG -----
WHEEL_SIZE = 800       # Wheel image size in pixels
SPIN_DURATION = 5      # Spin duration in seconds
FPS = 30               # Frames per second
OUTPUT_FILE = "spin_fight_reel.mp4"

# ----- LOAD USERNAMES -----
with open("usernames.txt", "r") as f:
    usernames = [line.strip() for line in f.readlines() if line.strip()]

num_users = len(usernames)
if num_users == 0:
    raise ValueError("No usernames found in usernames.txt")

# ----- CREATE BASIC WHEEL IMAGE (without text) -----
def create_wheel(num_slices):
    wheel = Image.new("RGB", (WHEEL_SIZE, WHEEL_SIZE), (255, 255, 255))
    draw = ImageDraw.Draw(wheel)
    angle_per_slice = 360 / num_slices
    for i in range(num_slices):
        start_angle = i * angle_per_slice
        end_angle = start_angle + angle_per_slice
        color = (255, 200, 0) if i % 2 == 0 else (255, 150, 0)
        draw.pieslice([0,0,WHEEL_SIZE,WHEEL_SIZE], start=start_angle, end=end_angle, fill=color)
    return wheel

wheel_img = create_wheel(num_users)
wheel_img.save("wheel.png")  # Optional: see the wheel image

# ----- CONVERT WHEEL TO MOVIEPY CLIP -----
wheel_clip = ImageClip(np.array(wheel_img)).set_duration(SPIN_DURATION).resize(width=500)

# ----- SPIN ANIMATION -----
def spin(get_frame, t):
    progress = t / SPIN_DURATION
    angle = 720*progress*(1-progress) + random.randint(0,360)  # spins + random offset
    frame = wheel_clip.get_frame(0)
    pil_frame = Image.fromarray(frame).rotate(angle, resample=Image.BICUBIC, expand=False)
    return np.array(pil_frame)

spinning = wheel_clip.fl(spin, apply_to=['mask'])

# ----- PICK RANDOM WINNER -----
winner = random.choice(usernames)
print("Winner is:", winner)

# ----- CREATE WINNER TEXT CLIP -----
winner_clip = TextClip(f"{winner} WINS!", fontsize=70, color='yellow', font='DejaVu-Sans-Bold')\
               .set_duration(3).set_position('center')

# ----- COMBINE SPIN + WINNER -----
final = concatenate_videoclips([spinning, winner_clip])

# ----- EXPORT VIDEO -----
final.write_videofile(OUTPUT_FILE, fps=FPS)
