"""Drift Tank sound + music generator (a tiny synthesizer).

Every sound in the game is BUILT here from math: oscillators (square,
triangle, saw, sine), noise, envelopes, pitch sweeps and simple filters.
No samples, no internet, no AI credits — run it and it writes .wav files:

    .venv/bin/python tools/make_audio.py

Output: part4_ui/assets/sounds/sfx_*.wav  and  part4_ui/assets/music/*.wav
(needs numpy, only for this tool — the game itself doesn't need it)
"""
import os
import wave

import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_DIR = os.path.join(ROOT, "part4_ui", "assets", "sounds")
MUSIC_DIR = os.path.join(ROOT, "part4_ui", "assets", "music")
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- building blocks
def t_axis(seconds):
    return np.arange(int(SR * seconds)) / SR


def phase_from_freq(freq):
    """Integrate a (possibly changing) frequency into a phase, so sweeps sound smooth."""
    return 2 * np.pi * np.cumsum(freq) / SR


def osc(kind, freq, seconds, duty=0.5):
    n = int(SR * seconds)
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,)) if np.ndim(freq) == 0 else np.asarray(freq, dtype=float)[:n]
    ph = phase_from_freq(f)
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
    return rng.uniform(-1, 1, int(SR * seconds))


def sweep(f0, f1, seconds, curve=1.0):
    k = np.linspace(0, 1, int(SR * seconds)) ** curve
    return f0 + (f1 - f0) * k


def env(seconds, attack=0.005, decay=0.1, sustain=0.0, release=0.05, hold=0.0):
    n = int(SR * seconds)
    e = np.zeros(n)
    a, d, h = int(SR * attack), int(SR * decay), int(SR * hold)
    r = int(SR * release)
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


def exp_decay(seconds, rate):
    return np.exp(-t_axis(seconds) * rate)


def lowpass(x, cutoff):
    """One-pole low-pass filter (cutoff can change over time)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    alpha = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def drive(x, amount=2.0):
    return np.tanh(x * amount) / np.tanh(amount)


def echo(x, delay=0.11, feedback=0.3, taps=3):
    out = np.concatenate([x, np.zeros(int(SR * delay * taps))])
    d = int(SR * delay)
    for k in range(1, taps + 1):
        out[d * k:d * k + len(x)] += x * (feedback ** k)
    return out


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def normalize(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def fade_edges(x, ms=4):
    n = int(SR * ms / 1000)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def save(path, x, peak=0.9):
    x = fade_edges(normalize(x, peak))
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
def sfx():
    s = {}
    d = 0.09     # machine gun: bright square blip that drops in pitch + a noise click
    s["shot_small"] = mix(osc("square", sweep(900, 260, d, 0.6), d, 0.25) * env(d, 0.001, 0.08) * 0.6,
                          highpass(noise(0.03), 2000) * env(0.03, 0.001, 0.03) * 0.8)
    d = 0.45     # cannon: deep thump + crunchy noise
    s["shot_cannon"] = mix(osc("sine", sweep(160, 38, d, 0.5), d) * exp_decay(d, 9),
                           drive(lowpass(noise(d), sweep(3000, 200, d)) * exp_decay(d, 14), 3) * 0.7)
    d = 0.35     # scatter gun: wide noise blast
    s["shot_shotgun"] = mix(lowpass(noise(d), sweep(6000, 400, d, 0.5)) * exp_decay(d, 11),
                            osc("sine", sweep(110, 45, d), d) * exp_decay(d, 12) * 0.8)
    d = 0.8      # rocket: rising whoosh + rumble
    s["shot_rocket"] = mix(lowpass(noise(d), sweep(300, 4500, d, 0.7)) * env(d, 0.05, 0.6, 0.2, 0.2),
                           osc("saw", sweep(55, 90, d), d) * env(d, 0.02, 0.5, 0.0) * 0.35)
    d = 0.5      # railgun: zappy falling saw + ring
    zap = osc("saw", sweep(2400, 180, d, 0.4), d) * osc("sine", 70, d)
    s["shot_rail"] = echo(mix(zap * exp_decay(d, 6) * 0.8, osc("sine", sweep(3000, 1200, d), d) * exp_decay(d, 9) * 0.4), 0.06, 0.25)
    d = 0.3      # bouncer: springy boing
    vib = 420 + 120 * np.sin(2 * np.pi * 22 * t_axis(d))
    s["shot_bouncer"] = osc("triangle", vib * np.linspace(1.2, 0.7, int(SR * d)), d) * exp_decay(d, 9)
    d = 1.0      # explosion
    body = lowpass(noise(d), sweep(5000, 120, d, 0.5)) * exp_decay(d, 4.5)
    s["explosion"] = drive(mix(body, osc("sine", sweep(90, 30, d), d) * exp_decay(d, 6) * 0.9), 2)
    d = 1.8      # big explosion: longer, deeper, with debris crackle
    body = lowpass(noise(d), sweep(4000, 80, d, 0.4)) * exp_decay(d, 2.6)
    crackle = highpass(noise(d), 3000) * (rng.random(int(SR * d)) > 0.995) * exp_decay(d, 3) * 3
    s["big_explosion"] = drive(mix(body, osc("sine", sweep(70, 24, d), d) * exp_decay(d, 3) * 1.1, crackle), 2.2)
    d = 0.25     # metal hit: inharmonic partials
    s["hit"] = mix(*[osc("sine", f, d) * exp_decay(d, r) * a for f, r, a in
                     ((523, 18, 0.6), (1187, 24, 0.4), (2210, 30, 0.3), (3301, 40, 0.2))],
                   highpass(noise(0.02), 1500) * 0.6)
    pick = []    # pickup: quick upward arpeggio
    for i, n in enumerate((72, 76, 79, 84)):
        pick.append(np.concatenate([np.zeros(int(SR * 0.055 * i)), osc("square", note_hz(n), 0.12, 0.25) * env(0.12, 0.002, 0.1)]))
    s["pickup"] = echo(mix(*pick), 0.09, 0.25, 2)
    heal = []    # heal: soft shimmering major chord
    for i, n in enumerate((67, 71, 74, 79)):
        heal.append(np.concatenate([np.zeros(int(SR * 0.06 * i)), osc("triangle", note_hz(n), 0.5) * env(0.5, 0.01, 0.45)]))
    s["heal"] = echo(mix(*heal), 0.12, 0.3, 2)
    d = 0.5      # spawn: rising sine sweep
    s["spawn"] = osc("sine", sweep(200, 1200, d, 1.5), d) * env(d, 0.05, 0.4, 0, 0.05) + \
        osc("sine", sweep(400, 2400, d, 1.5), d) * env(d, 0.05, 0.4) * 0.3
    s["empty"] = mix(osc("square", 140, 0.04, 0.5) * env(0.04, 0.001, 0.035),
                     np.concatenate([np.zeros(int(SR * 0.07)), osc("square", 110, 0.04, 0.5) * env(0.04, 0.001, 0.035)]))
    d = 0.35     # crate lands: thud + rattle
    s["crate_drop"] = mix(osc("sine", sweep(120, 50, d), d) * exp_decay(d, 14),
                          lowpass(noise(d), 1500) * exp_decay(d, 18) * 0.8,
                          highpass(noise(d), 2500) * (np.sin(2 * np.pi * 30 * t_axis(d)) > 0.6) * exp_decay(d, 10) * 0.3)
    d = 0.3      # wood / concrete breaking
    s["break"] = mix(*[np.concatenate([np.zeros(int(SR * k)), lowpass(noise(0.08), 2500) * exp_decay(0.08, 40)])
                       for k in (0, 0.04, 0.09, 0.15)])
    s["countdown"] = osc("square", 660, 0.16, 0.5) * env(0.16, 0.002, 0.14) * 0.6
    s["go"] = echo(mix(osc("square", note_hz(84), 0.4, 0.5) * env(0.4, 0.002, 0.35),
                       osc("square", note_hz(79), 0.4, 0.25) * env(0.4, 0.002, 0.35) * 0.6), 0.1, 0.3, 2)
    s["click"] = osc("square", 1200, 0.03, 0.5) * env(0.03, 0.001, 0.025) * 0.5
    s["select"] = osc("triangle", 880, 0.05) * env(0.05, 0.001, 0.045) * 0.5
    s["confirm"] = mix(osc("square", note_hz(76), 0.08, 0.25) * env(0.08, 0.001, 0.07),
                       np.concatenate([np.zeros(int(SR * 0.07)), osc("square", note_hz(83), 0.14, 0.25) * env(0.14, 0.001, 0.12)]))
    s["switch"] = osc("triangle", sweep(500, 900, 0.07), 0.07) * env(0.07, 0.001, 0.06) * 0.6
    d = 0.7      # zone warning: two-tone alarm
    tone = np.where((t_axis(d) * 6).astype(int) % 2 == 0, 740, 520)
    s["zone_warning"] = osc("square", tone, d, 0.4) * env(d, 0.01, 0.1, 0.8, 0.1) * 0.5
    d = 0.18     # zone tick damage
    s["zone_hurt"] = lowpass(osc("saw", 90, d), 900) * exp_decay(d, 18)
    for name, x in s.items():
        save(os.path.join(SFX_DIR, "sfx_%s.wav" % name), x, 0.85)
    print("sfx:", len(s))


# ---------------------------------------------------------------- music
def kick(seconds=0.25):
    return osc("sine", sweep(150, 42, seconds, 0.4), seconds) * exp_decay(seconds, 14)


def snare(seconds=0.2):
    return mix(highpass(noise(seconds), 1200) * exp_decay(seconds, 18) * 0.7, osc("triangle", 190, seconds) * exp_decay(seconds, 25) * 0.5)


def hat(seconds=0.05, open_=False):
    return highpass(noise(seconds), 6000) * exp_decay(seconds, 30 if open_ else 80) * 0.35


def place(track, sound, start, gain=1.0):
    i = int(start * SR)
    end = min(len(track), i + len(sound))
    if i < len(track):
        track[i:end] += sound[:end - i] * gain


def song(bpm, bars, chords, scale_root, lead_pattern, style):
    """A 4/4 chiptune loop: drums + bass + arpeggio + lead melody."""
    beat = 60 / bpm
    length = bars * 4 * beat
    n = int(length * SR)
    drums, bass, arp, lead = (np.zeros(n) for _ in range(4))
    for bar in range(bars):
        chord = chords[bar % len(chords)]          # list of MIDI notes
        t0 = bar * 4 * beat
        # drums
        for b in range(4):
            if style == "battle":
                place(drums, kick(), t0 + b * beat, 0.9 if b in (0, 2) else 0.0)
                if b in (1, 3):
                    place(drums, snare(), t0 + b * beat, 0.8)
                for e in range(2):
                    place(drums, hat(open_=(e == 1 and b == 3)), t0 + b * beat + e * beat / 2, 0.8)
                if bar % 4 == 3 and b == 3:        # fill
                    for k in range(4):
                        place(drums, snare(0.12), t0 + b * beat + k * beat / 4, 0.5 + 0.1 * k)
            else:
                if b == 0 or (b == 2 and bar % 2):
                    place(drums, kick(), t0 + b * beat, 0.7)
                if b == 2:
                    place(drums, snare(), t0 + b * beat, 0.45)
                place(drums, hat(), t0 + b * beat + beat / 2, 0.6)
        # bass: root on 8th notes (battle) or half notes (menu)
        root = chord[0] - 12
        steps = 8 if style == "battle" else 2
        for k in range(steps):
            dur = 4 * beat / steps
            note = root + (12 if style == "battle" and k % 2 else 0)
            tone = osc("triangle", note_hz(note), dur * 0.95) * env(dur * 0.95, 0.003, dur * 0.5, 0.6, 0.03)
            place(bass, tone, t0 + k * dur, 0.9)
        # arpeggio: 16th notes through the chord
        for k in range(16):
            dur = beat / 4
            note = chord[k % len(chord)] + (12 if (k // len(chord)) % 2 else 0)
            tone = osc("square", note_hz(note), dur * 0.9, 0.125) * env(dur * 0.9, 0.002, dur * 0.6, 0.2, 0.01)
            place(arp, tone, t0 + k * dur, 0.35 if style == "battle" else 0.25)
        # lead melody (scale degrees -> notes, None = rest)
        pattern = lead_pattern[bar % len(lead_pattern)]
        step = 4 * beat / len(pattern)
        for k, deg in enumerate(pattern):
            if deg is None:
                continue
            note = scale_root + deg
            dur = step * 0.92
            vib = note_hz(note) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t_axis(dur)))
            tone = osc("square", vib, dur, 0.5) * env(dur, 0.005, dur * 0.4, 0.55, 0.03)
            place(lead, tone, t0 + k * step, 0.38)
    lead = lowpass(lead, 3500)
    arp = lowpass(arp, 5000)
    out = drums * 0.9 + bass * 0.8 + arp + lead
    return normalize(out, 0.85)


def music():
    # A minor, relaxed: Am - F - C - G
    am, f, c, g = [57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]
    menu_lead = [[0, None, 3, None, 7, None, 5, 3], [0, None, None, 8, 7, None, 5, None],
                 [3, None, 5, None, 7, None, 10, 12], [10, None, 7, None, 5, None, 3, 2]]
    menu = song(96, 16, [am, f, c, g], 69, menu_lead, "menu")
    save(os.path.join(MUSIC_DIR, "menu.wav"), menu, 0.8)
    # D minor, driving: Dm - Bb - F - C, faster
    dm, bb, ff, cc = [50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]
    battle_lead = [[0, 0, 3, 5, 7, None, 5, 3], [10, None, 8, 7, 5, None, 3, None],
                   [0, 3, 7, 10, 12, None, 10, 7], [8, 7, 5, 3, 2, None, 0, None]]
    battle = song(140, 32, [dm, bb, ff, cc], 62, battle_lead, "battle")
    save(os.path.join(MUSIC_DIR, "battle.wav"), battle, 0.8)
    # victory jingle
    parts = []
    for i, nte in enumerate((72, 76, 79, 84, 79, 84)):
        dur = 0.16 if i < 5 else 0.9
        parts.append(np.concatenate([np.zeros(int(SR * 0.16 * i)),
                                     osc("square", note_hz(nte), dur, 0.25) * env(dur, 0.003, dur * 0.7, 0.3, 0.1)]))
    save(os.path.join(MUSIC_DIR, "victory.wav"), echo(mix(*parts), 0.12, 0.3, 3), 0.8)
    print("music: menu %.0fs, battle %.0fs" % (len(menu) / SR, len(battle) / SR))


if __name__ == "__main__":
    sfx()
    music()
