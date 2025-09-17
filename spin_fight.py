import random
from moviepy.editor import *
from moviepy.video.tools.drawing import color_gradient
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

# ----- CONFIG -----
WHEEL_SIZE = 800  # pixels
SPIN_DURATION = 5  # seconds
FPS = 30
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Termux font path

# Load usernames
with open("usernames.txt", "r") as f:
    usernames = [line.strip() for line in f.readlines() if line.strip()]

num_users = len(usernames)

# Create wheel image
def create_wheel(usernames):
    wheel = Image.new("RGBA", (WHEEL_SIZE, WHEEL_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(wheel)
    angle_per_slice = 360 / len(usernames)
    
    for i, name in enumerate(usernames):
        start_angle = i * angle_per_slice
        end_angle = start_angle + angle_per_slice
        
        # Alternate slice colors
        color = (255, 200, 0) if i % 2 == 0 else (255, 150, 0)
        draw.pieslice([0,0,WHEEL_SIZE,WHEEL_SIZE], start=start_angle, end=end_angle, fill=color)
        
        # Draw username
        mid_angle = (start_angle + end_angle) / 2
        text_x = WHEEL_SIZE/2 + 0.35*WHEEL_SIZE*np.cos(np.radians(mid_angle))
        text_y = WHEEL_SIZE/2 + 0.35*WHEEL_SIZE*np.sin(np.radians(mid_angle))
        
        font = ImageFont.truetype(FONT_PATH, 28)
        text_w, text_h = draw.textsize(name, font=font)
        draw.text((text_x-text_w/2, text_y-text_h/2), name, fill="black", font=font)
        
    return wheel

wheel_img = create_wheel(usernames)
wheel_img.save("wheel.png")

# Convert PIL image to MoviePy clip
wheel_clip = ImageClip(np.array(wheel_img)).set_duration(SPIN_DURATION).resize(width=500)

# Animation: Spin with easing out
def spin(get_frame, t):
    progress = t / SPIN_DURATION
    angle = 720*progress*(1-progress) + random.randint(0,360)  # spins + random offset
    frame = wheel_clip.get_frame(0)
    pil_frame = Image.fromarray(frame).rotate(angle, resample=Image.BICUBIC, expand=False)
    return np.array(pil_frame)

spinning = wheel_clip.fl(spin, apply_to=['mask'])

# Pick random winner
winner = random.choice(usernames)
print("Winner is:", winner)

# Create winner text clip
txt_clip = TextClip(f"{winner} WINS!", fontsize=70, color='yellow', font='DejaVu-Sans-Bold')\
           .set_duration(3).set_position('center')

# Combine spin + winner reveal
final = concatenate_videoclips([spinning, txt_clip])

# Export
final.write_videofile("spin_fight_reel.mp4", fps=FPS)
