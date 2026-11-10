"""Regenerate launcher icons. This optional developer tool requires Pillow.

The app itself does not require Pillow or other third-party packages.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
image = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((48, 48, 976, 976), radius=220, fill='#183f32')
draw.rounded_rectangle((230, 170, 794, 854), radius=78, fill='#f2fbf5')
draw.rounded_rectangle((310, 740, 714, 757), radius=8, fill='#a6cdb5')
try:
    font = ImageFont.truetype('DejaVuSans-Bold.ttf', 420)
except OSError:
    font = ImageFont.load_default(size=420)
draw.text((512, 462), 'H', font=font, fill='#177052', anchor='mm')
image.save(ROOT / 'assets' / 'hernandez_invoice.ico', sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])
image.save(ROOT / 'assets' / 'hernandez_invoice.icns', format='ICNS')
