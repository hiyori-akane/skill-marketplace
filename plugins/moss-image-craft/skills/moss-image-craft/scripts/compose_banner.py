"""make_banner.py で作った下地の「空の写真枠」に実画像を貼り、必要ならサイズを切りそろえる。

MOSS-Image は既存の画像を描き込めない。そこで枠だけ描かせ、後処理で貼る。
モデルが描いた枠の位置は少しずれるので、定義の bbox の位置に白い枠を描き直してから貼る。

使い方:
  python3 compose_banner.py raw.png out.png --spec examples/ogp_note.json \
      --image photo.png:128,40,896,472 --crop-to 1280x670
  --image は frames の順に指定する。「パス:left,top,right,bottom」で元画像の切り出し範囲を指定できる。
  --sticker "スキル/配布中！" で星形ステッカーを重ねる（--sticker-at x,y で位置）。
要るもの: Pillow
"""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BORDER, RADIUS = 6, 14
FONTS = ["/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc", "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"]


def font(size):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def fit(img, w, h):
    """縦横比を保って w x h を覆うように縮め、横は中央・縦は上寄せで切る。"""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    left = (img.width - w) // 2
    return img.crop((left, 0, left + w, h))


def paste_frame(base, bbox, pic):
    W, H = base.size
    y0, x0, y1, x1 = bbox
    L, T, R, B = x0 + W // 2, y0 + H // 2, x1 + W // 2, y1 + H // 2
    shadow = Image.new("L", base.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((L + 6, T + 8, R + 6, B + 8), RADIUS, fill=140)
    base.paste((0, 0, 0), mask=shadow.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(base).rounded_rectangle((L, T, R, B), RADIUS, fill="white", outline=(40, 40, 50), width=2)
    w, h = R - L - BORDER * 2, B - T - BORDER * 2
    pic = fit(pic, w, h)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), RADIUS - 4, fill=255)
    base.paste(pic, (L + BORDER, T + BORDER), mask)


def sticker(base, lines, cx, cy, r1=92, r2=74, n=14):
    def star(dx=0, dy=0):
        return [(cx + dx + (r1 if i % 2 == 0 else r2) * math.cos(math.pi * i / n - math.pi / 2),
                 cy + dy + (r1 if i % 2 == 0 else r2) * math.sin(math.pi * i / n - math.pi / 2)) for i in range(2 * n)]
    d = ImageDraw.Draw(base)
    d.polygon(star(5, 7), fill=(0, 0, 0))
    d.polygon(star(), fill=(230, 20, 60), outline="white", width=5)
    f = font(30)
    for i, t in enumerate(lines):
        d.text((cx, cy + (i - (len(lines) - 1) / 2) * 38), t, font=f, fill="white", anchor="mm",
               stroke_width=3, stroke_fill=(120, 0, 30))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--image", action="append", default=[])
    ap.add_argument("--crop-to", help="WxH。上下・左右を均等に切る（例 1280x670）")
    ap.add_argument("--sticker", help="改行を / で区切った文言（例 スキル/配布中！）")
    ap.add_argument("--sticker-at", default="585,548", help="ステッカーの中心（切りそろえた後のピクセル）")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    base = Image.open(a.src).convert("RGB")
    assert base.size == (spec["width"], spec["height"]), base.size
    for bbox, arg in zip(spec.get("frames", []), a.image):
        path, _, box = arg.partition(":")
        pic = Image.open(path).convert("RGB")
        if box:
            pic = pic.crop(tuple(int(v) for v in box.split(",")))
        paste_frame(base, bbox, pic)
    if a.crop_to:
        w, h = (int(v) for v in a.crop_to.lower().split("x"))
        dx, dy = (base.width - w) // 2, (base.height - h) // 2
        base = base.crop((dx, dy, dx + w, dy + h))
    if a.sticker:
        sticker(base, a.sticker.split("/"), *(int(v) for v in a.sticker_at.split(",")))
    base.save(a.dst)
    print("wrote", a.dst, base.size)


if __name__ == "__main__":
    main()
