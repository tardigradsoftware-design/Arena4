#!/usr/bin/env python3
"""
Dikey (9:16)短视频 üretim hattı / Dikey (9:16) video üretim hattı.

Kullanım:
    python3 video/build_video.py video/scenes/ornek.json

Senaryo JSON'u (bkz. video/scenes/*.json):
{
  "slug": "dosya-adi",
  "baslik": "Hook üst etiketi",
  "vurgu": "sarı vurgulu kelimeler (hook)",
  "scenes": [
     {"img": "assets/img/s1.png", "vo": "assets/vo/vo1.mp3",
      "text": "ekranda görünecek satır(lar)",
      "num": null, "motion": "in|out|pan_l|pan_r"}
  ]
}
Çıktı: video/out/<slug>.mp4  (720x1280, 30fps, H.264 + AAC, ~1.2 Mbps)
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = subprocess.run(
    ["python3", "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
    capture_output=True, text=True).stdout.strip()

W, H, FPS = 720, 1280, 30
XFADE = 0.40          # sahneler arası geçiş
PAD = 0.75            # sahne sonunda nefes payı (sn)
VO_LEAD = 0.30        # sahne başında sesin girdiği an
FONT = "DejaVu Sans"
GOLD = "&H0033C7FF"   # ASS BGR -> amber/sarı
WHITE = "&H00FFFFFF"


def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"ffmpeg hata: {' '.join(args[:6])}...")
    return p.stdout


def audio_dur(path):
    out = subprocess.run([FF, "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def img_size(path):
    import struct
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    raise SystemExit("PNG bekleniyor: " + path)


def motion_filter(motion, d):
    """2x upscale + crop -> Ken Burns (zoompan). Yatay kayma için x ekseni."""
    frames = max(2, int(round(d * FPS)))
    if motion == "out":
        z = f"'1.14-0.14*on/{frames}'"
        x = "'iw/2-(iw/zoom/2)'"
    elif motion == "pan_l":
        z = "'1.10'"
        x = f"'iw/2-(iw/zoom/2)-(iw*0.04)*(on/{frames})'"
    elif motion == "pan_r":
        z = "'1.10'"
        x = f"'iw/2-(iw/zoom/2)+(iw*0.04)*(on/{frames})'"
    else:  # in
        z = f"'1.02+0.12*on/{frames}'"
        x = "'iw/2-(iw/zoom/2)'"
    y = "'ih/2-(ih/zoom/2)'"
    return (f"scale=1440:2560:force_original_aspect_ratio=increase,"
            f"crop=1440:2560,zoompan=z={z}:x={x}:y={y}:d={frames}:"
            f"s={W}x{H}:fps={FPS},format=yuv420p")


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def wrap(text, max_chars=22):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def build_ass(scenes, timeline, path, baslik):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},42,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,44,44,250,1
Style: Hook,{FONT},46,{GOLD},{GOLD},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,44,44,300,1
Style: Tag,{FONT},30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,4,0,8,40,40,64,1
Style: Num,{FONT},140,{GOLD},{GOLD},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,0,8,44,44,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    # üst etiket (tüm video)
    total = timeline[-1][1]
    ev.append(f"Dialogue: 0,{ass_time(0.2)},{ass_time(total)},{'Tag'},,0,0,0,,{{\\fad(300,300)}}{baslik}")
    for i, (sc, (start, end)) in enumerate(zip(scenes, timeline)):
        d = end - start
        is_hook = i == 0
        style = "Hook" if is_hook else "Cap"
        txt = "\\N".join(wrap(sc.get("text", ""), 20 if is_hook else 22))
        # hook kelimelerini sarı vurgula
        if is_hook and sc.get("vurgu"):
            for w in sc["vurgu"].split("|"):
                txt = txt.replace(w, "{\\c" + GOLD + "}" + w + "{\\c&H00FFFFFF&}")
        # metin sahnenin ortasında değil, sağnağın %15'inden sonra girsin
        t0 = start + min(0.35, d * 0.12)
        t1 = end - 0.10
        anim = "{\\fad(180,220)\\fscx92\\fscy92\\t(0,180,\\fscx100\\fscy100)}"
        ev.append(f"Dialogue: 1,{ass_time(t0)},{ass_time(t1)},{style},,0,0,0,,{anim}{txt}")
        if sc.get("num"):
            ev.append(f"Dialogue: 2,{ass_time(start + 0.10)},{ass_time(end)},{'Num'},,0,0,0,,"
                      f"{{\\fad(150,150)\\fscx80\\fscy80\\t(0,220,\\fscx100\\fscy100)}}{sc['num']}")
    # alt ilerleme çizgisi
    ev.append(f"Dialogue: 3,0,{ass_time(total)},Tag,,0,0,0,,{{\\an7\\pos(0,1272)\\p1\\c&H00FFFFFF&\\alpha&H50&}}"
              f"m 0 0 l {W} 0 l {W} 12 l 0 12")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(ev) + "\n")


def make_music(path, dur):
    """Çok hafif ambient pad + nabız. Numpy varsa sentezle, yoksa sessiz."""
    try:
        import numpy as np
    except ImportError:
        return None
    sr = 44100
    t = np.arange(int(sr * dur)) / sr
    sig = np.zeros_like(t)
    # Am - F - C - G, 4'er saniyelik döngü
    chords = [(110.0, 164.81, 220.0), (87.31, 130.81, 174.61),
              (130.81, 196.0, 261.63), (98.0, 146.83, 196.0)]
    for k, ch in enumerate(chords):
        start = int(sr * k * (dur / 4 if dur > 16 else 8))
        seg = t - start / sr
        env = np.clip(seg / 0.6, 0, 1) * np.exp(-np.clip(seg, 0, None) / 6.0)
        for f0 in ch:
            sig[start:start + len(seg)] += (0.030 * np.sin(2 * np.pi * f0 * seg)
                                           * env * (1 if len(seg) else 0))
    # nabız: her 0.6 sn'de yumuşak vuruş (4/4, 100bpm)
    beat = 0.6
    for b in np.arange(0, dur, beat):
        i = int(sr * b)
        n = min(int(sr * 0.18), len(sig) - i)
        if n <= 0:
            break
        k = np.arange(n) / sr
        sig[i:i + n] += 0.05 * np.sin(2 * np.pi * 60 * k) * np.exp(-k * 30)
    # lowpass benzeri yumuşatma
    kernel = np.ones(90) / 90
    sig = np.convolve(sig, kernel, mode="same")
    sig = np.clip(sig / max(1e-9, np.max(np.abs(sig))) * 0.5, -1, 1)
    stereo = np.stack([sig, sig], axis=1)
    pcm = (stereo * 32767).astype("<i2").tobytes()
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm)
    return path


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    slug = spec["slug"]
    scenes = spec["scenes"]
    outdir = os.path.join(ROOT, "video", "out")
    os.makedirs(outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="vbuild_")

    # süreler
    durs = []
    for sc in scenes:
        vo = os.path.join(ROOT, sc["vo"])
        durs.append(round(audio_dur(vo) + PAD, 2))
    timeline, cur = [], 0.0
    for i, d in enumerate(durs):
        start = cur - (XFADE * i)
        timeline.append((start, start + d))
        cur += d
    total = timeline[-1][1]

    # 1) sahneler (video only)
    clips = []
    for i, (sc, d) in enumerate(zip(scenes, durs)):
        img = os.path.join(ROOT, sc["img"])
        w, h = img_size(img)
        vf = motion_filter(sc.get("motion", "in"), d)
        # sahne karartma/aydınlatma dengesi
        vf += ",eq=contrast=1.04:saturation=1.06"
        out = os.path.join(tmp, f"c{i}.mp4")
        run([FF, "-y", "-loop", "1", "-i", img, "-t", f"{d:.2f}",
             "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
             "-crf", "18", "-pix_fmt", "yuv420p", out])
        clips.append(out)

    # 2) xfade zinciri
    n = len(clips)
    if n == 1:
        shutil.copy(clips[0], os.path.join(tmp, "v.mp4"))
    else:
        cmd = [FF, "-y"]
        for c in clips:
            cmd += ["-i", c]
        parts, prev = [], "[0:v]"
        for i in range(1, n):
            off = sum(durs[:i]) - XFADE * i
            lab = f"[x{i}]"
            parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XFADE}:offset={off:.3f}{lab}")
            prev = lab
        run(cmd + ["-filter_complex", ";".join(parts), "-map", prev,
                   "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                   "-pix_fmt", "yuv420p", "-an", os.path.join(tmp, "v.mp4")])

    # 3) altyazı katmanı
    ass = os.path.join(tmp, "sub.ass")
    build_ass(scenes, timeline, ass, spec.get("baslik", ""))
    vf_sub = f"ass={ass}:fontsdir=/usr/share/fonts/truetype/dejavu"
    run([FF, "-y", "-i", os.path.join(tmp, "v.mp4"), "-vf", vf_sub,
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", os.path.join(tmp, "v_sub.mp4")])

    # 4) ses: voiceover'ları timeline'a yerleştir + hafif müzik
    music = make_music(os.path.join(tmp, "music.wav"), total + 1)
    cmd = [FF, "-y", "-i", os.path.join(tmp, "v_sub.mp4")]
    filt, mixin = [], []
    for i, sc in enumerate(scenes):
        cmd += ["-i", os.path.join(ROOT, sc["vo"])]
        off = timeline[i][0] + VO_LEAD
        filt.append(f"[{i+1}:a]aresample=44100,adelay={int(off*1000)}|{int(off*1000)},"
                    f"volume=1.0[a{i}]")
        mixin.append(f"[a{i}]")
    if music:
        cmd += ["-i", music]
        mi = len(scenes) + 1
        filt.append(f"[{mi}:a]volume=0.10,afade=t=in:st=0:d=1.5[a{len(scenes)}]")
        mixin.append(f"[a{len(scenes)}]")
    filt.append("".join(mixin) + f"amix=inputs={len(mixin)}:normalize=0:dropout_transition=0,"
                "aformat=channel_layouts=stereo,"
                f"alimiter=limit=0.95,afade=t=out:st={total-1.2:.2f}:d=1.2[aout]")
    out = os.path.join(outdir, slug + ".mp4")
    run(cmd + ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[aout]",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
               "-shortest", "-movflags", "+faststart", out])
    shutil.rmtree(tmp, ignore_errors=True)
    print(out, round(total, 2), "sn")


if __name__ == "__main__":
    main()
