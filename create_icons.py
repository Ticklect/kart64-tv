"""Export application artwork from the checked-in master; requires Pillow."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
ANDROID = ROOT / 'android/app/src/main/res/drawable-nodpi'


def generate():
    with Image.open(ASSETS / 'kart64-master.png') as master:
        image = master.convert('RGBA')
    if image.width != image.height:
        raise ValueError('The icon master must be square')

    icon = image.resize((512, 512), Image.Resampling.LANCZOS)
    icon.save(ASSETS / 'kart64.png', optimize=True)
    icon.save(ASSETS / 'kart64.ico', sizes=[
        (16, 16), (24, 24), (32, 32), (48, 48),
        (64, 64), (128, 128), (256, 256),
    ])
    for size in (80, 130, 256):
        image.resize((size, size), Image.Resampling.LANCZOS).save(
            ASSETS / f'kart64-{size}.png', optimize=True)

    ANDROID.mkdir(parents=True, exist_ok=True)
    icon.save(ANDROID / 'kart64.png', optimize=True)

    # TV launchers display a landscape tile: keep the name large and readable.
    banner = Image.new('RGB', (1280, 720), '#061a3b')
    banner.paste(image.resize((720, 720), Image.Resampling.LANCZOS), (0, 0))
    draw = ImageDraw.Draw(banner)
    try:
        title = ImageFont.truetype('arialbd.ttf', 126)
        number = ImageFont.truetype('arialbd.ttf', 168)
    except OSError:
        title = ImageFont.load_default(size=126)
        number = ImageFont.load_default(size=168)
    draw.text((762, 205), 'KART', font=title, fill='#fff0c6')
    draw.text((758, 332), '64 TV', font=number, fill='#ffd137')
    draw.rectangle((768, 554, 1190, 565), fill='#e53927')
    banner.resize((320, 180), Image.Resampling.LANCZOS).save(
        ANDROID / 'banner.png', optimize=True)


if __name__ == '__main__':
    generate()
