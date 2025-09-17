import random
import math
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, TextClip, CompositeVideoClip

# ===== Settings =====
WIDTH, HEIGHT = 720, 720
FPS = 30
DURATION = 5  # seconds for spin
FINAL_HOLD = 3  # seconds showing winner
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

    # Draw slices
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

# ===== Add arrow on top =====
def add_arrow(img):
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2
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

# Final angle so that winner is at the arrow (top = 90°)
final_angle = 90 - (winner_index * angle_per_slice + angle_per_slice / 2)

for i in range(total_frames):
    # Ease-out rotation: fast → slow → stop
    progress = i / total_frames
    rotation = (1 - (progress ** 2)) * 720 + final_angle  # 2 spins + stop
    rotated = wheel_img.rotate(rotation, resample=Image.BICUBIC)
    frames.append(rotated)

# ===== Build spin clip =====
clip = ImageSequenceClip([frame for frame in frames], fps=FPS)

# ===== Winner text =====
winner_text = TextClip(f"{winner} WINS!", fontsize=WINNER_FONT_SIZE,
                       color="yellow", size=(WIDTH, HEIGHT)).set_duration(FINAL_HOLD)

final_video = CompositeVideoClip([clip, winner_text.set_start(DURATION)])

# ===== Export =====
final_video.write_videofile("spin_fight_reel.mp4", fps=FPS)

print(f"Winner is: {winner}")
