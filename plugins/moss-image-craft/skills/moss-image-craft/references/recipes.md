# レシピ

どれも `scripts/` のコマンドは、スキルのフォルダ（`SKILL.md` のある場所）から見たパスで書く。

## 1枚絵

```bash
mflux-generate-moss-image -q 8 --seed 1 --steps 30 --width 1024 --height 1024 --output out.png \
  --prompt "masterpiece, best quality, anime style illustration, 1girl, adult woman, pink long hair, heart-shaped pupils, gentle smile, sitting at a cafe window, soft afternoon sunlight, upper body"
```

タグ列でも文章でも描ける。実写も描ける（`a photograph of ...`、`shot on a 50mm lens`、`realistic skin texture`）。

## 文字入りポスター

```text
A cute anime-style cafe poster. A pink-haired girl holding a latte in the lower half.
At the top, large bold rounded lettering reads "HIYORI CAFE", and below it smaller text reads "Open 10:00 - 18:00".
Pastel pink and cream color palette, clean flat illustration.
```

文字は `reads "..."` で書く。1024²、30 steps、cfg 3 で崩れずに出た。

## 4コマ漫画（セリフ入り）

1. `examples/4koma_cake_ja.json` をコピーし、`brief`（画風・主人公）と `panels`（場面とセリフ）を書き換える。
2. JSON にする: `python3 scripts/make_comic.py my_story.json -o prompt.json`
3. 生成する（どれか1つ）:
   - mflux: `mflux-generate-moss-image -q 8 --prompt-file prompt.json --seed 1 --steps 30 --guidance 5 --width 640 --height 2560 --output out.png`
   - felix: `moss-mlx "$(cat prompt.json)" --turbo --seed 1 --guidance 5 --width 640 --height 2560 -o out.png`
   - ComfyUI: `python3 scripts/comfy_run.py --name koma --prompt-file prompt.json --seed 1 --steps 30 --cfg 5 --width 640 --height 2560`
4. セリフ4つ、キャラの一貫性、起承転結を目で確かめる。

- コマ数は `panels` の数で決まる。縦横比はコマ数に合わせる（4コマは 1:4、8コマは 1:8）。
- 英語のセリフでも同じ品質で出る。
- `--no-dialog`（吹き出しを空にする）は非推奨。吹き出しが乱れる。
- 方法ごとの比較画像: `python3 scripts/compare.py cmp.jpg a.png:ComfyUI b.png:"felix turbo" c.png:"mflux"`

## 公式8コマの再現

公式ギャラリー `assets/images/003`（OpenMOSS/MOSS-Image）の parameters.json を使う。

- `parameters` 欄は JSON のオブジェクト。`json.load` で読み、`prompt` を取り出せばよい（`eval` は要らない）。
- 条件: Base、512x4096、50 steps、cfg 5、shift 5、uncond-skip-layers 22、seed 42、ネガティブ `worst quality, low quality, blurry, jpeg artifacts`。
- felix 版なら `moss-mlx --parameters parameters.json` でそのまま再現できる。
- mflux: `--model moss-image-base -q 8`。M1 Max で 1ステップ 48 秒、約40分、36GB。構成とセリフはほぼ公式どおり。ピクセル単位では一致しない。

## OGP・バナー（実画像のはめ込み付き）

1. `examples/ogp_note.json` をコピーし、`texts`（見出し・帯・バッジ）、`objects`（キャラ）、`frames`（写真枠）を書き換える。
2. JSON にする: `python3 scripts/make_banner.py my_ogp.json -o prompt.json`
3. 16 の倍数で生成する（1280x670 なら 1280x672）。シードを2〜4個試す。
4. 文字を目で確かめる。抜けたら `references/prompting.md` の「文字を正しく出す」。
5. 仕上げる:
   ```bash
   python3 scripts/compose_banner.py raw.png ogp.png --spec my_ogp.json \
     --image photo.png:128,40,896,472 --crop-to 1280x670 --sticker "スキル/配布中！"
   ```
   - `--image` は frames の順。`:left,top,right,bottom` で元画像の切り出し範囲を指定する。
   - `--sticker` は星形のステッカー。`/` で改行。位置は `--sticker-at x,y`（切りそろえた後の座標）。

- 表情は caption で調整する。「screaming」まで振り切ると叫びに見える。驚きにとどめるなら `pleasantly surprised, small open mouth in a soft gasp, one hand lightly touching her cheek`。
- 公開の場（SNS・note のフィード）に出る画像なので、肌の露出は「普通の服でも見える程度」までにする。

## 証跡を残す（ブログ・検証記事向け）

```bash
scripts/run.sh <名前> <出力先> <コマンド...>   # logs/<名前>.log に実行時間とピークメモリを記録
```

`/usr/bin/time -l` の `real`（秒）と `peak memory footprint`（バイト）を読む。
