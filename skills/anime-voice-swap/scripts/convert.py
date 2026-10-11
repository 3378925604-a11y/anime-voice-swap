# -*- coding: utf-8 -*-
"""Seed-VC 零样本语音转换封装。
用法: python convert.py --source vocal.wav --ref ref20s.wav --out-dir out/
      [--semitone 0] [--steps 35] [--f0-follow] [--vc-dir C:\\Users\\<u>\\tools\\seed-vc]
      [--venv-python <venv>\\Scripts\\python.exe] [--ckpt <模型.pth>] [--config <模型.yml>]
前置: 环境变量 HF_ENDPOINT=https://hf-mirror.com（国内）。
"""
import argparse, glob, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='待转换人声 wav')
    ap.add_argument('--ref', required=True, help='目标音色参考段 wav(建议10~25s,情绪饱满)')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--semitone', type=int, default=0)
    ap.add_argument('--steps', type=int, default=35)
    ap.add_argument('--vc-dir', default=os.path.expandvars(r'%USERPROFILE%\tools\seed-vc'))
    ap.add_argument('--venv-python', default=os.path.expandvars(r'%USERPROFILE%\tools\seedvc-env\Scripts\python.exe'))
    ap.add_argument('--ckpt', default=os.path.expandvars(r'%USERPROFILE%\models\seed-vc\DiT_seed_v2_uvit_whisper_base_f0_44k_bigvgan_pruned_ema.pth'))
    ap.add_argument('--config', default=os.path.expandvars(r'%USERPROFILE%\models\seed-vc\config_dit_mel_seed_uvit_whisper_base_f0_44k.yml'))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    env = dict(os.environ, HF_ENDPOINT='https://hf-mirror.com')
    cmd = [a.venv_python, '-X', 'utf8', 'inference.py',
           '--source', a.source, '--target', a.ref, '--output', a.out_dir,
           '--diffusion-steps', str(a.steps), '--f0-condition', 'True',
           '--auto-f0-adjust', 'True', '--semi-tone-shift', str(a.semitone),
           '--checkpoint', a.ckpt, '--config', a.config, '--fp16', 'True']
    r = subprocess.run(cmd, cwd=a.vc_dir, capture_output=True, text=True, errors='replace', env=env)
    out = sorted(glob.glob(os.path.join(a.out_dir, '*.wav')), key=os.path.getmtime)
    if not out:
        print('FAILED:\n', (r.stdout + r.stderr)[-800:]); sys.exit(1)
    print('OK ->', out[-1])

if __name__ == '__main__':
    main()
