import math
import random
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
import numpy as np

# ---------------- CONFIG ----------------
WHEEL_SIZE = 800                 # Wheel diameter
SPIN_DURATION = 5                # Spin duration in seconds
FPS = 30                         # Video FPS
OUTPUT_FILE = "/data/data/com.termux/files/home/storage/downloads/spin_wheel_reel.mp4"
FONT_SIZE = 28                    # Username font size
WINNER_FONT_SIZE = 100            # Winner text size
ARROW_SIZE = 50                    # Arrow length

# ---------------- LOAD USERNAMES ----------------
with open("usernames.txt", "r") as f:
    usernames = [line.strip() for line in f.readlines() if line.strip()]

num_users = len(usernames)
if num_users == 0:
    raise ValueError("No usernames in usernames.txt")

angle_per_slice = 360 / num_users

# ---------------- CREATE WHEEL IMAGE ----------------
def create_wheel_image(usernames):
    img = Image.new("RGB", (WHEEL_SIZE, WHEEL_SIZE), "black")
    draw = ImageDraw.Draw(img)
    center = WHEEL_SIZE // 2
    radius = WHEEL_SIZE // 2 - 50  # margin

    # Draw circle
    draw.ellipse([center-radius, center-radius, center+radius, center+radius], outline="white", width=4)

    # Draw lines and usernames
    for i, name in enumerate(usernames):
        angle_deg = i * angle_per_slice
        angle_rad = math.radians(angle_deg - 90)  # start from top

        # Line
        x = center + radius * math.cos(angle_rad)
        y = center + radius * math.sin(angle_rad)
        draw.line([center, center, x, y], fill="white", width=3)

        # Username position
        text_radius = radius + 30
        text_x = center + text_radius * math.cos(angle_rad)
        text_y = center + text_radius * math.sin(angle_rad)

        # Draw username
        try:
            font = ImageFont.truetype("/data/data/com.termux/files/usr/share/fonts/DejaVuSans.ttf", FONT_SIZE)
        except:
            font = ImageFont.load_default()
        text_w, text_h = draw.textsize(name, font=font)
        draw.text((text_x - text_w/2, text_y - text_h/2), name, fill="white", font=font)

    return img

wheel_img = create_wheel_image(usernames)
wheel_clip = ImageClip(np.array(wheel_img)).set_duration(SPIN_DURATION).resize(width=500)

# ---------------- ADD ARROW ----------------
arrow_img = Image.new("RGBA", (WHEEL_SIZE, WHEEL_SIZE), (0,0,0,0))
draw_arrow = ImageDraw.Draw(arrow_img)
center = WHEEL_SIZE//2
draw_arrow.polygon([
    (center, 0),
    (center-15, ARROW_SIZE),
    (center+15, ARROW_SIZE)
], fill="red")
arrow_clip = ImageClip(np.array(arrow_img)).set_duration(SPIN_DURATION).resize(width=500)

# ---------------- PICK WINNER ----------------
winner_index = random.randint(0, num_users-1)
winner = usernames[winner_index]
print("Winner is:", winner)

# ---------------- SPIN ANIMATION ----------------
# Calculate final angle so winner is at top under arrow
final_angle = 360 * 5 + (360 - winner_index * angle_per_slice - angle_per_slice/2)  # 5 full spins + offset

def spin(get_frame, t):
    progress = t / SPIN_DURATION
    # Ease out rotation
    angle = final_angle * (1 - (1 - progress)**3)
    frame = wheel_clip.get_frame(0)
    pil_frame = Image.fromarray(frame).rotate(angle, resample=Image.BICUBIC, expand=False)
    return np.array(pil_frame)

spinning = wheel_clip.fl(spin, apply_to=['mask'])
spinning = CompositeVideoClip([spinning, arrow_clip])

# ---------------- WINNER REVEAL ----------------
winner_clip = TextClip(f"{winner} WINS!", fontsize=WINNER_FONT_SIZE, color='yellow', method='label')\
               .set_duration(3).set_position('center')

# ---------------- FINAL VIDEO ----------------
final = concatenate_videoclips([spinning, winner_clip])
final.write_videofile(OUTPUT_FILE, fps=FPS)
