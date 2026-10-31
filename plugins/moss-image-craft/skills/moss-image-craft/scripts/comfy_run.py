"""ComfyUI（既定 http://127.0.0.1:8000、COMFY_URL か --comfy-url で変更可）に MOSS-Image の API ワークフローを投げ、時間を記録する。

使い方:
  python3 scripts/comfy_run.py --name akane_s1 --prompt-file prompts/akane.txt --seed 1 --steps 30
結果: out/<name>.png と logs/comfy-<name>.json（使ったワークフローと所要時間）
"""
import argparse, json, os, time, urllib.request, uuid
from pathlib import Path

# COMFY_URL / --comfy-url で指定する。
# Comfy Desktop の既定は 8000、素の ComfyUI は 8188
DEFAULT_COMFY_URL = "http://127.0.0.1:8000"
HOST = DEFAULT_COMFY_URL
ROOT = Path.cwd()  # パスはすべてカレントディレクトリ基準
NEG = "worst quality, low quality, blurry, jpeg artifacts, watermark"


def workflow(prompt, seed, steps, cfg, w, h, sampler, scheduler, lora=None, neg=NEG):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "moss_image_sft_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3.5_9b_bf16.safetensors", "type": "moss_image", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae_small.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0],
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": sampler, "scheduler": scheduler, "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "moss_eval"}},
    }
    if lora:
        path, strength = lora
        wf["10"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": path, "strength_model": strength}}
        wf["7"]["inputs"]["model"] = ["10", 0]
    return wf


def call(path, data=None):
    req = urllib.request.Request(HOST + path, data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--cfg", type=float, default=3.0)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--sampler", default="euler")
    ap.add_argument("--scheduler", default="simple")
    ap.add_argument("--lora", nargs=2, metavar=("FILE", "STRENGTH"))
    ap.add_argument("--negative", default=NEG, help="ネガティブプロンプト")
    ap.add_argument("--outdir", default="out", help="画像の保存先")
    ap.add_argument("--comfy-url", help=f"ComfyUI のアドレス（既定: {DEFAULT_COMFY_URL}）")
    a = ap.parse_args()
    global HOST
    HOST = (a.comfy_url or os.environ.get("COMFY_URL") or DEFAULT_COMFY_URL).rstrip("/")

    prompt = (ROOT / a.prompt_file).read_text().strip()
    lora = (a.lora[0], float(a.lora[1])) if a.lora else None
    wf = workflow(prompt, a.seed, a.steps, a.cfg, a.width, a.height, a.sampler, a.scheduler, lora, a.negative)
    t0 = time.time()
    pid = call("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
    while True:
        time.sleep(5)
        hist = call(f"/history/{pid}")
        if pid in hist and hist[pid].get("status", {}).get("completed") is not None:
            break
    elapsed = time.time() - t0
    h = hist[pid]
    out = ROOT / a.outdir / f"{a.name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    for node in h["outputs"].values():
        for img in node.get("images", []):
            q = f"/view?filename={img['filename']}&subfolder={img['subfolder']}&type={img['type']}"
            out.write_bytes(urllib.request.urlopen(HOST + q).read())
    log = {"name": a.name, "args": vars(a), "elapsed_sec": round(elapsed, 1),
           "status": h["status"], "workflow": wf}
    (ROOT / "logs" / f"comfy-{a.name}.json").write_text(json.dumps(log, ensure_ascii=False, indent=1))
    print(f"{a.name}: {elapsed:.1f}s status={h['status'].get('status_str')} -> {out}")


if __name__ == "__main__":
    main()
