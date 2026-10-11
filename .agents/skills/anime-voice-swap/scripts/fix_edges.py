# -*- coding: utf-8 -*-
"""检测并修复整轨转换的首尾 warm-up 杂讯（对比原人声轨分段 RMS，自动 afade）。
用法: python fix_edges.py --converted vc.wav --original vocal.wav --out fixed.wav
      [--edge 1.7] [--thresh 6.0]
thresh: 首/尾段 RMS 比原曲同段高超过该 dB 数则判定有伪影并加淡入淡出。
"""
import argparse, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def rms_at(p, t, d):
    r = subprocess.run(['ffmpeg', '-ss', str(t), '-t', str(d), '-i', p,
                        '-af', 'astats=measure_perchannel=none:measure_overall=RMS_level',
                        '-f', 'null', '-'], capture_output=True, text=True, errors='replace')
    m = re.search(r'RMS level dB:\s*([-\d.]+)', r.stderr)
    return float(m.group(1)) if m else -90.0

def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', p], capture_output=True, text=True)
    return float(r.stdout.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--converted', required=True)
    ap.add_argument('--original', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--edge', type=float, default=1.7)
    ap.add_argument('--thresh', type=float, default=6.0)
    a = ap.parse_args()
    D = dur(a.converted)
    e = min(a.edge, D / 3)
    head_c, head_o = rms_at(a.converted, 0, e), rms_at(a.original, 0, e)
    tail_c, tail_o = rms_at(a.converted, D - e, e), rms_at(a.original, D - e, e)
    print(f'head: converted {head_c:.1f} vs original {head_o:.1f} dB')
    print(f'tail: converted {tail_c:.1f} vs original {tail_o:.1f} dB')
    f = []
    if head_c - head_o > a.thresh:
        f.append(f'afade=t=in:st=0:d={e}')
    if tail_c - tail_o > a.thresh:
        f.append(f'afade=t=out:st={D - e:.3f}:d={e:.3f}')
    if not f:
        print('edges clean, copy through')
        import shutil; shutil.copyfile(a.converted, a.out); return
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.converted,
                    '-af', ','.join(f), '-c:a', 'pcm_s16le', a.out], check=True)
    print('fixed ->', a.out, '| fades:', f)

if __name__ == '__main__':
    main()
