"""縦N コマ漫画（4コマなど）の scene JSON を、ストーリー定義の JSON から作る。

公式の8コマ作例（OpenMOSS/MOSS-Image の assets/images/003）と同じ scene JSON 形式で出力する。
座標は abs_centralized（キャンバス中心が原点）、bbox は [y_min, x_min, y_max, x_max]。

使い方:
  python3 make_comic.py examples/4koma_cake_ja.json -o prompt.json
  python3 make_comic.py examples/4koma_cake_ja.json --format layout -o prompt.json   # summary/items 形式
  python3 make_comic.py examples/4koma_cake_ja.json --no-dialog -o prompt.json       # セリフ空欄（非推奨）

ストーリー定義（examples/*.json を参照）:
  width, height        キャンバス（16 の倍数。4コマは 640x2560 を推奨）
  title                scene_type に入る短い説明
  brief                全体の指示（画風、主人公の外見、起承転結など）。主人公の外見はここで固定する
  lettering            吹き出しの文字の指示（日本語なら「hand-lettered black Japanese text」など）
  panels[]             コマごとの {"identity", "scene", "line"}。line が空ならセリフなし
  must_not[]           禁止事項
  palette[]            色（16進）
"""
import argparse
import json
from pathlib import Path

GUTTER = 20   # コマ間のすき間
MARGIN = 12   # 外枠からの余白
BALLOON_H = 150


def panel_boxes(h, n):
    """縦に n 等分したコマの (y0, y1) を返す。"""
    inner = h - MARGIN * 2
    ph = (inner - GUTTER * (n - 1)) // n
    top = -h // 2 + MARGIN
    return [(top + i * (ph + GUTTER), top + i * (ph + GUTTER) + ph) for i in range(n)]


def build_scene(story, dialog=True):
    w, h = story["width"], story["height"]
    xs = w // 2 - MARGIN
    boxes = panel_boxes(h, len(story["panels"]))
    elements = [{
        "type": "obj", "salience": "primary",
        "identity": story["title"],
        "shape": (f"{len(boxes)} equal stacked panels, slim white gutters, black borders, expressive cartoon acting, "
                  + (story["lettering"] if dialog else "Empty white speech balloons with no text inside.")
                  + " Consistent character in every panel."),
        "colors": [{"color": f"c{i}", "hex": c} for i, c in enumerate(story.get("palette", [])[:3])],
        "bbox": [-h // 2, -w // 2, h // 2, w // 2],
    }]
    for (y0, y1), p in zip(boxes, story["panels"]):
        if dialog and p.get("line"):
            elements.append({"type": "text", "text": p["line"],
                             "bbox": [y0 + MARGIN, -(xs - 18), y0 + BALLOON_H, xs - 18],
                             "shape": "White rounded speech balloon at the top of the panel, black lettering.",
                             "is_watermark": False})
        elements.append({"type": "obj", "salience": "secondary", "identity": p["identity"],
                         "shape": p["scene"], "bbox": [y0, -xs, y1, xs]})
    return {
        "scene_type": story["title"],
        "gen_brief": story["brief"],
        "elements": elements,
        "must_not": story.get("must_not", []),
        "palette": story.get("palette", []),
        "bbox_coord_space": "abs_centralized",
    }


def build_layout(story, dialog=True):
    """USERGUIDE の summary/items 形式。SFT ではどちらの形式でも同等の品質だった。"""
    scene = build_scene(story, dialog)
    items = []
    for e in scene["elements"][1:]:
        if e["type"] == "text":
            items.append({"label": "text", "text": e["text"], "caption": "speech balloon with black hand-lettered text", "bbox": e["bbox"]})
        else:
            items.append({"label": "object", "caption": f'{e["identity"]}: {e["shape"]}', "bbox": e["bbox"]})
    return {"summary": {"caption": scene["gen_brief"] + " " + scene["elements"][0]["shape"]},
            "items": items, "bbox_coord_space": "abs_centralized", "bbox_format": "yxyx"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--format", choices=["scene", "layout"], default="scene")
    ap.add_argument("--no-dialog", action="store_true")
    a = ap.parse_args()
    story = json.loads(Path(a.story).read_text())
    for k in ("width", "height"):
        assert story[k] % 16 == 0, f"{k} は 16 の倍数にする（MOSS-Image の制約）"
    fn = build_scene if a.format == "scene" else build_layout
    Path(a.output).write_text(json.dumps(fn(story, not a.no_dialog), ensure_ascii=False))
    print("wrote", a.output, f'{story["width"]}x{story["height"]}', len(story["panels"]), "panels")


if __name__ == "__main__":
    main()
