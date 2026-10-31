"""画像を横に並べ、上にラベルを付けた比較画像を作る（方法別・LoRA 別・言語別の比較用）。

使い方:
  python3 compare.py out.jpg a.png:ComfyUI b.png:"felix turbo" c.png:"mflux main"
要るもの: Pillow
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTS = ["/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]


def main(out, *pairs):
    items = [p.rsplit(":", 1) if ":" in p else (p, Path(p).stem) for p in pairs]
    ims = [Image.open(p).convert("RGB") for p, _ in items]
    g, top = 24, 56
    c = Image.new("RGB", (sum(i.width for i in ims) + g * (len(ims) - 1), max(i.height for i in ims) + top), "white")
    d = ImageDraw.Draw(c)
    fp = next((f for f in FONTS if Path(f).exists()), None)
    f = ImageFont.truetype(fp, 30) if fp else ImageFont.load_default()
    x = 0
    for im, (_, label) in zip(ims, items):
        c.paste(im, (x, top))
        d.text((x + 10, 12), label, fill="black", font=f)
        x += im.width + g
    c.save(out, quality=85)
    print("wrote", out, c.size)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
