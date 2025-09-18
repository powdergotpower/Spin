#!/usr/bin/env python3
# spin_fight.py — Termux-friendly spin-wheel generator
# Requires: pillow, moviepy, numpy
# Install if needed: pip install pillow moviepy numpy

import os, math, random, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, ImageClip, CompositeVideoClip, vfx

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1080, 1080            # square video
RADIUS = 420                          # wheel radius
FPS = 30
SPIN_DURATION = 6.0                   # seconds wheel spins
HOLD_DURATION = 2.0                   # pause on stopped wheel
WINNER_DURATION = 4.0                 # big winner screen
SPINS = 6                             # full rotations before stop
OUTPUT_NAME = "spin_result.mp4"
AUTO_MOVE = False                     # keep file in Termux (Spin folder)
# ---------------------------------------

# ---------------- helpers ----------------
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

def ease_out_cubic(p): return 1 - (1 - p) ** 3

def generate_colors(n):
    colors = []
    for i in range(n):
        r = (70 + i * 37) % 256
        g = (110 + i * 59) % 256
        b = (160 + i * 83) % 256
        colors.append((r, g, b))
    return colors

# ---------------- load usernames ----------------
filename = "usernames.txt"
if not os.path.isfile(filename):
    raise SystemExit("Missing usernames.txt — add usernames, one per line.")

with open(filename, "r", encoding="utf-8-sig") as f:
    usernames = [ln.strip() for ln in f if ln.strip()]

if not usernames:
    raise SystemExit("usernames.txt is empty.")

n = len(usernames)
angle_per = 360.0 / n
colors = generate_colors(n)

FONT_PATH = find_font()
if FONT_PATH: print("Using font:", FONT_PATH)

# ---------------- build wheel image ----------------
def build_wheel(names):
    cx, cy = WIDTH//2, HEIGHT//2
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,255))
    draw = ImageDraw.Draw(img)

    draw.ellipse([cx-RADIUS-6, cy-RADIUS-6, cx+RADIUS+6, cy+RADIUS+6],
                 outline=(230,230,230), width=6)

    for i, name in enumerate(names):
        start = i * angle_per
        end = start + angle_per
        draw.pieslice([cx-RADIUS, cy-RADIUS, cx+RADIUS, cy+RADIUS],
                      start=start, end=end, fill=colors[i])

        ang_rad = math.radians(start - 90)
        x = cx + RADIUS * math.cos(ang_rad)
        y = cy + RADIUS * math.sin(ang_rad)
        draw.line([(cx, cy), (x, y)], fill=(240,240,240), width=4)

        mid_angle = start + angle_per/2
        rad = math.radians(mid_angle - 90)
        text_r = RADIUS + 70
        tx, ty = cx + text_r * math.cos(rad), cy + text_r * math.sin(rad)

        try: font = ImageFont.truetype(FONT_PATH, max(12, int(2000/n)))
        except: font = ImageFont.load_default()

        tw, th = draw.textsize(name, font=font)
        draw.text((tx - tw/2, ty - th/2), name, font=font, fill=(255,255,255))
    return img

wheel_base = build_wheel(usernames)

# ---------------- build arrow ----------------
def build_arrow():
    w, h = 240, 140
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(w//2, 10), (w//2 - 50, 100), (w//2 + 50, 100)],
                 fill=(220,40,40,255))
    draw.ellipse([(w//2-12, 92), (w//2+12, 116)],
                 fill=(255,255,255,255))
    return img

arrow_img = build_arrow()

# ---------------- select winner ----------------
winner = random.choice(usernames)
winner_index = usernames.index(winner)
slice_center = winner_index * angle_per + angle_per/2
offset_needed = 90 - slice_center
total_rotation = SPINS * 360 + offset_needed
print(f"Winner: {winner} (index {winner_index}), stops at top")

# ---------------- generate wheel frames ----------------
spin_frames = int(round(SPIN_DURATION * FPS))
hold_frames = int(round(HOLD_DURATION * FPS))
frames = []

for i in range(spin_frames):
    p = i / (spin_frames - 1) if spin_frames > 1 else 1.0
    eased = ease_out_cubic(p)
    angle = eased * total_rotation
    rotated = wheel_base.rotate(angle, resample=Image.BICUBIC,
                                center=(WIDTH//2, HEIGHT//2), expand=False)
    frames.append(np.array(rotated.convert("RGB")))

final_frame = frames[-1].copy()
for _ in range(hold_frames):
    frames.append(final_frame)

spin_clip = ImageSequenceClip(frames, fps=FPS)
arrow_clip = ImageClip(np.array(arrow_img)).set_duration(SPIN_DURATION + HOLD_DURATION).set_position(("center", 20))
spin_and_arrow = CompositeVideoClip([spin_clip, arrow_clip], size=(WIDTH, HEIGHT)).set_duration(SPIN_DURATION + HOLD_DURATION)
spin_and_arrow = spin_and_arrow.fx(vfx.fadeout, 0.6)

# ---------------- winner reveal ----------------
def make_winner_image(text):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype(FONT_PATH, int(WIDTH*0.12))
    except: font = ImageFont.load_default()

    tw, th = draw.textsize(text, font=font)
    x, y = (WIDTH - tw)//2, (HEIGHT - th)//2
    for dx, dy in [(-4,-4),(-4,4),(4,-4),(4,4),(0,-4),(0,4),(4,0),(-4,0)]:
        draw.text((x+dx, y+dy), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=(255,215,0))
    return img

winner_img = make_winner_image(f"{winner} WINS!")
winner_clip = ImageClip(np.array(winner_img)).set_duration(WINNER_DURATION).set_start(SPIN_DURATION + HOLD_DURATION)

# ---------------- final video ----------------
final = CompositeVideoClip([spin_and_arrow, winner_clip], size=(WIDTH, HEIGHT))
print("Rendering video — please wait...")
final.write_videofile(OUTPUT_NAME, fps=FPS, codec="libx264", audio=False, preset="medium")

# ---------------- done ----------------
print("Video saved in Termux folder:", os.path.abspath(OUTPUT_NAME))
print("Done! Winner:", winner)
