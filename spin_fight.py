#!/usr/bin/env python3
# spin_fight_portrait.py — Termux vertical HD spin wheel, max quality
# Requires: pillow, moviepy, numpy
# Install: pip install pillow moviepy numpy

import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, ImageClip, CompositeVideoClip

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1080, 1920       # Portrait HD
RADIUS = 500
FPS = 60                         # Smooth 60 FPS
SPIN_DURATION = 6.0
HOLD_DURATION = 2.0
WINNER_DURATION = 4.0
SPINS = 6
OUTPUT_NAME = "spin_result_portrait.mp4"
# ---------------------------------------

def find_font():
    candidates = [
        "/data/data/com.termux/files/usr/share/fonts/DejaVuSans.ttf",
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/Roboto-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

def ease_out_cubic(p):
    return 1 - (1 - p) ** 3

# ---------------- load usernames ----------------
txt_file = "usernames.txt" if os.path.exists("usernames.txt") else "username.txt"
with open(txt_file, "r", encoding="utf-8-sig") as f:
    usernames = [ln.strip() for ln in f if ln.strip()]

if not usernames:
    raise SystemExit("No usernames found!")

n = len(usernames)
angle_per = 360.0 / n
FONT_PATH = find_font()
WHEEL_CENTER = (WIDTH//2, HEIGHT//2 - 150)  # move wheel slightly up

# ---------------- build wheel ----------------
def build_wheel(names):
    cx, cy = WHEEL_CENTER
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,255))
    draw = ImageDraw.Draw(img)

    draw.ellipse([cx-RADIUS-6, cy-RADIUS-6, cx+RADIUS+6, cy+RADIUS+6], outline=(230,230,230), width=6)

    for i, name in enumerate(names):
        start = i * angle_per
        color = ((70 + (i*45)) % 256, (110 + (i*85)) % 256, (160 + (i*55)) % 256)
        draw.pieslice([cx-RADIUS, cy-RADIUS, cx+RADIUS, cy+RADIUS], start=start, end=start+angle_per, fill=color)

        ang_rad = math.radians(start - 90)
        x = cx + RADIUS * math.cos(ang_rad)
        y = cy + RADIUS * math.sin(ang_rad)
        draw.line([(cx, cy), (x, y)], fill=(240,240,240), width=3)

        slice_angle = angle_per
        max_font, min_font = 60, 12
        base_size = int(max_font * (slice_angle / 30))
        font_size = max(min_font, min(max_font, base_size))

        try:
            font = ImageFont.truetype(FONT_PATH, font_size) if FONT_PATH else ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        tw, th = draw.textsize(name, font=font)
        max_width = 2 * math.pi * RADIUS * (slice_angle / 360)
        while tw > max_width and font_size > min_font:
            font_size -= 2
            font = ImageFont.truetype(FONT_PATH, font_size)
            tw, th = draw.textsize(name, font=font)

        mid_angle = start + slice_angle / 2
        text_rad = math.radians(mid_angle - 90)
        text_r = RADIUS + 80
        tx, ty = cx + text_r * math.cos(text_rad), cy + text_r * math.sin(text_rad)
        txt_img = Image.new("RGBA", (tw+10, th+10), (0,0,0,0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text(((txt_img.width-tw)//2, (txt_img.height-th)//2), name, font=font, fill=(255,255,255))
        rotated_txt = txt_img.rotate(mid_angle, resample=Image.BICUBIC, expand=1)
        img.paste(rotated_txt, (int(tx - rotated_txt.width//2), int(ty - rotated_txt.height//2)), rotated_txt)

    return img

wheel_base = build_wheel(usernames)
wheel_base.save("wheel_preview_portrait.png")

# ---------------- arrow ----------------
def build_arrow():
    w, h = 320, 180
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(w//2, 10), (w//2 - 70, 120), (w//2 + 70, 120)], fill=(220,40,40,255))
    return img

arrow_img = build_arrow()

# ---------------- winner selection ----------------
winner = random.choice(usernames)
winner_index = usernames.index(winner)
slice_center = winner_index * angle_per + angle_per/2
offset_needed = 90 - slice_center
total_rotation = SPINS*360 + offset_needed
print(f"Winner: {winner} (index {winner_index}), stops at top")

# ---------------- wheel frames ----------------
spin_frames = int(round(SPIN_DURATION * FPS))
hold_frames = int(round(HOLD_DURATION * FPS))
frames = []

for i in range(spin_frames):
    p = i / (spin_frames-1) if spin_frames > 1 else 1.0
    eased = ease_out_cubic(p)
    angle = eased * total_rotation
    rotated = wheel_base.rotate(angle, resample=Image.BICUBIC, center=WHEEL_CENTER)
    frames.append(np.array(rotated.convert("RGB")))

final_frame = frames[-1].copy()
for _ in range(hold_frames):
    frames.append(final_frame)

spin_clip = ImageSequenceClip(frames, fps=FPS)
arrow_clip = ImageClip(np.array(arrow_img))\
    .set_duration(SPIN_DURATION+HOLD_DURATION)\
    .set_position(("center", 50))  # top arrow

spin_and_arrow = CompositeVideoClip([spin_clip, arrow_clip], size=(WIDTH, HEIGHT)).set_duration(SPIN_DURATION+HOLD_DURATION)

# ---------------- winner screen ----------------
def make_winner_image(text):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0,0,0))
    draw = ImageDraw.Draw(img)
    max_width = WIDTH * 0.8
    max_font_size = int(WIDTH * 0.12)
    min_font_size = 24
    font_size = max_font_size

    while font_size > min_font_size:
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
        tw, th = draw.textsize(text, font=font)
        if tw <= max_width:
            break
        font_size -= 6

    x, y = (WIDTH-tw)//2, HEIGHT//2 + 500  # place below wheel
    for dx, dy in [(-4,0),(4,0),(0,-4),(0,4)]:
        draw.text((x+dx, y+dy), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=(255,215,0))
    return img

winner_img = make_winner_image(f"{winner} WINS!")
winner_clip = ImageClip(np.array(winner_img))\
    .set_duration(WINNER_DURATION)\
    .set_start(SPIN_DURATION+HOLD_DURATION)

# ---------------- final video ----------------
final = CompositeVideoClip([spin_and_arrow, winner_clip], size=(WIDTH, HEIGHT))
print("Rendering vertical HD video — please wait...")
final.write_videofile(
    OUTPUT_NAME,
    fps=FPS,
    codec="libx264",
    audio=False,
    preset="slow",
    ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"]
)

print("Video saved in Termux folder:", os.path.abspath(OUTPUT_NAME))
print("Done! Winner:", winner)
