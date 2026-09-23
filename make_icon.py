from PIL import Image, ImageDraw, ImageFont

size = 512
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

cx, cy = size // 2, size // 2
r = size // 2 - 10

for y in range(size):
    for x in range(size):
        dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
        if dist <= r:
            t = dist / r
            red = int(56 + (30 - 56) * t)
            green = int(220 + (180 - 220) * t)
            blue = int(125 + (80 - 125) * t)
            img.putpixel((x, y), (red, green, blue, 255))

emoji_font = None
for path in [
    'C:/Windows/Fonts/seguiemj.ttf',
    'C:/Windows/Fonts/NotoColorEmoji.ttf',
    'C:/Windows/Fonts/AppleColorEmoji.ttf',
]:
    try:
        emoji_font = ImageFont.truetype(path, 200)
        print(f'Using emoji font: {path}')
        break
    except:
        continue

if emoji_font:
    try:
        bbox = draw.textbbox((0, 0), '\U0001f4b0', font=emoji_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size - tw) // 2
        ty = (size - th) // 2
        draw.text((tx, ty), '\U0001f4b0', font=emoji_font, embedded_color=True)
    except Exception as e:
        print(f'Emoji render failed: {e}, using fallback')
        emoji_font = None

if not emoji_font:
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 260)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), 'd', font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - 20
    draw.text((tx, ty), 'd', fill=(255, 255, 255, 255), font=font)

img.save('icon.png', 'PNG')
import os
print('icon.png:', os.path.getsize('icon.png'), 'bytes')
