#!/usr/bin/env python3
# spin_fight.py — Clean Termux-friendly spin-wheel reel generator
# Requires: pillow, moviepy, numpy
# Installs: pip install pillow moviepy numpy

import os
import math
import random
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, ImageClip, CompositeVideoClip, vfx

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1080, 1080            # output resolution (square, Instagram-friendly)
RADIUS = 420                          # wheel radius
FPS = 30
SPIN_DURATION = 4.0                   # seconds of spin (fast->slow)
HOLD_DURATION = 2.0                   # seconds to pause on stopped wheel (clear winner)
WINNER_DURATION = 2.0                 # seconds big winner screen
SPINS = 6                             # how many full rotations before stopping
OUTPUT_NAME = "spin_fight_reel.mp4"
AUTO_MOVE_TO_DOWNLOADS = True         # move result to ~/storage/downloads/ and broadcast
# ---------------------------------------

# ----------------- helpers -----------------
def find_font():
    # common font candidates on Termux/Android/Linux
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
    # cubic ease-out: fast -> slow
    return 1 - (1 - p) ** 3

# -------------- load usernames --------------
with open("usernames.txt", "r") as f:
    usernames = [ln.strip() for ln in f if ln.strip()]

if not usernames:
    raise SystemExit("usernames.txt is empty — add one username per line and re-run.")

n = len(usernames)
angle_per = 360.0 / n

# ---------------- choose font ----------------
FONT_PATH = find_font()
if FONT_PATH:
    print("Using font:", FONT_PATH)
else:
    print("Warning: no TTF font found in common locations. Falling back to default font (may be small).")
# For drawing wheel labels we'll try to load a moderate font size; fallback to load_default if fails later.

# ---------------- draw base wheel (no arrow) ----------------
def build_wheel_image():
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2

    # draw circle border for clarity
    draw.ellipse([cx - RADIUS - 4, cy - RADIUS - 4, cx + RADIUS + 4, cy + RADIUS + 4], outline=(220,220,220), width=4)

    # draw colored slices and separator lines
    for i, name in enumerate(usernames):
        start = i * angle_per
        end = start + angle_per
        # pick visually pleasant color per slice
        color = (
            (80 + (i * 37)) % 256,
            (120 + (i * 73)) % 256,
            (160 + (i * 53)) % 256
        )
        draw.pieslice([cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS], start=start, end=end, fill=color, outline=None)

        # separator line at slice start
        ang_rad = math.radians(start - 90)  # PIL pieslice 0deg = 3 o'clock; subtract 90 to rotate start at 12 o'clock
        x = cx + RADIUS * math.cos(ang_rad)
        y = cy + RADIUS * math.sin(ang_rad)
        draw.line([ (cx, cy), (x, y) ], fill=(230,230,230), width=6)

        # place username OUTSIDE wheel near slice top (offset outside circle)
        mid_angle = start + angle_per / 2
        mid_rad = math.radians(mid_angle - 90)
        text_radius = RADIUS + 60
        tx = cx + text_radius * math.cos(math.radians(mid_angle - 90))
        ty = cy + text_radius * math.sin(math.radians(mid_angle - 90))

        # use true type font if available (preferred)
        try:
            if FONT_PATH:
                font = ImageFont.truetype(FONT_PATH, 36)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # center the text
        tw, th = draw.textsize(name, font=font)
        draw.text((tx - tw/2, ty - th/2), name, font=font, fill=(255,255,255))

    return img

wheel_base = build_wheel_image()
# Save preview optionally
wheel_base.save("wheel_base.png")

# ---------------- static arrow image (separate) ----------------
def build_arrow_image():
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = WIDTH // 2
    tip_y = 30
    base_y = tip_y + 80
    # triangle pointing down
    draw.polygon([(cx, tip_y), (cx-40, base_y), (cx+40, base_y)], fill=(220,40,40,255))
    # small circle or marker under tip for clarity
    draw.ellipse([cx-10, base_y-10, cx+10, base_y+10], fill=(255,255,255,255))
    return img

arrow_img = build_arrow_image()
# arrow_img.save("arrow.png")  # optional

# ---------------- compute rotation target ----------------
# we want the slice center of the chosen winner to land at top (90 degrees)
winner = random.choice(usernames)
winner_index = usernames.index(winner)
slice_center = winner_index * angle_per + angle_per / 2  # degrees (0 deg = slice start at 3 o'clock)
# To place slice_center at top (90deg), wheel must be rotated by:
offset_needed = 90 - slice_center
final_total_degrees = SPINS * 360 + offset_needed
print("Winner:", winner, "| final target offset:", offset_needed)

# ---------------- generate spin frames ----------------
spin_frames = int(round(SPIN_DURATION * FPS))
hold_frames = int(round(HOLD_DURATION * FPS))

frames = []
for i in range(spin_frames):
    p = i / (spin_frames - 1) if spin_frames > 1 else 1.0
    eased = ease_out_cubic(p)
    angle = eased * final_total_degrees
    # PIL rotate rotates counter-clockwise by default; using positive angle is fine
    rotated = wheel_base.rotate(angle, resample=Image.BICUBIC, center=(WIDTH//2, HEIGHT//2), expand=False)
    # paste arrow on top as separate overlay later — here we keep only wheel (so arrow stays static overlay)
    frames.append(np.array(rotated.convert("RGB")))

# hold last frame for a clear pause (wheel stopped)
last_frame = frames[-1].copy()
for _ in range(hold_frames):
    frames.append(last_frame)

# build spin clip
spin_clip = ImageSequenceClip(frames, fps=FPS)

# create static arrow clip that lasts for spin + hold (not during winner reveal)
arrow_clip = ImageClip(np.array(arrow_img)).set_duration(SPIN_DURATION + HOLD_DURATION)

# ---------------- prepare winner reveal image (Pillow) ----------------
def build_winner_image(text):
    # big bold centered text; prefer TTF if available
    img = Image.new("RGB", (WIDTH, HEIGHT), "black")
    draw = ImageDraw.Draw(img)
    try:
        if FONT_PATH:
            # choose a large size based on canvas
            fsize = int(WIDTH * 0.10)  # 10% of width
            font = ImageFont.truetype(FONT_PATH, fsize)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # draw with a simple stroke effect: draw text multiple times offset for outline
    txt = text
    tw, th = draw.textsize(txt, font=font)
    x = (WIDTH - tw) // 2
    y = (HEIGHT - th) // 2

    # outline
    outline_color = (0,0,0)
    for dx,dy in [(-3,-3),(-3,3),(3,-3),(3,3),(-3,0),(3,0),(0,-3),(0,3)]:
        draw.text((x+dx, y+dy), txt, font=font, fill=outline_color)
    # main text
    draw.text((x, y), txt, font=font, fill=(255, 215, 0))  # gold-ish

    return img

winner_img = build_winner_image(f"{winner} WINS!")
winner_clip = ImageClip(np.array(winner_img)).set_duration(WINNER_DURATION).set_start(SPIN_DURATION + HOLD_DURATION)

# optional fade: fade out wheel right before winner reveal
spin_clip = spin_clip.set_duration(SPIN_DURATION + HOLD_DURATION).fx(vfx.fadeout, 0.6)

# ---------------- build final composite ----------------
final = CompositeVideoClip([spin_clip, arrow_clip, winner_clip], size=(WIDTH, HEIGHT))

# ---------------- export ----------------
print("Rendering video — this can take a bit. Output:", OUTPUT_NAME)
final.write_videofile(OUTPUT_NAME, fps=FPS, codec="libx264", audio=False)

# ---------------- move & broadcast (Termux) ----------------
if AUTO_MOVE_TO_DOWNLOADS:
    # Termux provides ~/storage/downloads (symlink) when termux-setup-storage used
    dest_dir = os.path.expanduser("~/storage/downloads")
    if not os.path.isdir(dest_dir):
        # try /sdcard/Download as fallback
        dest_dir = "/sdcard/Download"
    dest_path = os.path.join(dest_dir, OUTPUT_NAME)
    try:
        shutil.move(OUTPUT_NAME, dest_path)
        print("Moved video to:", dest_path)
        # broadcast to media scanner
        cmd = f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{dest_path}"
        subprocess.call(cmd, shell=True)
        print("Broadcasted media-scan for:", dest_path)
    except Exception as e:
        print("Could not move/broadcast automatically:", e)
        print("Video remains at:", os.path.abspath(OUTPUT_NAME))

print("Done. Winner:", winner)
