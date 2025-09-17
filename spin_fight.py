import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, ImageClip, CompositeVideoClip

# ===== Settings =====
WIDTH, HEIGHT = 720, 720
FPS = 30
DURATION = 5   # spin duration in seconds
FINAL_HOLD = 3 # seconds showing winner
ARROW_SIZE = 40
WINNER_FONT_SIZE = 90

# ===== Load usernames =====
with open("usernames.txt", "r") as f:
    usernames = [line.strip() for line in f if line.strip()]

if not usernames:
    raise ValueError("No usernames found in usernames.txt")

# ===== Create wheel image =====
def make_wheel(names):
    n = len(names)
    angle_per_slice = 360 / n
    radius = WIDTH // 2

    img = Image.new("RGB", (WIDTH, HEIGHT), "black")
    draw = ImageDraw.Draw(img)

    for i, name in enumerate(names):
        start_angle = i * angle_per_slice
        end_angle = start_angle + angle_per_slice
        color = (100 + (i * 40) % 155, 50 + (i * 80) % 205, 150 + (i * 120) % 105)
        draw.pieslice([0, 0, WIDTH, HEIGHT], start=start_angle, end=end_angle, fill=color)

        # Place text
        angle_rad = math.radians(start_angle + angle_per_slice / 2)
        x = WIDTH / 2 + (radius / 1.5) * math.cos(angle_rad)
        y = HEIGHT / 2 + (radius / 1.5) * math.sin(angle_rad)
        font = ImageFont.load_default()
        draw.text((x, y), name, fill="white", anchor="mm", font=font)

    return img

# ===== Add arrow =====
def add_arrow(img):
    draw = ImageDraw.Draw(img)
    cx = WIDTH // 2
    arrow = [(cx - ARROW_SIZE, 10), (cx + ARROW_SIZE, 10), (cx, ARROW_SIZE * 2)]
    draw.polygon(arrow, fill="red")
    return img

# ===== Spin animation =====
wheel_img = make_wheel(usernames)
wheel_img = add_arrow(wheel_img)

frames = []
total_frames = DURATION * FPS
winner = random.choice(usernames)
winner_index = usernames.index(winner)
angle_per_slice = 360 / len(usernames)

# Final angle: winner under arrow at 90°
final_angle = 90 - (winner_index * angle_per_slice + angle_per_slice / 2)

for i in range(total_frames):
    progress = i / total_frames
    rotation = (1 - (progress ** 2)) * 720 + final_angle  # ease out
    rotated = wheel_img.rotate(rotation, resample=Image.BICUBIC)
    frames.append(np.array(rotated))  # PIL → numpy

# ===== Build spin clip =====
clip = ImageSequenceClip(frames, fps=FPS)

# ===== Winner text with Pillow (NO IMAGEMAGICK) =====
def make_text_image(text, fontsize=90, color="yellow"):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()  # use default font
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((WIDTH - w) / 2, (HEIGHT - h) / 2), text, font=font, fill=color)
    return img

winner_img = make_text_image(f"{winner} WINS!", fontsize=WINNER_FONT_SIZE)
winner_clip = ImageClip(np.array(winner_img)).set_duration(FINAL_HOLD)

final_video = CompositeVideoClip([clip, winner_clip.set_start(DURATION)])

# ===== Export =====
final_video.write_videofile("spin_fight_reel.mp4", fps=FPS)

print(f"Winner is: {winner}")
