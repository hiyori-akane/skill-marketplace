# 成人向け（NSFW）

## 必ず守るルール

1. **描くのは成人だけ。** 主人公の年齢（20代後半・30代など）と大人の体型を、毎回プロンプトに書く。
2. **ネガティブプロンプトに若さの除外を入れる**: `young-looking, childlike, teen, petite, flat chest`
3. **生成した画像を目で見て、成人に見えるかを確かめる。** 成人と指定しても幼く見えることがある（下の「実写と LoRA」）。幼く見える画像は使わない・配らない。作り直す。
4. 性行為の描写は入れない（このスキルが扱うのはヌードまで）。他の人物も入れない。
5. 公開の場に出さない。GitHub の Issue やリポジトリ、SNS のプレビュー（OGP）には、局部の描写がある画像を置かない（GitHub の Acceptable Use Policies）。OGP には、普通の服でも見える程度に切り出して使う。

## LoRA

- [axiomofmind/Moss-image-nsfw-uncensored-lora](https://huggingface.co/axiomofmind/Moss-image-nsfw-uncensored-lora)（SFT 向け、Apache-2.0）。トリガー `moss_xvstyle`、推奨 0.7。
  - mflux: `--lora axiomofmind/Moss-image-nsfw-uncensored-lora:pytorch_lora_weights.safetensors 0.7`
  - ComfyUI: `MOSS-Image-NSFW-Uncensored-LoRA-ComfyUI.safetensors` を `models/loras/` に置く。
- [axiomofmind/Moss-image-anime-lora](https://huggingface.co/axiomofmind/Moss-image-anime-lora): アニメらしさを足す。NSFW LoRA と同時に使える。

## 分かったこと（M1 Max、mflux q8、1024²、30 steps）

- **SFT は LoRA なしでもヌードを描く。** アニメ絵では、LoRA の効果は小さい（強度 0.8 と 1.0 もほぼ同じ）。まず LoRA なしで試す。
- anime LoRA を足すと、アニメらしさが上がる。代わりに局部の描き込みは簡略になる。
- LoRA 1つで +40〜55 秒、2つで +80 秒ほど。メモリは変わらない。

### 実写と LoRA

- 実写は LoRA なしでも、成人女性として自然に描けた。
- NSFW LoRA を使うと、「20代後半」と書いても**顔と体型が幼く見えた**。学習データの偏りが原因と考えられる。
- 直し方（これで成人に見えるようになった）:
  - 年齢を上げて具体的に書く: `mature adult Japanese woman in her mid thirties`
  - 体型を書く: `voluptuous curvy glamour figure, full hips, thick thighs, large heavy breasts`
  - 顔を書く: `mature adult face with defined features`
  - ネガティブ: `young-looking, teen, petite, childlike, flat chest, slim`
- 日本人らしさと可愛らしさを足すなら: `typical Japanese facial features, soft round face, gentle almond-shaped dark brown eyes, small nose, kind warm smile, cute and charming adult beauty`。ネガティブに `western features, caucasian`。年齢と体型の指定は残す。
- 化粧を消すなら: `natural bare face with no makeup` とネガティブ `makeup, blush, lipstick`。

## 成人向け4コマ

`examples/4koma_nsfw_lingerie_ja.json` を使う。全年齢版と同じ手順で作れる。

- `brief` で主人公を「mature adult woman in her late twenties with a voluptuous curvy figure」と固定する。
- `must_not` に `not childlike or young-looking`、`no other people`、`no sexual acts` を入れる。
- mflux で約17分、ComfyUI（fp32 指定）で約25分。4つとも成立した。画の密度は ComfyUI、速さは mflux。
