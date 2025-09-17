from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import math, random, os

# --- CONFIG ---
WIDTH, HEIGHT = 720, 720
WHEEL_RADIUS = 300
FONT_PATH = "/data/data/com.termux/files/usr/share/fonts/DejaVuSans.ttf"
WINNER_FONT_SIZE = 90
FPS = 30

# Load usernames
with open("usernames.txt", "r") as f:
    usernames = [u.strip() for u in f.readlines() if u.strip()]

n = len(usernames)
angle_per_user = 360 / n

# --- Draw Wheel ---
def make_wheel(usernames):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,255))
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH//2, HEIGHT//2
    font = ImageFont.truetype(FONT_PATH, 26)

    for i, user in enumerate(usernames):
        start_angle = i * angle_per_user
        end_angle = start_angle + angle_per_user
        draw.pieslice([cx-WHEEL_RADIUS, cy-WHEEL_RADIUS, cx+WHEEL_RADIUS, cy+WHEEL_RADIUS],
                      start=start_angle, end=end_angle,
                      fill=(50+ i*20 % 200, 100+ i*40 % 155, 150, 255),
                      outline="white")

        # Position text on edge
        text_angle = math.radians(start_angle + angle_per_user/2)
        tx = cx + math.cos(text_angle) * (WHEEL_RADIUS - 50)
        ty = cy + math.sin(text_angle) * (WHEEL_RADIUS - 50)
        draw.text((tx-20, ty-10), user, font=font, fill="white")

    return img

wheel_img = make_wheel(usernames)
wheel_img_path = "wheel.png"
wheel_img.save(wheel_img_path)

# --- MoviePy Animation ---
wheel_clip = ImageClip(wheel_img_path).set_duration(6).set_position("center")

# Rotation easing (fast → slow → stop)
winner = random.choice(usernames)
winner_index = usernames.index(winner)
stop_angle = -(winner_index * angle_per_user + angle_per_user/2)

def rotation(t):
    total_spin = 1440  # 4 full spins
    progress = t / 6
    eased = 1 - (1-progress)**3  # cubic ease out
    return total_spin * (1-eased) + stop_angle*eased

rotated = wheel_clip.fl_time(lambda t: t).rotate(lambda t: rotation(t), resample="bilinear")

# Arrow on top
arrow = (ImageClip(wheel_img_path)
         .set_make_frame(lambda t: Image.new("RGBA",(WIDTH,HEIGHT),(0,0,0,0)).tobytes())
         .set_duration(6))
arrow_draw = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,0))
d = ImageDraw.Draw(arrow_draw)
cx, cy = WIDTH//2, HEIGHT//2
d.polygon([(cx, cy-WHEEL_RADIUS-40), (cx-20, cy-WHEEL_RADIUS), (cx+20, cy-WHEEL_RADIUS)], fill="red")
arrow_path = "arrow.png"
arrow_draw.save(arrow_path)
arrow_clip = ImageClip(arrow_path).set_duration(6)

# Winner text after spin
winner_text = (TextClip(f"{winner} WINS!", fontsize=WINNER_FONT_SIZE, color="yellow", font="DejaVu-Sans")
               .set_duration(3)
               .set_start(6)
               .set_position("center"))

# Final video
final = CompositeVideoClip([rotated, arrow_clip, winner_text], size=(WIDTH,HEIGHT))
final.write_videofile("spin_fight_reel.mp4", fps=FPS)

print("Winner is:", winner)
