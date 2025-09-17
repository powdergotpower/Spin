#!/usr/bin/env python3
# spin_fight.py  — fixed, clean, Termux-friendly spin wheel generator
# Requirements: pillow, moviepy, numpy
# Install (if needed): pip install pillow moviepy numpy

import os, math, random, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, ImageClip, CompositeVideoClip, vfx

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1080, 1080      # output resolution
RADIUS = 420                    # wheel radius
FPS = 30
SPIN_DURATION = 6.0             # seconds wheel spins (fast -> slow -> stop)
HOLD_DURATION = 2.0             # seconds to show stopped wheel clearly
WINNER_DURATION = 4.0           # seconds for big winner screen
SPINS = 4                       # full rotations before stopping
OUTPUT_NAME = "spin_result.mp4"
AUTO_MOVE_TO_DOWNLOADS = True
# ---------------------------------------

# ------------ utility helpers ------------
def find_font():
    candidates = [
        "/data/data/com.termux/files/usr/share/fonts/DejaVuSans.ttf",
        "/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
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

# ------------- load usernames -------------
with open("usernames.txt", "r") as f:
    usernames = [ln.strip() for ln in f if ln.strip()]

if not usernames:
    raise SystemExit("usernames.txt is empty — add one username per line and re-run.")

n = len(usernames)
angle_per = 360.0 / n

FONT_PATH = find_font()
if FONT_PATH:
    print("Using font:", FONT_PATH)
else:
    print("No TTF font found — using Pillow default (winner text may be less crisp).")

# ------------- build wheel (no arrow) -------------
def build_wheel(names):
    cx, cy = WIDTH//2, HEIGHT//2
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,255))
    draw = ImageDraw.Draw(img)

    # outer circle outline
    draw.ellipse([cx-RADIUS-6, cy-RADIUS-6, cx+RADIUS+6, cy+RADIUS+6], outline=(230,230,230), width=6)

    for i, name in enumerate(names):
        start = i * angle_per
        end = start + angle_per
        color = (
            (70 + (i * 45)) % 256,
            (110 + (i * 85)) % 256,
            (160 + (i * 55)) % 256
        )
        draw.pieslice([cx-RADIUS, cy-RADIUS, cx+RADIUS, cy+RADIUS], start=start, end=end, fill=color)

        # separator line
        ang_rad = math.radians(start - 90)
        x = cx + RADIUS * math.cos(ang_rad)
        y = cy + RADIUS * math.sin(ang_rad)
        draw.line([(cx, cy), (x, y)], fill=(240,240,240), width=6)

        # username outside the wheel near the slice top
        mid_angle = start + angle_per/2
        rad = math.radians(mid_angle - 90)
        text_r = RADIUS + 70
        tx = cx + text_r * math.cos(rad)
        ty = cy + text_r * math.sin(rad)

        try:
            font = ImageFont.truetype(FONT_PATH, 36) if FONT_PATH else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        tw, th = draw.textsize(name, font=font)
        draw.text((tx - tw/2, ty - th/2), name, font=font, fill=(255,255,255))

    return img

wheel_base = build_wheel(usernames)
wheel_base.save("wheel_preview.png")  # debug preview saved

# ------------- build small arrow (separate, static) -------------
def build_arrow_small():
    w, h = 240, 140
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Triangle pointing down (at bottom part of arrow image)
    draw.polygon([(w//2, 10), (w//2 - 50, 100), (w//2 + 50, 100)], fill=(220,40,40,255))
    # small circle marker
    draw.ellipse([(w//2 - 12, 92), (w//2 + 12, 116)], fill=(255,255,255,255))
    return img

arrow_small = build_arrow_small()
# arrow_small.save("arrow_small.png")

# ------------- compute rotation goal (winner) -------------
winner = random.choice(usernames)
winner_index = usernames.index(winner)
slice_center = winner_index * angle_per + angle_per/2
offset_needed = 90 - slice_center          # rotate wheel so the slice_center lands at 90deg (top)
total_rotation = SPINS * 360 + offset_needed
print(f"Winner: {winner} (index {winner_index}), offset_needed={offset_needed:.2f}°, total_rotation={total_rotation:.2f}°")

# ------------- generate frames (wheel rotates only) -------------
spin_frames = int(round(SPIN_DURATION * FPS))
hold_frames = int(round(HOLD_DURATION * FPS))
frames = []

for i in range(spin_frames):
    p = i / (spin_frames - 1) if spin_frames > 1 else 1.0
    eased = ease_out_cubic(p)
    angle = eased * total_rotation
    rotated = wheel_base.rotate(angle, resample=Image.BICUBIC, center=(WIDTH//2, HEIGHT//2), expand=False)
    frames.append(np.array(rotated.convert("RGB")))

# hold the final stopped frame for clarity
final_frame = frames[-1].copy()
for _ in range(hold_frames):
    frames.append(final_frame)

# ------------- make spin clip and static arrow overlay -------------
spin_clip = ImageSequenceClip(frames, fps=FPS)

# arrow clip: small image positioned at top-center (so it's static)
arrow_clip = ImageClip(np.array(arrow_small)).set_duration((SPIN_DURATION + HOLD_DURATION)).set_position(("center", 20))

# fade wheel (and arrow) slightly before winner reveal for nice transition
spin_and_arrow = CompositeVideoClip([spin_clip, arrow_clip], size=(WIDTH, HEIGHT)).set_duration(SPIN_DURATION + HOLD_DURATION)
spin_and_arrow = spin_and_arrow.fx(vfx.fadeout, 0.6)

# ------------- winner big text (Pillow -> ImageClip) -------------
def make_winner_image(text):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0,0,0))
    draw = ImageDraw.Draw(img)

    if FONT_PATH:
        # choose large size (13% of width) for a very big title
        try:
            fsize = int(WIDTH * 0.13)
            font = ImageFont.truetype(FONT_PATH, fsize)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # draw outline for readability
    tw, th = draw.textsize(text, font=font)
    x = (WIDTH - tw)//2
    y = (HEIGHT - th)//2

    # outline (8-direction)
    outline = (0,0,0)
    for dx, dy in [(-4,-4),(-4,4),(4,-4),(4,4),(-4,0),(4,0),(0,-4),(0,4)]:
        draw.text((x+dx, y+dy), text, font=font, fill=outline)
    # main text (gold)
    draw.text((x, y), text, font=font, fill=(255,215,0))

    return img

winner_img = make_winner_image(f"{winner} WINS!")
winner_clip = ImageClip(np.array(winner_img)).set_duration(WINNER_DURATION).set_start(SPIN_DURATION + HOLD_DURATION)

# ------------- compose final video and export -------------
final = CompositeVideoClip([spin_and_arrow, winner_clip], size=(WIDTH, HEIGHT))

print("Rendering video — this may take a while on mobile.")
final.write_videofile(OUTPUT_NAME, fps=FPS, codec="libx264", audio=False, preset="medium")

# ------------- move to downloads and broadcast (Termux) -------------
if AUTO_MOVE_TO_DOWNLOADS:
    dest_dir = os.path.expanduser("~/storage/downloads")
    if not os.path.isdir(dest_dir):
        dest_dir = "/sdcard/Download"
    dest_path = os.path.join(dest_dir, OUTPUT_NAME)
    try:
        shutil.move(OUTPUT_NAME, dest_path)
        print("Moved video to:", dest_path)
        subprocess.call(f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{dest_path}", shell=True)
        print("Broadcasted media-scan for:", dest_path)
    except Exception as e:
        print("Could not move/broadcast automatically:", e)
        print("Video is at:", os.path.abspath(OUTPUT_NAME))

print("Done. Winner:", winner)
