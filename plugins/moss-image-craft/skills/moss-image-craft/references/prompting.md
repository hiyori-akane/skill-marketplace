# プロンプトの書き方

公式ガイド: [USERGUIDE.md](https://github.com/OpenMOSS/MOSS-Image/blob/main/USERGUIDE.md)

## 3つの形式

| 形式 | 使う場面 | 例 |
|---|---|---|
| 文章（またはタグ） | 1枚絵、短い文字入れ | `examples` 外。下の「文字を正しく出す」 |
| scene JSON | 漫画（公式8コマと同じ形） | `scripts/make_comic.py` の既定 |
| summary/items | ポスター、OGP、配置を決めたいもの | `scripts/make_banner.py`、`make_comic.py --format layout` |

SFT では、漫画を scene JSON と summary/items のどちらで書いても同じくらいの品質だった。

### scene JSON

```json
{"scene_type": "...", "gen_brief": "全体の指示",
 "elements": [
   {"type": "obj", "salience": "primary", "identity": "...", "shape": "...", "bbox": [y0, x0, y1, x1]},
   {"type": "text", "text": "描かせる文字", "shape": "文字の見た目", "bbox": [...], "is_watermark": false},
   {"type": "obj", "salience": "secondary", "identity": "コマ1", "shape": "コマの内容", "bbox": [...]}],
 "must_not": ["禁止事項"], "palette": ["#FFFFFF"], "bbox_coord_space": "abs_centralized"}
```

### summary/items

```json
{"summary": {"caption": "全体の説明"},
 "items": [{"label": "text", "text": "文字", "caption": "見た目", "bbox": [y0, x0, y1, x1]},
           {"label": "object", "caption": "物の説明", "bbox": [...]}],
 "bbox_coord_space": "abs_centralized", "bbox_format": "yxyx"}
```

## 座標

- `abs_centralized`: キャンバスの中心が (0, 0)。640x2560 なら y は -1280〜1280、x は -320〜320。
- bbox は `[y_min, x_min, y_max, x_max]`（yxyx）。
- 解像度は 16 の倍数。0.25M〜4M ピクセル。推奨は 1M〜2M。

## 生成設定

| 用途 | steps | cfg | 備考 |
|---|---|---|---|
| 1枚絵・ポスター | 30（公式推奨は 50 以上） | 3 | 30 でも十分きれい |
| 漫画 | 30〜50 | 5 | `uncond-skip-layers 22`（mflux の既定） |
| 公式8コマの再現 | 50 | 5 | Base、512x4096、seed 42、shift 5 |

ネガティブプロンプトの基本: `worst quality, low quality, blurry, jpeg artifacts, watermark`

## 文字を正しく出す

- 描かせたい文字は、そのまま書く（日本語・英語・中国語）。日本語は公式にうたわれていないが、かな・漢字とも崩れずに出た。
- 漫画のセリフは、コマ上部の吹き出しの bbox に `text` として置く。
- **長い見出しは1文字抜けることがある**（例：「もう漫画家いらない！？」→「いない」）。直し方:
  1. caption に正確な並びを書く: `reads exactly もう漫画家いらない！？ (eleven characters: も う 漫 画 家 い ら な い ！ ？, do not drop ら)`
  2. ネガティブプロンプトに `misspelled text, missing characters` を足す。
  3. シードを変えて2〜4枚作り、正しいものを選ぶ。
- 似た形の字は化けることがある（「4コマ」→「4コ毛」）。仕上がりを必ず目で確かめる。

## キャラを全コマでそろえる

- 主人公の外見（髪・目・服・体型・年齢）は `gen_brief` に1回だけ書き、「keep her design identical in all four panels」と添える。
- 各コマの `shape` には、その場面の動作と表情だけを書く。
- `must_not` に `not a different character design between panels` を入れる。
