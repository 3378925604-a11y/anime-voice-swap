---
name: anime-voice-swap
description: 'Replace the voice in anime/video clips with a target voice while 100% preserving the original voice actor performance (breath, emotion, timing, lip-sync). Seed-VC zero-shot voice conversion (voice-to-voice, NOT TTS). Local GPU, no API, no signup. Use when asked to "swap the voice", "dub into another character voice", "change voice keep the acting", or given a reference voice clip + a video to re-voice. Anti-trigger: narrating NEW text (that is TTS); low-bitrate source needing quality boost (that is video-upscale-cpu). 中文：把视频里的人声换成指定音色且 100% 保留原声优表演（气息/情绪/节奏/口型），本地 Seed-VC 零样本语音转换，非 TTS 念稿，免注册。'
---

# anime-voice-swap — Seed-VC 零样本换配音 / Zero-shot Voice Swap

**EN — Core insight:** "swap voice, keep the acting" = **Voice Conversion**, not TTS. Performance lives in the original waveform; any text→speech route (including voice-cloned TTS) discards it and no parameter can bring it back. Seed-VC converts timbre directly on the original vocal.
**中文核心认知：** 换声保表演 = Voice Conversion，不是 TTS。表演信息全在原声波形里，任何"文本→语音"路线必然丢戏。

## Step 0 (decides everything): find the native high-bitrate video source
先找用户的原生高码率导出件（>10Mbps）。有 → 成片 `-c:v copy` 只换音轨，画质零损失。没有才考虑超分（超分追不回被压缩销毁的信息，见 video-upscale-cpu）。

## Environment (one-time; large files should be downloaded by the user)
```powershell
# Repo (browser): https://gh-proxy.com/https://github.com/Plachtaa/seed-vc/archive/refs/heads/main.zip  → unzip to <home>\tools\seed-vc
# Weights (~3.7GB, watch disk space):
pip install -U huggingface_hub -i https://mirrors.aliyun.com/pypi/simple
python -c "import os;os.environ['HF_ENDPOINT']='https://hf-mirror.com';from huggingface_hub import snapshot_download;snapshot_download('Plachta/Seed-VC',local_dir=os.path.expandvars(r'%USERPROFILE%\models\seed-vc'))"
# Isolated venv (reuses system CUDA torch≈2.4; transformers MUST be 4.46.3):
python -m venv --system-site-packages <home>\tools\seedvc-env
<home>\tools\seedvc-env\Scripts\python -m pip install "numpy==1.26.4" "scipy==1.13.1" "librosa==0.10.2" munch "einops==0.8.0" "descript-audio-codec==1.0.0" "pydub==0.25.1" "transformers==4.46.3" "soundfile==0.12.1" hydra-core pyyaml python-dotenv -i https://mirrors.aliyun.com/pypi/simple
```
Tested on RTX 4060 Laptop 8GB (RTF<1). Needs ffmpeg in PATH.

## Pipeline
```
video ──① separate──> vocal.wav + instrumental.wav   (audio-separator / UVR, 44.1k)
target voice clip ──② pick 20s emotional clean segment──> ref.wav
vocal + ref ──③ scripts/convert.py──> converted.wav
converted ──④ scripts/fix_edges.py──> head/tail warm-up artifacts removed
(optional per-line tuning: re-cut segment → convert.py --semitone ±n → 50ms crossfade)
──⑤ scripts/master.py──> mix BGM + loudness-match original + copy-mux final MP4
```
**②参考音段决定一切 / The reference segment decides everything:** timbre AND speaking temperament come from these 20 seconds. Pick an emotionally-rich, BGM-free stretch of the target voice.

## Verified parameters & pitfalls（已验证参数与坑）
- Model: `DiT_seed_v2_uvit_whisper_base_f0_44k_bigvgan_pruned_ema.pth` (**note the `_ema` suffix**) + its yml
- `--f0-condition True` follow original pitch contour (mandatory for dubbing)
- `--auto-f0-adjust True` align overall pitch to the reference's range
- `--semi-tone-shift -1/-2` calm down one overly-excited line
- `--diffusion-steps 35` quality/speed sweet spot
- **Warm-up artifacts:** first & last ~1.5s of a full-track conversion carry ~20dB noise bursts (diagnose via per-segment RMS vs original vocal). `fix_edges.py` fades them; for stricter needs re-convert edge segments with 1s context padding.
- Mix: instrumental `volume=0.85`, `amix normalize=0`
- **Loudness: match the ORIGINAL video's level** — do not impose platform targets (users want "as loud as the original"); `TP=-1` to avoid clipping
- `-c:v copy` cut aligns to keyframes — have the user check lip-sync at the head

## Acceptance（验收）
1. head/tail vs mid RMS report (fix_edges prints it)
2. `volumedetect` mean/max (max < -0.5dB)
3. audio start_time=0, A/V duration aligned
4. human ears: is the performance still there; per-line tone

## Compliance（合规红线）
- Only use reference voices you have rights to; disclose AI dubbing when publishing.
- This skill ships NO voice samples and NO model weights — users download them.
