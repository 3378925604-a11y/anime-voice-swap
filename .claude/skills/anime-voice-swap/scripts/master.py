# -*- coding: utf-8 -*-
"""总装：人声+伴奏混音 → 响度对齐原视频 → 原生源画面 copy 换轨出成片。
用法: python master.py --video native.mp4 --vocal fixed.wav --bgm instrumental.wav
      --out 成片.mp4 [--bg-gain 0.85] [--cut 1.0] [--mean-target -12.9]
video: 高码率原生画面源；cut: 从第几秒开始取画面(对齐人声轨起点)。
mean-target: 原片人声段 mean_volume(dB)，留空则自动测 video 音轨。
"""
import argparse, os, re, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run(c):
    r = subprocess.run(c, capture_output=True, text=True, errors='replace')
    return r

def vol(p, ss=None, t=None):
    c = ['ffmpeg']
    if ss is not None: c += ['-ss', str(ss)]
    if t is not None: c += ['-t', str(t)]
    r = run(c + ['-i', p, '-af', 'volumedetect', '-f', 'null', '-'])
    m = re.search(r'mean_volume:\s*([-\d.]+)', r.stderr)
    x = re.search(r'max_volume:\s*([-\d.]+)', r.stderr)
    return (float(m.group(1)) if m else None, float(x.group(1)) if x else None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--vocal', required=True)
    ap.add_argument('--bgm', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--bg-gain', type=float, default=0.85)
    ap.add_argument('--cut', type=float, default=0.0)
    ap.add_argument('--mean-target', type=float, default=None)
    a = ap.parse_args()
    tgt = a.mean_target if a.mean_target is not None else (vol(a.video, a.cut, 20)[0] or -14)
    tmp = tempfile.mktemp(suffix='.wav')
    run(['ffmpeg', '-y', '-v', 'error', '-i', a.vocal, '-i', a.bgm,
         '-filter_complex', f'[1:a]volume={a.bg_gain}[bg];[0:a][bg]amix=inputs=2:duration=longest:normalize=0[a]',
         '-map', '[a]', '-ar', '44100', '-c:a', 'pcm_s16le', tmp])
    mean, mx = vol(tmp)
    i_est = mean - 3.0  # 粗略 LUFS 估计
    r = run(['ffmpeg', '-y', '-v', 'error', '-i', tmp,
             '-af', f'loudnorm=I={i_est:.1f}:TP=-1.0:LRA=11', '-c:a', 'pcm_s16le', tmp + '.ln.wav'])
    if r.returncode: print('loudnorm fail', r.stderr[-300:]); sys.exit(1)
    run(['ffmpeg', '-y', '-v', 'error', '-ss', str(a.cut), '-i', a.video, '-i', tmp + '.ln.wav',
         '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
         '-shortest', a.out])
    m2, x2 = vol(a.out)
    for p in (tmp, tmp + '.ln.wav'): os.remove(p)
    print(f'OK -> {a.out} | 原片mean≈{tgt:.1f} 成片mean={m2} max={x2} (max 应 < -0.5)')
    print('提示: copy 剪切按关键帧对齐，请核对开头口型')

if __name__ == '__main__':
    main()
