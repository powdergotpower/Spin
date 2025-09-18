import random
import math
import numpy as np
from moviepy.editor import ImageSequenceClip, TextClip, CompositeVideoClip
from PIL import ImageFont
import os

# Load usernames
with open("username.txt", "r", encoding="utf-8-sig") as f:
    usernames = [line.strip() for line in f if line.strip()]

if not usernames:
    raise ValueError("No usernames found in username.txt")

# Font
font_path = "/system/fonts/Roboto-Regular.ttf"
font = ImageFont.truetype(font_path, 24)

# Wheel setup
n = len(usernames)
colors = plt.cm.tab20(np.linspace(0, 1, n))

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(aspect="equal"))
wedges, texts = ax.pie([1] * n, colors=colors, startangle=90, counterclock=False)

# Adjust font size dynamically
max_font_size = 14
min_font_size = 2
font_size = max(min_font_size, min(max_font_size, int(200 / math.sqrt(n))))

for i, p in enumerate(wedges):
    ang = (p.theta2 - p.theta1) / 2. + p.theta1
    y = math.sin(math.radians(ang))
    x = math.cos(math.radians(ang))
    ha = "left" if x > 0 else "right"
    ax.text(x * 0.8, y * 0.8, usernames[i],
            ha=ha, va="center", rotation=ang,
            fontsize=font_size, color="white")

# Draw arrow at top
ax.add_patch(plt.Polygon([[0, 1.05], [-0.05, 1.15], [0.05, 1.15]], color="red"))

# Pick winner
slice_angle = 360 / n
winner_index = random.randint(0, n - 1)

# Spin rotation
spins = 5
stop_angle = winner_index * slice_angle
final_angle = 360 * spins + stop_angle

# Corrected winner calc (arrow at top)
corrected_angle = (final_angle + 90) % 360
winner_index = int(corrected_angle / slice_angle) % n
winner = usernames[winner_index]

print(f"Winner: {winner} (index {winner_index}), stops at top")

# Generate frames
frames = []
steps = 60
angles = np.linspace(0, final_angle, steps)

for ang in angles:
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(aspect="equal"))
    wedges, texts = ax.pie([1] * n, colors=colors, startangle=90 - ang, counterclock=False)

    for i, p in enumerate(wedges):
        ang_text = (p.theta2 - p.theta1) / 2. + p.theta1
        y = math.sin(math.radians(ang_text))
        x = math.cos(math.radians(ang_text))
        ha = "left" if x > 0 else "right"
        ax.text(x * 0.8, y * 0.8, usernames[i],
                ha=ha, va="center", rotation=ang_text,
                fontsize=font_size, color="white")

    ax.add_patch(plt.Polygon([[0, 1.05], [-0.05, 1.15], [0.05, 1.15]], color="red"))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)

    fig.canvas.draw()
    image = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
    image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    frames.append(image)
    plt.close(fig)

print("Rendering video — please wait...")

clip = ImageSequenceClip(frames, fps=30)

# Winner text
txt_clip = TextClip(f"{winner} WINS!", fontsize=60, color='yellow', font="Roboto-Regular")
txt_clip = txt_clip.set_duration(3).set_position("center")

final_clip = CompositeVideoClip([clip, txt_clip.set_start(len(frames)/30)])
final_clip.write_videofile("spin_result.mp4", fps=30)

print("Video saved in Termux folder: " + os.path.abspath("spin_result.mp4"))
print("Done! Winner:", winner)
