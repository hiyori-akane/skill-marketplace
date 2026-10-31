# 動かし方（Mac / Apple Silicon）

3通りある。どれも M1 Max 64GB で動作を確かめた（2026-10）。

## A. mflux（MLX）— スクリプトで量産・LoRA

```bash
# 必ず main から入れる（理由は下の「mflux が真っ黒になる」）
uv tool install --force "git+https://github.com/mflux-community/mflux@main"

mflux-generate-moss-image --model moss-image-sft -q 8 \
  --prompt-file prompt.json --seed 1 --steps 30 --guidance 5 \
  --width 640 --height 2560 --output out.png
```

- `--model moss-image-sft`（既定）か `moss-image-base`。初回に重みを Hugging Face から取る。
- `-q 8` で 8bit 量子化。`--negative-prompt`、`--uncond-skip-layers`（既定 22）、`--lora PATH SCALE`（複数可）が使える。
- LoRA は `--lora org/repo:file.safetensors 0.7` の形で Hugging Face から直接読める。
- `--negative-prompt` を zsh の変数で渡すときは、配列にして `"${M[@]}"` で展開する。文字列のまま展開すると、カンマ区切りの語が別の引数になって失敗する（`unrecognized arguments`）。

### mflux が真っ黒になる（NaN）

- 症状: 長いプロンプト（約350トークン以上）で、出力が真っ黒になる。ログに `RuntimeWarning: invalid value encountered in cast` が出る。
- 原因: テキストエンコーダー（Qwen3.5）の Gated DeltaNet 層で、チャンクごとの逆行列を「繰り返し二乗」で計算していた。float32 の桁落ちで NaN になる（Issue [#920](https://github.com/mflux-community/mflux/issues/920)）。
- 修正: PR [#939](https://github.com/mflux-community/mflux/pull/939)（2026-10-27 マージ）。PyPI の **0.24.0 はこれより前のリリースで、修正が入っていない**。0.24.1 以降か main を使う。
- 漫画の JSON は 600〜900 トークン、公式8コマは約 7000 文字になるので、この修正が必須。

## B. moss-image-mlx（felix 版、MLX）— いちばん速い

```bash
uv tool install moss-image-mlx
moss-mlx "$(cat prompt.json)" --turbo --seed 1 --guidance 5 --width 640 --height 2560 -o out.png
```

- `--turbo` は 10〜15 パスで、通常の約6倍速い。4コマで約4.4分、ピークメモリ 11GB。表情の強さは少し落ちる。
- `--parameters parameters.json` で、公式ギャラリーの parameters.json をそのまま再現できる。
- 長いプロンプトでも NaN にならなかった。
- `--lora FILE@STRENGTH` で Kohya 形式の LoRA を使える。

## C. ComfyUI — 画の密度が最も高い

- ComfyUI **0.43 以上**が MOSS-Image に標準で対応する（PR #17095）。Comfy Desktop も更新すれば使える。
- 重み（[Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image)）:
  - `diffusion_models/moss_image_sft_bf16.safetensors`（10.2GB）
  - `text_encoders/qwen3.5_9b_bf16.safetensors`（19.3GB）。`w4a8_gptq` 版は MPS での動作を確かめていない
  - `vae/flux2-vae_small.safetensors`
- ノード: `UNETLoader` → `CLIPLoader`（type `moss_image`）→ `CLIPTextEncode` ×2 → `EmptyFlux2LatentImage` → `KSampler`（euler / simple）→ `VAEDecode`。shift 5 はモデル側の既定値。
- `scripts/comfy_run.py` がこのワークフローを API に送る。接続先は `COMFY_URL` か `--comfy-url`（Comfy Desktop の既定は 8000、素の ComfyUI は 8188）。LoRA は `--lora file.safetensors 0.7`（`models/loras/` に置いた ComfyUI 形式のファイル）。
- MPS は float64 を使えない。ComfyUI 本体の `rope()` が CPU に逃がすので、パッチは要らない（0.43 で確認）。
- Comfy Desktop の起動引数に `--force-fp32` などがあると、メモリと時間が bf16 の約2倍になる。

## メモリの目安（M1 Max 64GB）

| 方法 | 1024² | 640x2560 | 512x4096 |
|---|---|---|---|
| mflux q8 | 22GB | 30GB | 36GB（Base） |
| felix 8bit turbo | — | 11GB | — |
| ComfyUI bf16 | モデルだけで約 28GB | — | — |

2つの方法を同時に動かさない。メモリが足りなくなり、時間の計測も乱れる。
