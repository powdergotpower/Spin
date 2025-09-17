import random
import numpy as np
import matplotlib.pyplot as plt
from moviepy.editor import *
from moviepy.video.tools.drawing import color_gradient

# ===== CONFIG =====
USERNAMES = ["user1", "user2", "user3", "user4", "user5"]
DURATION = 6  # total spin duration
FPS = 30
WHEEL_SIZE = 600
WINNER_FONT_SIZE = 90
ARROW_COLOR = 'red'

# ===== PICK WINNER =====
winner = random.choice(USERNAMES)
winner_index = USERNAMES.index(winner)
print(f"Winner is: {winner}")

# ===== DRAW WHEEL =====
def make_wheel(usernames):
    fig, ax = plt.subplots(figsize=(6,6), facecolor="black")
    wedges, _ = ax.pie([1]*len(usernames), startangle=90, colors=plt.cm.Set3.colors)

    for i, w in enumerate(wedges):
        ang = (w.theta2 + w.theta1)/2
        x = np.cos(np.deg2rad(ang))*0.6
        y = np.sin(np.deg2rad(ang))*0.6
        ax.text(x, y, usernames[i], ha="center", va="center", color="black", fontsize=12, weight="bold")

    ax.set(aspect="equal")
    plt.axis("off")

    plt.savefig("wheel.png", dpi=200, bbox_inches="tight", facecolor="black")
    plt.close(fig)
    return "wheel.png"

wheel_img = make_wheel(USERNAMES)

# ===== MOVIEPY CLIPS =====
wheel_clip = ImageClip(wheel_img).set_duration(DURATION)

# Arrow (static on top)
arrow = ColorClip(size=(40,100), color=(255,0,0)).set_duration(DURATION)
arrow = arrow.set_position(("center", 20))

# Rotation easing function
def ease_out(t):
    return 1 - (1 - t)**3  # cubic ease-out

slices = len(USERNAMES)
angle_per_slice = 360 / slices
stop_angle = winner_index * angle_per_slice + angle_per_slice/2

def rotate(get_frame, t):
    # progress goes 0→1
    progress = ease_out(t / DURATION)
    # spin many turns, then land on winner
    total_rotation = 5*360 + stop_angle
    angle = progress * total_rotation
    return get_frame(t).rotate(angle, resample="bilinear")

rotating_wheel = wheel_clip.fl(rotate, apply_to=['mask'])

# Winner text (appears at end)
winner_text = TextClip(f"🎉 {winner} WINS! 🎉",
                       fontsize=WINNER_FONT_SIZE,
                       color="yellow",
                       stroke_color="black",
                       stroke_width=3,
                       font="DejaVu-Sans-Bold")
winner_text = winner_text.set_duration(3).set_position("center").set_start(DURATION)

# Final video
final = CompositeVideoClip([rotating_wheel, arrow, winner_text],
                           size=(WHEEL_SIZE, WHEEL_SIZE),
                           bg_color="black")

final.write_videofile("spin_fight_reel.mp4", fps=FPS, codec="libx264", audio=False)
