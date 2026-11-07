"""Render assets/icon/*.svg with a local Chrome and write pler.ico plus PNG sizes.

Developer tool; the generated files are committed so packaging does not need Chrome.
Usage: python tools/build_icon.py --chrome PATH_TO_CHROME
16-24 px use the simplified pler-small.svg; 32 px and up use pler.svg.
ICO entries up to 64 px are 32-bit BMP (accepted by every resource compiler); 256 px is PNG.
"""
import argparse, io, struct, subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT/'assets/icon'
SIZES = (16, 20, 24, 32, 40, 48, 64, 256)


def render(chrome, svg, size, work):
    page = work/f'{size}.html'
    page.write_text('<!doctype html><html><body style="margin:0;overflow:hidden;background:transparent">'
                    f'<img src="{svg.as_uri()}" width="{size}" height="{size}" style="display:block"></body></html>', 'utf-8')
    shot = work/f'{size}.png'
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    '--default-background-color=00000000', f'--user-data-dir={work/"profile"}',
                    f'--window-size={max(size, 64)},{max(size, 64)}', f'--screenshot={shot}', page.as_uri()],
                   check=True, capture_output=True, timeout=60)
    return Image.open(shot).convert('RGBA').crop((0, 0, size, size))


def bmp_entry(image):
    size = image.width
    pixels = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            r, g, b, a = image.getpixel((x, y))
            pixels += bytes((b, g, r, a))
    mask_row = ((size + 31)//32)*4
    header = struct.pack('<IiiHHIIiiII', 40, size, size*2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    return header + bytes(pixels) + bytes(mask_row*size)


def write_ico(images, path):
    entries = []
    for image in images:
        if image.width >= 256:
            data = io.BytesIO(); image.save(data, 'PNG'); data = data.getvalue()
        else:
            data = bmp_entry(image)
        entries.append((image.width, data))
    offset = 6 + 16*len(entries)
    out = bytearray(struct.pack('<HHH', 0, 1, len(entries)))
    for size, data in entries:
        out += struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    for _, data in entries:
        out += data
    path.write_bytes(bytes(out))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chrome', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        images = [render(args.chrome, ICON/('pler-small.svg' if size <= 24 else 'pler.svg'), size, work) for size in SIZES]
        big = render(args.chrome, ICON/'pler.svg', 1024, work)
    write_ico(images, ICON/'pler.ico')
    for image in images:
        if image.width in (32, 256):
            image.save(ICON/f'pler-{image.width}.png')
    big.save(ICON/'pler-1024.png')
    print('wrote', ICON/'pler.ico', [image.width for image in images])


if __name__ == '__main__':
    main()
