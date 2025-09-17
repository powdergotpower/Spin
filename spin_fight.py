import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip, ImageClip, concatenate_videoclips

# ---------------- CONFIG ----------------
WHEEL_SIZE = 800
FONT_PATH = "/data/data/com.termux/files/usr/share/fonts/DejaVuSans.ttf"
ARROW_SIZE = 40
SPIN_DURATION = 5   # seconds of spin animation
STOP_HOLD = 2       # seconds to pause on stopped wheel
FPS = 30
WINNER_FONT_SIZE = 90

# ---------------- LOAD USERNAMES ----------------
with open("usernames.txt", "r") as f:
    usernames = [line.strip() for line in f if line.strip()]

if not usernames:
    raise ValueError("No usernames found in usernames.txt!")

# ---------------- DRAW WHEEL ----------------
def create_wheel(usernames):
    n = len(usernames)
    angle_per_slice = 360 / n
    img = Image.new("RGBA", (WHEEL_SIZE, WHEEL_SIZE), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    center = WHEEL_SIZE // 2
    radius = center - 10

    for i, name in enumerate(usernames):
        start_angle = i * angle_per_slice
        end_angle = (i + 1) * angle_per_slice
        color = (100 + (i*40) % 155, 100 + (i*80) % 155, 200, 255)
        draw.pieslice([10, 10, WHEEL_SIZE-10, WHEEL_SIZE-10],
                      start=start_angle, end=end_angle,
                      fill=color, outline="white")

        # Separator line
        rad = math.radians(start_angle)
        x = center + radius * math.cos(rad)
        y = center + radius * math.sin(rad)
        draw.line((center, center, x, y), fill="white", width=3)

        # Username text
        text_angle = start_angle + angle_per_slice / 2
        rad = math.radians(text_angle)
        tx = center + (radius/1.5) * math.cos(rad)
        ty = center + (radius/1.5) * math.sin(rad)
        try:
            font = ImageFont.truetype(FONT_PATH, 24)
        except:
            font = ImageFont.load_default()
        tw, th = draw.textsize(name, font=font)
        draw.text((tx - tw/2, ty - th/2), name, font=font, fill="black")

    return img

wheel_img = create_wheel(usernames)
wheel_img.save("wheel.png")

# ---------------- WINNER SELECTION ----------------
winner = random.choice(usernames)
winner_index = usernames.index(winner)
print(f"Winner is: {winner}")

# Final stop angle so arrow points to winner
angle_per_slice = 360 / len(usernames)
target_angle = 90 - (winner_index * angle_per_slice + angle_per_slice/2)

# ---------------- ARROW ----------------
def draw_arrow():
    img = Image.new("RGBA", (WHEEL_SIZE, WHEEL_SIZE), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = WHEEL_SIZE // 2
    draw.polygon([(cx-ARROW_SIZE, 20), (cx+ARROW_SIZE, 20), (cx, 80)], fill="red")
    return img
arrow_img = draw_arrow()

# ---------------- SPIN ANIMATION ----------------
wheel_np = np.array(wheel_img)

def make_spin_frame(t):
    progress = min(1, t / SPIN_DURATION)
    eased = 1 - (1-progress)**3  # ease-out
    rotation = 1440*(1-progress) + target_angle  # 4 spins then stop
    rotated = Image.fromarray(wheel_np).rotate(rotation, resample=Image.BICUBIC,
                                               center=(WHEEL_SIZE//2, WHEEL_SIZE//2), expand=False)
    frame = Image.new("RGB", (WHEEL_SIZE, WHEEL_SIZE), "black")
    frame.paste(rotated, (0,0), rotated)
    frame.paste(arrow_img, (0,0), arrow_img)
    return np.array(frame)

spin_clip = VideoClip(make_spin_frame, duration=SPIN_DURATION)

# ---------------- STOPPED WHEEL ----------------
stopped_frame = make_spin_frame(SPIN_DURATION)
stopped_clip = ImageClip(stopped_frame).set_duration(STOP_HOLD)

# ---------------- WINNER REVEAL ----------------
def make_winner_frame(t):
    img = Image.new("RGB", (WHEEL_SIZE, WHEEL_SIZE), "black")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, WINNER_FONT_SIZE)
    except:
        font = ImageFont.load_default()
    text = f"{winner} WINS!"
    tw, th = draw.textsize(text, font=font)
    draw.text(((WHEEL_SIZE-tw)//2, (WHEEL_SIZE-th)//2),
              text, font=font, fill="yellow")
    return np.array(img)

winner_clip = VideoClip(make_winner_frame, duration=3)

# ---------------- EXPORT VIDEO ----------------
final = concatenate_videoclips([spin_clip, stopped_clip, winner_clip])
final.write_videofile("spin_fight_reel.mp4", fps=FPS, codec="libx264")
