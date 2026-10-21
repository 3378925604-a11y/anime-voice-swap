---
name: anime-voice-swap
description: '动漫换配音 / 视频换音色 / AI 配音替换：把动漫（或任意人声素材）里的说话声换成指定音色，且 100% 保留原声优的表演（气息、情绪、节奏、口型时序）。基于 Seed-VC 零样本语音转换（voice-to-voice，不是 TTS 念稿），全程本地 GPU，零注册。当用户说"把这个视频的声音换成 XX 音色""换配音""给动漫角色变声""保留表演只换音色"，或提供 目标音色素材+待换声视频 时使用。反触发：只是要朗读/旁白新文本（那是 TTS，用百炼 cosyvoice 或 edge-tts）；只有低码率孤本源且要提画质（那是超分任务，用 video-upscale-cpu）。 English triggers: swap the voice in a video to a target timbre, redub an anime character using a reference voice clip, keep the original acting (breath, emotion, lip-sync timing) but change the voice, voice conversion voice-to-voice not TTS, seed-vc dubbing replacement.'
---

# anime-voice-swap — 动漫换配音（Seed-VC 零样本工作流）

核心认知：**"换声保表演" = Voice Conversion，不是 TTS。** 表演信息全在原声音波形里，任何"文本→语音"路线（含各家音色复刻 TTS）必然丢戏，参数救不回来。Seed-VC 直接吃原人声做音色替换。

## 第 0 步（决定成败）：找原生高码率视频源

先问/先找用户的**导出工程件或原片**（>10Mbps）。有 → 最后成片用 `-c:v copy` 只换音轨，画质零损失。没有高码源时任何超分都追不回被压缩销毁的信息（611kbps 的抖音源超到 4K 也是糊的），此时才和用户确认是否接受低画质或用 video-upscale-cpu 尽力。

## 环境准备（一次性，大文件让用户手动下载）

```powershell
# 1) 代码仓库（浏览器下载后解压到 C:\Users\<你>\tools\seed-vc）
#    https://gh-proxy.com/https://github.com/Plachtaa/seed-vc/archive/refs/heads/main.zip
# 2) 44k 模型权重（约 3.7GB，注意 C 盘余量，跑完中间产物要清）
pip install -U huggingface_hub -i https://mirrors.aliyun.com/pypi/simple
# 用 python -c "from huggingface_hub import snapshot_download; import os; os.environ['HF_ENDPOINT']='https://hf-mirror.com'; snapshot_download('Plachta/Seed-VC', local_dir=r'<models目录>\seed-vc')"
# 3) 隔离环境（复用系统 CUDA torch 2.4.x；transformers 必须 4.46.3）
python -m venv --system-site-packages <venv目录>
<venv>\Scripts\python -m pip install "numpy==1.26.4" "scipy==1.13.1" "librosa==0.10.2" munch "einops==0.8.0" "descript-audio-codec==1.0.0" "pydub==0.25.1" "transformers==4.46.3" "soundfile==0.12.1" hydra-core pyyaml python-dotenv -i https://mirrors.aliyun.com/pypi/simple
```

依赖：系统已有 CUDA 版 torch≈2.4；ffmpeg 在 PATH。RTX 4060 笔记本 8G 显存实测可跑（RTF<1）。

## 标准流程

```
原视频 ── 分离──> vocal.wav + instrumental.wav
目标音色素材 ──② 挑参考段(20s,情绪强、干净)──> ref.wav
vocal + ref ──③ scripts/convert.py──> converted.wav
converted ──④ scripts/fix_edges.py──> 首尾修顺（warm-up 杂讯）
(可选) 单句微调 ──⑤ scripts/convert.py 切段 + crossfade──>
──⑥ scripts/master.py──> 混伴奏 + 响度对齐原片 + copy 换轨成片
```

① 人声分离：用音频分离工具（如 audio-separator/UVR 的 mel-band-roformer 模型）出 44.1k wav；已有分离产物则跳过。
② **参考音段决定一切**：音色、说话气质、情绪强度全来自这 20 秒。从目标素材里挑情绪饱满且无 BGM/噪音的连续段；要"冷静"就用它冷静的段落做参考。
③④⑤⑥ 见各脚本 `--help`。

## 关键参数与已验证经验

- 模型：`DiT_seed_v2_uvit_whisper_base_f0_44k_bigvgan_pruned_ema.pth`（**文件名带 _ema**）+ 同名 yml 配置
- `--f0-condition True`：跟随原音高曲线（配音必开）
- `--auto-f0-adjust True`：整体音高对齐到参考音域
- `--semi-tone-shift`：单句降调/升调（嫌某句太亢奋就 -1/-2）
- `--diffusion-steps 35`：质量/速度平衡点
- **warm-up 伪影**：整条转换首尾各 ~1.5s 会出现 20dB 杂讯爆发（用分段 RMS 对比原人声轨可确诊），`fix_edges.py` 渐入渐出即可；要求更高就加垫音重转首尾段
- 单句重做：切段单独 convert（可换参考段）→ 50ms crossfade 拼回，不整轨重跑
- 混音：伴奏 `volume=0.85`，`amix normalize=0`
- **响度对齐原片**，不要套平台标准（用户要"跟原片一样响"）；TP=-1 防削波
- copy 剪切按关键帧对齐：交付前让用户核开头口型

## 验收

1. 首尾各 1s 与中段 RMS 对比（fix_edges 输出报告）
2. `volumedetect` mean/max（max 应 < -0.5dB）
3. 音轨 start_time=0、时长与画面一致
4. 用户过耳：表演是否还在、单句语气

## 合规红线（发布/使用都适用）

- 参考音色素材需使用者有权使用；复刻真人声音对外发布须标明 AI 配音
- 本 skill 不携带任何音色样本与模型权重，全部用户自取


## English

**Voice conversion, not TTS.** The acting lives in the original waveform; any text→speech route re-reads the script and loses it. Seed-VC replaces timbre while keeping breath, emotion, rhythm and lip-sync timing. Fully local GPU: no API keys, no signups.

**Step 0 (decides the outcome): get a high-bitrate source.** Ask for the export master or original (>10 Mbps). With it, the final cut replaces only the audio track (`-c:v copy`) — zero quality loss. Without it, no upscaling can recover what compression destroyed.

**One-time environment** (downloads are manual by design; exact mirror commands are in the Chinese section above): unzip seed-vc, fetch the 44 kHz weights (~3.7 GB) with `HF_ENDPOINT=https://hf-mirror.com`, then create a `--system-site-packages` venv pinned to `transformers==4.46.3`.

**Pipeline** — `separate → scripts/convert.py → scripts/fix_edges.py → scripts/master.py`. Key parameters: `--f0-condition True` (follow the original pitch curve), `--auto-f0-adjust True` (align to the reference range), `--diffusion-steps 35`, `--semi-tone-shift` for individual lines. About 1.5 s of warm-up noise appears at both ends; `fix_edges.py` fades it out. Redo single lines by cutting segments, converting, then crossfading at 50 ms.

**Verification** — first/last second vs mid-section RMS; `volumedetect` (max below -0.5 dB); audio `start_time=0` with a duration matching the picture; then listen: is the performance still there?

**Compliance** — use reference voices you have the rights to; label AI dubbing when publishing. This skill ships no voice samples and no model weights.
