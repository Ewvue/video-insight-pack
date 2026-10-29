#!/usr/bin/env python3
"""Locate and extract key frames from a LOCAL video file with ffmpeg.

ffmpeg comes from `pip install imageio-ffmpeg` (bundled binary) or the system PATH.

  # contact sheets: one tile every N seconds, 8x6 tiles per sheet, timestamp burned in
  python3 extract_frames.py video.mp4 sheet --every 10 [--start 40:00 --end 45:00] --out sheets/

  # exact full-resolution frames, saved as MM-SS.jpg (rename them afterwards)
  python3 extract_frames.py video.mp4 grab 41:55 42:57 1:02:03 --out frames/
"""
import argparse
import os
import shutil
import subprocess
import sys


def ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("ffmpeg not found: pip install imageio-ffmpeg (or install ffmpeg)")
    return exe


def secs(ts):
    parts = [float(p) for p in str(ts).split(":")]
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def label(t):
    t = int(round(t))
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}-{m:02d}-{s:02d}" if h else f"{m:02d}-{s:02d}"


def duration(ff, video):
    r = subprocess.run([ff, "-i", video], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            return secs(line.split("Duration:")[1].split(",")[0].strip())
    return None


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + r.stderr[-1500:])


def grab(ff, video, times, out):
    os.makedirs(out, exist_ok=True)
    for ts in times:
        t = secs(ts)
        dst = os.path.join(out, f"{label(t)}.jpg")
        run([ff, "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "2", dst])
        print(dst)


def sheet(ff, video, every, start, end, out, cols=8, rows=6):
    os.makedirs(out, exist_ok=True)
    dur = duration(ff, video) or end or 0
    start = start or 0.0
    end = min(end or dur, dur) if dur else end
    per = cols * rows
    span = every * per
    t, n = start, 0
    while t < end:
        length = min(span, end - t)
        dst = os.path.join(out, f"sheet_{label(t)}.png")
        base = [ff, "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-t", f"{length:.3f}", "-i", video]
        # select (not fps): keeps the first frame of each step, so the burned-in time matches the picture
        pick = f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{every - 0.01})',scale=320:-2"
        stamped = (f"{pick},"
                   f"drawtext=text='%{{pts\\:hms\\:{t:.3f}}}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.7,"
                   f"tile={cols}x{rows}")
        r = subprocess.run(base + ["-vf", stamped, "-fps_mode", "vfr", "-frames:v", "1", dst], capture_output=True, text=True)
        if r.returncode != 0:
            # Some ffmpeg builds lack drawtext/fonts; fall back to unlabeled tiles.
            run(base + ["-vf", f"{pick},tile={cols}x{rows}", "-fps_mode", "vfr", "-frames:v", "1", dst])
            print(f"{dst}  (no timestamps: tile k starts at {label(t)} + k*{every:g}s)")
        else:
            print(dst)
        t += span
        n += 1
    print(f"{n} sheet(s); each tile = {every}s, read left-to-right, top-to-bottom")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("--every", type=float, default=10)
    s.add_argument("--start")
    s.add_argument("--end")
    s.add_argument("--out", default="sheets")
    g = sub.add_parser("grab")
    g.add_argument("times", nargs="+")
    g.add_argument("--out", default="frames")
    a = ap.parse_args()
    if not os.path.isfile(a.video):
        sys.exit(f"no such file: {a.video}")
    ff = ffmpeg_bin()
    if a.cmd == "grab":
        grab(ff, a.video, a.times, a.out)
    else:
        sheet(ff, a.video, a.every, secs(a.start) if a.start else None, secs(a.end) if a.end else None, a.out)


if __name__ == "__main__":
    main()
