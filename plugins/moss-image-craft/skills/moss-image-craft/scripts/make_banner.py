"""OGP・サムネイル用のバナー（文字＋キャラ＋空の写真枠）の layout JSON を、定義 JSON から作る。

使い方:
  python3 make_banner.py examples/ogp_note.json -o prompt.json
  → mflux-generate-moss-image --prompt-file prompt.json --width 1280 --height 672 ...
  → python3 compose_banner.py raw.png out.png --spec examples/ogp_note.json --crop-to 1280x670

定義 JSON（examples/ogp_note.json を参照）:
  width, height   生成サイズ（16 の倍数）。OGP 1280x670 なら 1280x672 で作り、compose で切る
  summary         全体の説明（画風、配色、背景）
  texts[]         {"text", "caption", "bbox"}。caption に「正確な文字の並び」と「落としやすい字」を書くと文字抜けが減る
  objects[]       {"caption", "bbox"}。キャラなど
  frames[]        写真枠の bbox。生成後に compose_banner.py が実画像を貼る
bbox は [y_min, x_min, y_max, x_max]、キャンバス中心が原点（abs_centralized）。
"""
import argparse
import json
from pathlib import Path


def build(spec):
    items = [{"label": "text", **t} for t in spec.get("texts", [])]
    items += [{"label": "object", **o} for o in spec.get("objects", [])]
    for i, b in enumerate(spec.get("frames", [])):
        items.append({"label": "object", "bbox": b,
                      "caption": f"empty plain white rounded rectangle photo frame number {i + 1} with a thin dark border and soft drop shadow, nothing inside"})
    return {"summary": {"caption": spec["summary"]}, "items": items,
            "bbox_coord_space": "abs_centralized", "bbox_format": "yxyx"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    for k in ("width", "height"):
        assert spec[k] % 16 == 0, f"{k} は 16 の倍数にする（MOSS-Image の制約）"
    Path(a.output).write_text(json.dumps(build(spec), ensure_ascii=False))
    print("wrote", a.output)


if __name__ == "__main__":
    main()
