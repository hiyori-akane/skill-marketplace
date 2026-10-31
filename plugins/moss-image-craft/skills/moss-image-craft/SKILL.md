---
name: moss-image-craft
description: MOSS-Image（OpenMOSS の 5B text-to-image。日本語・中国語・英語の文字を描け、JSON レイアウトで配置を指定できる）を Mac（Apple Silicon）で動かし、セリフ入りの4コマ・8コマ漫画、文字入りポスター、OGP・サムネイル、成人向け（NSFW）イラストまでを作るスキル。mflux・moss-image-mlx（felix 版）・ComfyUI の3通りの動かし方、漫画の JSON プロンプトの作り方、バナーへの実画像のはめ込み、既知の不具合（長いプロンプトで真っ黒・文字抜け）の直し方を含む。ユーザーが「MOSS-Imageで」「MOSS Imageを試したい」「4コマ漫画を生成して」「セリフ入りの漫画を作って」「漫画をAIで一発生成」「OGP画像を作って」「サムネを作って」「文字入りの画像を作って」「mfluxで真っ黒になる」「moss-mlx」「MOSS-ImageのLoRA」「NSFWの4コマ」などと言ったら必ず使う。
---

# MOSS-Image Craft

MOSS-Image で、プロンプト1つから「文字まで入った完成画像」を作るスキル。
判断が要る手順だけをここに置き、詳細は `references/` に分ける。

| ファイル | 中身 |
|---|---|
| `references/setup.md` | 3通りの動かし方（mflux / felix 版 / ComfyUI）、重み、既知の不具合 |
| `references/prompting.md` | プロンプトの形式（文章・scene JSON・summary/items）、座標、文字を正しく出すコツ |
| `references/recipes.md` | 1枚絵、文字入りポスター、4コマ、公式8コマの再現、OGP・バナー |
| `references/nsfw.md` | 成人向けの作り方と、必ず守るルール |
| `references/benchmarks.md` | M1 Max 64GB での実測（時間・メモリ・結果） |
| `scripts/` | `make_comic.py`（漫画の JSON）、`make_banner.py` と `compose_banner.py`（OGP）、`compare.py`（比較画像）、`comfy_run.py`（ComfyUI API）、`run.sh`（時間とメモリの記録） |
| `examples/` | ストーリー定義（4コマ、成人向け4コマ）とバナー定義（note の OGP） |

## 0. 最初に決めること

1. **何を作るか**を決め、`references/recipes.md` の該当レシピを読む。
2. **どれで動かすか**を決める。迷ったら次の表で選び、`references/setup.md` を読む。

| 目的 | おすすめ | 理由 |
|---|---|---|
| とにかく速く試す | felix 版 `moss-mlx --turbo` | 4コマで約4.4分、メモリ 11GB |
| スクリプトで量産・LoRA を使う | mflux（**main から入れる**） | CLI が素直で LoRA も使える。PyPI の 0.24.0 は長いプロンプトで真っ黒になる |
| 画の密度を最優先 | ComfyUI（0.43 以上） | 描き込みが最も細かい。そのぶん遅い |

3. **成人向けなら** `references/nsfw.md` を必ず先に読む。

## 1. 作る手順

1. プロンプトを作る。
   - 1枚絵なら文章でよい。文字を入れるなら、描かせたい文字をそのまま `"..."` で書く。
   - 漫画なら `examples/4koma_cake_ja.json` をまねてストーリー定義を書き、`scripts/make_comic.py` で JSON にする。
   - OGP・バナーなら `examples/ogp_note.json` をまねて定義を書き、`scripts/make_banner.py` で JSON にする。
2. 解像度を **16 の倍数**にする。半端なサイズ（例 1280x670）は、16 の倍数（1280x672）で作ってから切る。
3. 生成する。記事や検証の証跡が要るなら `scripts/run.sh` で包み、時間とピークメモリを残す。
4. **画像を目で見て確かめる**。次の3点は毎回見る。
   - 真っ黒でないか（真っ黒なら `references/setup.md` の「mflux が真っ黒になる」）。
   - 文字が正しいか。1文字抜け・誤字はよく起きる（例：「いらない」→「いない」、「4コマ」→「4コ毛」）。
   - キャラが全コマで同じに見えるか。
5. 外れたらシードを変えて2〜4枚作り、良いものを選ぶ。文字が抜けるなら `references/prompting.md` の「文字を正しく出す」を当てる。
6. 実画像を枠に入れる・ステッカーを足すなどの仕上げは、`scripts/compose_banner.py` で後処理する。

## 2. 外さないための要点

- 漫画は **cfg 5**、ほかは cfg 3 が基準。漫画は縦長 1:4（640x2560）で4コマ、1:8（512x4096）で8コマ。
- セリフは**入れて**生成する。吹き出しを空にすると、吹き出しの位置が乱れたり消えたりする。
- SFT と Base はどちらも漫画を描ける。公式の8コマ作例は Base（`references/recipes.md`）。
- MOSS-Image は既存の画像を描き込めない。実画像を載せたいときは「空の写真枠」を描かせ、後処理で貼る。
- 生成は重い。M1 Max で 1024² 30 steps が約9分、4コマが17分前後。待つ間に次の準備をする。
