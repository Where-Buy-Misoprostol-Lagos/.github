#!/usr/bin/env python3
"""Assemble a faceless video from beats: one image (or clip) + one voice line each.

Usage:
    python3 assemble.py manifest.json

manifest.json:
{
  "out": "out/video_long.mp4",
  "aspect": "16:9",               # or "9:16"
  "captions": true,               # burn word-chunk captions from each beat's text
  "music": "music.mp3",           # optional instrumental bed (looped, ducked under voice)
  "music_volume": 0.12,           # optional, 0-1
  "beats": [
    {"image": "img/01.png", "audio": "vo/01.mp3", "text": "Spoken line for this beat."},
    {"clip":  "clips/02.mp4", "audio": "vo/02.mp3", "text": "A beat that uses an AI video clip."}
  ]
}

Each beat lasts exactly as long as its voice line (+ a short breath), so picture, voice and
captions can never drift apart. Stills get a slow zoom or pan so nothing sits frozen.
Paths are resolved relative to the manifest file. Needs ffmpeg + ffprobe on PATH.
"""
import json
import os
import subprocess
import sys
import tempfile

FPS = 30
BREATH = 0.15  # seconds of silence after each line
SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
# Motion presets cycled per still: (zoom start, zoom end, x drift, y drift) as fractions.
MOVES = [
    (1.00, 1.12, 0.0, 0.0),    # slow push in
    (1.12, 1.00, 0.0, 0.0),    # slow pull out
    (1.08, 1.08, -0.5, 0.0),   # pan left to right
    (1.08, 1.08, 0.5, 0.0),    # pan right to left
    (1.00, 1.10, 0.0, -0.4),   # push in drifting up
]


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{res.stderr[-2000:]}")
    return res.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def still_segment(img, dur, w, h, move, out):
    z0, z1, dx, dy = move
    frames = max(1, round(dur * FPS))
    # Oversample 2x before zoompan: removes the stair-step jitter zoompan has at 1x.
    W, H = w * 2, h * 2
    z = f"({z0}+({z1}-{z0})*on/{frames})"
    x = f"(iw-iw/{z})/2+({dx})*(iw-iw/{z})/2*(2*on/{frames}-1)"
    y = f"(ih-ih/{z})/2+({dy})*(ih-ih/{z})/2*(2*on/{frames}-1)"
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={FPS},"
          f"format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", img, "-vf", vf,
         "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", "-an", out])


def clip_segment(clip, dur, w, h, out):
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"fps={FPS},format=yuv420p")
    # Loop short clips so the picture always covers the whole line.
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", clip, "-t", f"{dur:.3f}",
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", out])


def ass_time(t):
    cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def caption_events(text, start, end, max_words):
    """Split a line into short chunks timed by character length (speech tracks it closely)."""
    words = text.split()
    if not words:
        return []
    chunks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
    weights = [sum(len(wd) + 1 for wd in c) for c in chunks]
    total, t, events = sum(weights), start, []
    for chunk, wgt in zip(chunks, weights):
        t2 = t + (end - start) * wgt / total
        events.append((t, t2, " ".join(chunk)))
        t = t2
    return events


def write_ass(events, w, h, vertical, path):
    size = round(h * (0.045 if vertical else 0.06))
    margin_v = round(h * (0.30 if vertical else 0.08))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,{round(size * 0.12)},{round(size * 0.06)},2,{round(w * 0.08)},{round(w * 0.08)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for a, b, txt in events:
            txt = txt.replace("{", "(").replace("}", ")").upper()
            f.write(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{txt}\n")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    manifest_path = os.path.abspath(sys.argv[1])
    base = os.path.dirname(manifest_path)
    m = json.load(open(manifest_path, encoding="utf-8"))
    aspect = m.get("aspect", "16:9")
    if aspect not in SIZES:
        sys.exit(f"aspect must be one of {list(SIZES)}")
    w, h = SIZES[aspect]
    vertical = aspect == "9:16"
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    out = rel(m["out"])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        seg_list, aud_list, events, t = [], [], [], 0.0
        for i, beat in enumerate(m["beats"]):
            audio = rel(beat["audio"])
            dur = duration(audio) + BREATH
            seg = os.path.join(tmp, f"v{i:04d}.mp4")
            if beat.get("clip"):
                clip_segment(rel(beat["clip"]), dur, w, h, seg)
            else:
                still_segment(rel(beat["image"]), dur, w, h, MOVES[i % len(MOVES)], seg)
            # Pad each voice line with its breath so audio length == picture length.
            a = os.path.join(tmp, f"a{i:04d}.wav")
            run(["ffmpeg", "-y", "-v", "error", "-i", audio, "-af",
                 f"aresample=48000,apad=whole_dur={dur:.3f}", "-ac", "2", a])
            seg_list.append(seg)
            aud_list.append(a)
            if m.get("captions", True):
                events += caption_events(beat.get("text", ""), t, t + dur - BREATH,
                                         3 if vertical else 5)
            t += dur
            print(f"beat {i + 1}/{len(m['beats'])}: {dur:.2f}s", flush=True)

        for name, items in (("v.txt", seg_list), ("a.txt", aud_list)):
            with open(os.path.join(tmp, name), "w") as f:
                f.writelines(f"file '{p}'\n" for p in items)
        video = os.path.join(tmp, "video.mp4")
        voice = os.path.join(tmp, "voice.wav")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", os.path.join(tmp, "v.txt"), "-c", "copy", video])
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", os.path.join(tmp, "a.txt"), voice])

        inputs = ["-i", video, "-i", voice]
        if m.get("music"):
            vol = float(m.get("music_volume", 0.12))
            inputs += ["-stream_loop", "-1", "-i", rel(m["music"])]
            # Music ducks automatically whenever the narrator speaks.
            afilter = (f"[2:a]aresample=48000,volume={vol}[mu];"
                       f"[1:a]asplit[vo][key];"
                       f"[mu][key]sidechaincompress=threshold=0.05:ratio=6:release=400[duck];"
                       f"[vo][duck]amix=inputs=2:duration=first:normalize=0,"
                       f"loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        else:
            afilter = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"

        vfilter = "[0:v]null[vout]"
        if events:
            ass = os.path.join(tmp, "captions.ass")
            write_ass(events, w, h, vertical, ass)
            vfilter = f"[0:v]ass={ass}[vout]"

        run(["ffmpeg", "-y", "-v", "error", *inputs,
             "-filter_complex", f"{vfilter};{afilter}",
             "-map", "[vout]", "-map", "[aout]", "-t", f"{t:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out])
    print(f"done: {out} ({t:.1f}s, {w}x{h})")


if __name__ == "__main__":
    main()
