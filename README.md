# anime-voice-swap

**EN:** An agent skill that replaces the voice in anime/video clips with a target voice while **100% preserving the original voice actor's performance** — breath, emotion, rhythm, lip-sync timing. Built on [Seed-VC](https://github.com/Plachtaa/seed-vc) zero-shot voice conversion (voice-to-voice, NOT TTS). Fully local GPU pipeline: no API keys, no signups, no per-use cost.

**中文：** 动漫换配音 Agent Skill——把视频里的人声换成指定音色，同时 **100% 保留原声优的表演**（气息、情绪、节奏、口型时序）。基于 Seed-VC 零样本语音转换（voice-to-voice，不是 TTS 念稿）。全程本地 GPU，零 API、零注册、零单次成本。

## Why not TTS voice cloning? / 为什么不用 TTS 音色复刻？

**EN:** The performance you love lives in the original waveform. Text→speech pipelines throw the waveform away and re-read the script — the acting is gone no matter how you tune the parameters. Voice conversion keeps everything and only swaps the timbre.

**中文：** 表演在原声波形里。TTS 路线把波形扔掉、拿文本重新"念"，参数怎么调都救不回戏；语音转换只换音色，表演原样保留。

## Install / 安装

```bash
npx skills add 3378925604-a11y/anime-voice-swap
```
或直接把 `skills/anime-voice-swap/` 拷进你的 agent 技能目录（Claude Code: `.claude/skills/`，OpenCode: `~/.config/opencode/skills/`）。

One-time environment (models & repo are downloaded by you — the skill documents exact mirrors/commands):
一次性环境（模型与代码由用户自行下载，SKILL.md 内含国内镜像直链）：RTX 4060 8GB 实测可跑，需 ffmpeg + CUDA torch≈2.4。

## Usage / 用法

Ask your agent: *"swap this video's voice to the voice in this reference clip, keep the acting"* / *"把这段视频配音换成参考音频的音色，保留原表演"*.

Pipeline / 流程：`separate → convert.py → fix_edges.py → master.py`（单句微调：切段重转 `--semitone` + crossfade）。

## Compliance / 合规

Use only reference voices you have rights to; disclose AI dubbing when publishing. This repo ships no voice samples and no model weights.
仅使用你有权使用的参考音色；对外发布请标注 AI 配音。本仓库不含任何音色样本与模型权重。

## License

MIT
