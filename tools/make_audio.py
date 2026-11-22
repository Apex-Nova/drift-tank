"""Drift Tank sound + music generator (a tiny synthesizer).

Every sound in the game is BUILT here from math: oscillators (square,
triangle, saw, sine), noise, envelopes, pitch sweeps and filters.
No samples, no internet, no AI credits — run it and it writes the files:

    .venv/bin/python tools/make_audio.py           # everything
    .venv/bin/python tools/make_audio.py sfx       # only sound effects
    .venv/bin/python tools/make_audio.py music     # only music

Output: part4_ui/assets/sounds/sfx_*.wav   (sound effects)
        part4_ui/assets/music/*.mp3        (9 retro tracks + victory jingle, needs ffmpeg)
Needs numpy + scipy (only for this tool — the game itself doesn't need them).

How a good explosion is made (and why the old one hurt):
  - NOT white noise turned up to the max: that is just a harsh hiss + distortion.
  - real booms are mostly LOW frequencies: a short crack at the start, a deep
    "thump" (a sine wave sliding down to ~35 Hz), a rumbling cloud of BROWN noise
    (noise with the highs removed) that slowly gets darker, and a few small
    debris ticks falling afterwards. All mixed quietly enough to leave headroom.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_DIR = os.path.join(ROOT, "part4_ui", "assets", "sounds")
MUSIC_DIR = os.path.join(ROOT, "part4_ui", "assets", "music")
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- building blocks
def n_of(seconds):
    return int(SR * seconds)


def t_axis(seconds):
    return np.arange(n_of(seconds)) / SR


def osc(kind, freq, seconds, duty=0.5):
    n = n_of(seconds)
    f = np.full(n, float(freq)) if np.ndim(freq) == 0 else np.asarray(freq, dtype=float)[:n]
    ph = 2 * np.pi * np.cumsum(f) / SR
    cyc = (ph / (2 * np.pi)) % 1.0
    if kind == "sine":
        return np.sin(ph)
    if kind == "square":
        return np.where(cyc < duty, 1.0, -1.0)
    if kind == "triangle":
        return 4 * np.abs(cyc - 0.5) - 1
    if kind == "saw":
        return 2 * cyc - 1
    raise ValueError(kind)


def noise(seconds):
    return rng.uniform(-1, 1, n_of(seconds))


def brown(seconds):
    """Brown noise: deep rumbling noise (each sample wanders from the last)."""
    x = np.cumsum(rng.normal(0, 1, n_of(seconds)))
    x -= np.convolve(x, np.ones(2000) / 2000, mode="same")      # remove slow drift
    return x / (np.max(np.abs(x)) or 1)


def sweep(f0, f1, seconds, curve=1.0):
    k = np.linspace(0, 1, n_of(seconds)) ** curve
    return f0 + (f1 - f0) * k


def env(seconds, attack=0.005, decay=0.1, sustain=0.0, release=0.05, hold=0.0):
    n = n_of(seconds)
    e = np.zeros(n)
    a, d, h, r = n_of(attack), n_of(decay), n_of(hold), n_of(release)
    i = 0
    seg = min(a, n); e[i:i + seg] = np.linspace(0, 1, seg, endpoint=False); i += seg
    seg = min(h, n - i); e[i:i + seg] = 1; i += seg
    seg = min(d, n - i); e[i:i + seg] = np.linspace(1, sustain, seg, endpoint=False); i += seg
    rest = n - i
    if rest > 0:
        tail = max(0, rest - r)
        e[i:i + tail] = sustain
        e[i + tail:] = np.linspace(sustain, 0, rest - tail)
    return e


def decay(seconds, rate, attack=0.003):
    e = np.exp(-t_axis(seconds) * rate)
    a = n_of(attack)
    if a:
        e[:a] *= np.linspace(0, 1, a)
    return e


def lowpass(x, cutoff, order=2):
    return sosfilt(butter(order, min(cutoff, SR / 2 - 100), "low", fs=SR, output="sos"), x)


def highpass(x, cutoff, order=2):
    return sosfilt(butter(order, cutoff, "high", fs=SR, output="sos"), x)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def moving_lowpass(x, f_start, f_end, blocks=40):
    """A low-pass whose cutoff glides from f_start to f_end (the sound gets darker)."""
    out = np.zeros_like(x)
    edges = np.linspace(0, len(x), blocks + 1).astype(int)
    for k in range(blocks):
        f = f_start * (f_end / f_start) ** (k / max(1, blocks - 1))
        a, b = edges[k], edges[k + 1]
        lo = max(0, a - 2048)                               # overlap so blocks join smoothly
        out[a:b] = lowpass(x[lo:b], f)[a - lo:]
    return out


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def delay(x, seconds):
    return np.concatenate([np.zeros(n_of(seconds)), x])


def echo(x, time=0.11, feedback=0.3, taps=3):
    out = np.concatenate([x, np.zeros(n_of(time * taps))])
    d = n_of(time)
    for k in range(1, taps + 1):
        out[d * k:d * k + len(x)] += x * feedback ** k
    return out


def soft_limit(x, ceiling=0.95):
    """Gentle limiter: below the ceiling barely anything changes, above it the peaks are rounded off."""
    return np.tanh(x / ceiling) * ceiling


def normalize(x, peak):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def fade_edges(x, ms=4):
    n = n_of(ms / 1000)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def write_wav(path, x):
    data = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


def note_hz(n):
    """MIDI note number -> frequency (69 = A4 = 440 Hz)."""
    return 440.0 * 2 ** ((n - 69) / 12)


# ---------------------------------------------------------------- sound effects
def explosion(size=1.0):
    """size 1 = tank/crate blast, ~1.6 = big rocket blast."""
    d = 1.1 * size
    crack = highpass(noise(0.03), 1500) * decay(0.03, 160, 0.0005) * 0.5          # the first sharp "k"
    thump = osc("sine", sweep(95 / size, 34, 0.5 * size, 0.35), 0.5 * size) * decay(0.5 * size, 7 / size, 0.004)
    body = moving_lowpass(brown(d), 2400 / size, 120) * decay(d, 3.6 / size, 0.006)
    hiss = moving_lowpass(noise(d * 0.6), 5000, 700) * decay(d * 0.6, 9) * 0.18      # air rushing
    debris = np.zeros(n_of(d + 0.6))
    for _ in range(int(7 * size)):                                                     # small bits landing
        t = rng.uniform(0.25, d)
        tick = bandpass(noise(0.03), 1200, 4000) * decay(0.03, 120, 0.0005) * rng.uniform(0.05, 0.14)
        i = n_of(t)
        debris[i:i + len(tick)] += tick[:len(debris) - i]
    out = mix(crack, thump * 0.9, body * 0.85, hiss, debris)
    return soft_limit(out * 0.9)


def sfx():
    s = {}
    d = 0.11     # machine gun: short punchy "pew" + a tiny click (not a harsh square)
    s["shot_small"] = mix(lowpass(osc("square", sweep(720, 240, d, 0.5), d, 0.3), 3000) * decay(d, 30) * 0.5,
                          bandpass(noise(0.025), 1500, 6000) * decay(0.025, 140) * 0.35,
                          osc("sine", sweep(180, 70, 0.07), 0.07) * decay(0.07, 40) * 0.5)
    d = 0.5      # cannon: deep boom with a crack
    s["shot_cannon"] = mix(osc("sine", sweep(140, 40, d, 0.4), d) * decay(d, 9, 0.002),
                           moving_lowpass(brown(d), 3000, 250) * decay(d, 12) * 0.7,
                           highpass(noise(0.02), 2000) * decay(0.02, 150) * 0.3)
    d = 0.4      # scatter gun: wide puff of noise
    s["shot_shotgun"] = mix(moving_lowpass(noise(d), 4500, 500) * decay(d, 13) * 0.6,
                            osc("sine", sweep(120, 45, d), d) * decay(d, 13) * 0.7)
    d = 0.8      # rocket launch: whoosh rising + low rumble
    s["shot_rocket"] = mix(moving_lowpass(noise(d), 400, 3500) * env(d, 0.06, 0.6, 0.2, 0.2) * 0.6,
                           lowpass(osc("saw", sweep(55, 85, d), d), 400) * env(d, 0.02, 0.5) * 0.4)
    d = 0.5      # railgun: zap falling + bright ring
    zap = lowpass(osc("saw", sweep(2200, 160, d, 0.4), d), 4000)
    s["shot_rail"] = echo(mix(zap * decay(d, 6) * 0.6, osc("sine", sweep(2800, 1200, d), d) * decay(d, 9) * 0.3), 0.06, 0.25)
    d = 0.3      # bouncer: springy boing
    wobble = 420 + 90 * np.sin(2 * np.pi * 18 * t_axis(d))
    s["shot_bouncer"] = osc("triangle", wobble * np.linspace(1.2, 0.7, n_of(d)), d) * decay(d, 9) * 0.7
    s["explosion"] = explosion(1.0)
    s["big_explosion"] = mix(explosion(1.6), delay(explosion(0.8) * 0.45, 0.18))
    d = 0.22     # metal hit: "tink" (inharmonic partials, short)
    s["hit"] = mix(*[osc("sine", f, d) * decay(d, r, 0.001) * a for f, r, a in
                     ((620, 20, 0.5), (1390, 26, 0.3), (2470, 34, 0.2))],
                   bandpass(noise(0.015), 2000, 7000) * decay(0.015, 200) * 0.3)
    pick = []    # pickup: quick upward arpeggio
    for i, n in enumerate((72, 76, 79, 84)):
        pick.append(delay(lowpass(osc("square", note_hz(n), 0.12, 0.25), 5000) * env(0.12, 0.002, 0.1), 0.055 * i))
    s["pickup"] = echo(mix(*pick) * 0.6, 0.09, 0.25, 2)
    heal = []    # heal: soft shimmering major chord
    for i, n in enumerate((67, 71, 74, 79)):
        heal.append(delay(osc("triangle", note_hz(n), 0.5) * env(0.5, 0.01, 0.45), 0.06 * i))
    s["heal"] = echo(mix(*heal) * 0.5, 0.12, 0.3, 2)
    d = 0.5      # spawn: rising shimmer
    s["spawn"] = mix(osc("sine", sweep(200, 1200, d, 1.5), d) * env(d, 0.05, 0.4, 0, 0.05),
                     osc("sine", sweep(400, 2400, d, 1.5), d) * env(d, 0.05, 0.4) * 0.3) * 0.6
    s["empty"] = mix(lowpass(osc("square", 150, 0.04), 1500) * env(0.04, 0.001, 0.035),
                     delay(lowpass(osc("square", 115, 0.04), 1500) * env(0.04, 0.001, 0.035), 0.07)) * 0.5
    d = 0.3      # crate lands: soft wooden thud
    s["crate_drop"] = mix(osc("sine", sweep(110, 55, d), d) * decay(d, 16, 0.002) * 0.7,
                          lowpass(brown(d), 900) * decay(d, 20) * 0.5,
                          delay(bandpass(noise(0.05), 600, 2500) * decay(0.05, 60) * 0.15, 0.06))
    s["break"] = mix(*[delay(bandpass(noise(0.08), 300, 2500) * decay(0.08, 45, 0.001) * a, k)
                       for k, a in ((0, 0.6), (0.04, 0.45), (0.09, 0.35), (0.15, 0.25))])
    s["countdown"] = lowpass(osc("square", 660, 0.16), 4000) * env(0.16, 0.002, 0.14) * 0.45
    s["go"] = echo(mix(lowpass(osc("square", note_hz(84), 0.4), 5000) * env(0.4, 0.002, 0.35),
                       lowpass(osc("square", note_hz(79), 0.4, 0.25), 5000) * env(0.4, 0.002, 0.35) * 0.6) * 0.5, 0.1, 0.3, 2)
    s["click"] = lowpass(osc("square", 1100, 0.03), 4000) * env(0.03, 0.001, 0.025) * 0.4
    s["select"] = osc("triangle", 880, 0.05) * env(0.05, 0.001, 0.045) * 0.45
    s["confirm"] = mix(lowpass(osc("square", note_hz(76), 0.08, 0.25), 5000) * env(0.08, 0.001, 0.07),
                       delay(lowpass(osc("square", note_hz(83), 0.14, 0.25), 5000) * env(0.14, 0.001, 0.12), 0.07)) * 0.5
    s["switch"] = osc("triangle", sweep(500, 900, 0.07), 0.07) * env(0.07, 0.001, 0.06) * 0.5
    d = 0.7      # zone warning: two-tone alarm
    tone = np.where((t_axis(d) * 6).astype(int) % 2 == 0, 740, 520)
    s["zone_warning"] = lowpass(osc("square", tone, d, 0.4), 3000) * env(d, 0.01, 0.1, 0.8, 0.1) * 0.4
    d = 0.18     # zone tick damage: low buzz
    s["zone_hurt"] = lowpass(osc("saw", 90, d), 700) * decay(d, 18) * 0.6

    # Every effect is made with headroom: loud ones peak at ~0.7, small UI blips lower.
    # Several sounds playing together then add up without crackling.
    loud = {"explosion": 0.72, "big_explosion": 0.8, "shot_cannon": 0.65, "shot_rocket": 0.6}
    for name, x in s.items():
        x = fade_edges(normalize(x, loud.get(name, 0.55)))
        write_wav(os.path.join(SFX_DIR, "sfx_%s.wav" % name), x)
    print("sfx:", len(s))


# ---------------------------------------------------------------- music
SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "dorian": [0, 2, 3, 5, 7, 9, 10],
          "major": [0, 2, 4, 5, 7, 9, 11], "phrygian": [0, 1, 3, 5, 7, 8, 10],
          "mixolydian": [0, 2, 4, 5, 7, 9, 10], "harmonic": [0, 2, 3, 5, 7, 8, 11]}


def kick(seconds=0.28):
    return osc("sine", sweep(160, 45, seconds, 0.35), seconds) * decay(seconds, 13, 0.001)


def snare(seconds=0.2):
    return mix(bandpass(noise(seconds), 1200, 8000) * decay(seconds, 20, 0.001) * 0.6,
               osc("triangle", 185, seconds) * decay(seconds, 28) * 0.45)


def hat(open_=False):
    d = 0.18 if open_ else 0.05
    return highpass(noise(d), 7000) * decay(d, 18 if open_ else 80, 0.0005) * 0.3


def place(track, sound, start, gain=1.0):
    i = n_of(start)
    end = min(len(track), i + len(sound))
    if 0 <= i < len(track):
        track[i:end] += sound[:end - i] * gain


def scale_note(root, scale, degree):
    s = SCALES[scale]
    return root + s[degree % 7] + 12 * (degree // 7)


def triad(root, scale, degree):
    return [scale_note(root, scale, degree + k) for k in (0, 2, 4)]


def make_motif(seed, length=8, rest=0.25, leap=2):
    """A short random melody shape (scale steps); repeated and varied it becomes the tune."""
    r = np.random.default_rng(seed)
    deg, motif = 0, []
    for k in range(length):
        if k and r.random() < rest:
            motif.append(None)
            continue
        deg = int(np.clip(deg + r.integers(-leap, leap + 1), -3, 9))
        motif.append(deg)
    if motif[0] is None:
        motif[0] = 0
    return motif


def song(bpm, root, scale, chords, seed, style):
    """A full retro track: intro, theme A, theme A', bridge B, breakdown, theme A, ending.

    style picks the instruments and drum groove:
      "drive"  fast 8th-note bass, backbeat      "march"  four-on-the-floor, punchy
      "funk"   syncopated bass + offbeat hats    "wave"   saw pads, dreamy (synthwave)
      "calm"   soft menu groove                  "boss"   heavy, dark, double kicks
    """
    r = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = 4 * beat
    sections = [("intro", 4), ("A", 8), ("A2", 8), ("B", 8), ("break", 4), ("A", 8), ("end", 2)]
    total_bars = sum(n for _, n in sections)
    n = n_of(total_bars * bar + 1.5)
    drums, bass, arp, lead, pad = (np.zeros(n) for _ in range(5))
    motif_a = make_motif(seed, 8)
    motif_b = make_motif(seed + 100, 8, rest=0.15, leap=3)
    lead_duty = float(r.choice([0.125, 0.25, 0.5]))
    bar_i = 0
    for section, count in sections:
        for local in range(count):
            t0 = bar_i * bar
            prog = chords if section != "B" else chords[2:] + chords[:2]
            degree = prog[local % len(prog)]
            chord = triad(root, scale, degree)
            # ---------------- drums
            if section != "break" or local >= count - 1:
                for b in range(4):
                    tb = t0 + b * beat
                    if style in ("march", "boss"):
                        place(drums, kick(), tb, 0.9)
                        if style == "boss" and b in (1, 3):
                            place(drums, kick(), tb + beat / 2, 0.6)
                    elif style == "funk":
                        if b == 0 or (b == 2 and local % 2 == 0):
                            place(drums, kick(), tb, 0.9)
                        if b == 2:
                            place(drums, kick(), tb + beat * 0.75, 0.5)
                    elif style == "calm":
                        if b == 0 or (b == 2 and local % 2):
                            place(drums, kick(), tb, 0.6)
                    elif b in (0, 2):
                        place(drums, kick(), tb, 0.9)
                    if b in (1, 3) and section != "intro":
                        place(drums, snare(), tb, 0.45 if style == "calm" else 0.75)
                    for e in range(2):
                        place(drums, hat(style == "funk" and e == 1), tb + e * beat / 2, 0.5 if style == "calm" else 0.75)
                if local == count - 1 and section in ("A", "A2", "B") and style != "calm":
                    for k in range(4):                                     # drum fill
                        place(drums, snare(0.12), t0 + 3 * beat + k * beat / 4, 0.4 + 0.12 * k)
            # ---------------- bass
            low = chord[0] - 12 if chord[0] - 12 >= 33 else chord[0]
            if style in ("drive", "boss", "march"):
                steps = [(k * beat / 2, low + (12 if k % 2 and style == "drive" else 0)) for k in range(8)]
            elif style == "funk":
                steps = [(0, low), (beat * 0.75, low + 12), (beat * 1.5, low), (beat * 2.5, low + 7),
                         (beat * 3, low + 12), (beat * 3.5, low + 10)]
            else:
                steps = [(0, low), (beat * 2, low + 7)]
            for k, (off, note) in enumerate(steps):
                dur = (steps[k + 1][0] if k + 1 < len(steps) else bar) - off
                tone = osc("triangle", note_hz(note), dur * 0.92) * env(dur * 0.92, 0.003, dur * 0.4, 0.7, 0.03)
                place(bass, tone, t0 + off, 0.95)
            # ---------------- pad (wave / calm / boss): a soft held chord, two detuned saws
            if style in ("wave", "calm", "boss") and section != "intro":
                for note in chord:
                    tone = osc("saw", note_hz(note) * 1.003, bar) + osc("saw", note_hz(note) * 0.997, bar)
                    place(pad, tone * env(bar, 0.25, 0.2, 0.7, 0.3), t0, 0.12)
            # ---------------- arpeggio (16ths through the chord)
            if section != "intro":
                for k in range(16):
                    note = chord[k % 3] + 12 * ((k // 3) % 2) + 12
                    dur = beat / 4
                    tone = osc("square", note_hz(note), dur * 0.85, 0.125) * env(dur * 0.85, 0.002, dur * 0.5, 0.25, 0.01)
                    place(arp, tone, t0 + k * dur, 0.22 if section != "break" else 0.3)
            # ---------------- lead melody
            if section in ("A", "A2", "B", "end"):
                motif = motif_b if section == "B" else motif_a
                shift = degree if section == "B" else (2 if (section == "A2" and local % 4 >= 2) else 0)
                step = bar / len(motif)
                for k, deg in enumerate(motif):
                    if deg is None or (section == "end" and k > 0):
                        continue
                    note = scale_note(root + 12, scale, deg + shift)
                    length = step * (2 if k + 1 < len(motif) and motif[k + 1] is None else 1) * 0.92
                    if section == "end":
                        length = bar * 1.5
                    vib = note_hz(note) * (1 + 0.005 * np.sin(2 * np.pi * 5.5 * t_axis(length)) * np.linspace(0, 1, n_of(length)))
                    tone = osc("square", vib, length, lead_duty) * env(length, 0.004, length * 0.35, 0.55, 0.04)
                    place(lead, tone, t0 + k * step, 0.36)
            bar_i += 1
    lead = echo(lowpass(lead, 4200), beat * 0.75, 0.22, 2)[:n]
    out = drums * 0.85 + lowpass(bass, 2500) * 0.75 + lowpass(arp, 5500) + lead + lowpass(pad, 1800)
    out = soft_limit(normalize(out, 1.0) * 0.9, 0.9)
    return fade_edges(out, 40)


# name, bpm, root note, scale, chord degrees, melody seed, style
TRACKS = [
    ("menu_1", 92, 57, "minor", [0, 5, 2, 6], 11, "calm"),          # the old menu mood (A minor)
    ("menu_2", 84, 60, "major", [0, 4, 5, 3], 12, "wave"),          # sunny synthwave
    ("menu_3", 100, 62, "dorian", [0, 3, 0, 6], 13, "calm"),        # laid-back dorian groove
    ("battle_1", 140, 50, "minor", [0, 5, 2, 6], 21, "drive"),      # the old battle mood (D minor)
    ("battle_2", 156, 52, "phrygian", [0, 1, 0, 6], 22, "boss"),    # dark & heavy
    ("battle_3", 128, 55, "dorian", [0, 3, 4, 3], 23, "funk"),      # funky
    ("battle_4", 148, 53, "minor", [0, 3, 4, 4], 24, "march"),      # marching
    ("battle_5", 118, 57, "harmonic", [0, 5, 3, 4], 25, "wave"),    # synthwave chase
    ("battle_6", 164, 48, "mixolydian", [0, 6, 3, 0], 26, "drive"), # fast & happy
]


def write_mp3(name, x):
    tmp = os.path.join(MUSIC_DIR, name + ".tmp.wav")
    write_wav(tmp, x)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-c:a", "libmp3lame", "-q:a", "5",
                    os.path.join(MUSIC_DIR, name + ".mp3")], check=True)
    os.remove(tmp)


def music():
    os.makedirs(MUSIC_DIR, exist_ok=True)
    for old in os.listdir(MUSIC_DIR):                     # old single-track .wav files
        if old.endswith(".wav"):
            os.remove(os.path.join(MUSIC_DIR, old))
    for name, bpm, root, scale, chords, seed, style in TRACKS:
        x = song(bpm, root, scale, chords, seed, style)
        write_mp3(name, x)
        print("music: %-9s %3d bpm %-10s %-6s %4.0fs" % (name, bpm, scale, style, len(x) / SR))
    parts = []                                            # victory jingle
    for i, nte in enumerate((72, 76, 79, 84, 79, 84)):
        dur = 0.16 if i < 5 else 0.9
        parts.append(delay(lowpass(osc("square", note_hz(nte), dur, 0.25), 5000) * env(dur, 0.003, dur * 0.7, 0.3, 0.1), 0.16 * i))
    write_mp3("victory", fade_edges(normalize(echo(mix(*parts), 0.12, 0.3, 3), 0.8)))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "sfx"):
        sfx()
    if what in ("all", "music"):
        music()
