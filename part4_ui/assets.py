# =====================================================================
#  part4_ui/assets.py  —  LOADING IMAGES + PLAYING SOUNDS
#  OWNER: Person 4 (UI)
# =====================================================================
#
# One place that loads every picture, font and sound from part4_ui/assets/,
# so nobody else has to deal with file paths.
#
#   get_image("tankBody_red", scale=1.4, rotate=-90)   -> cached Surface
#   get_font(32)                                        -> Kenney Future font
#   play_sound("explosion")                             -> random variant
#
# Everything is cached (loaded once). Missing files never crash the game:
# get_image returns a magenta placeholder and play_sound does nothing.
# Art: Kenney.nl (CC0) — see assets/CREDITS.md
# =====================================================================
import os
import random

import pygame

from shared import web

from shared.resources import resource_path

ASSET_DIR = resource_path("part4_ui", "assets")

_images = {}
_fonts = {}
_sounds = {}
_sound_ok = None
_volume = 0.7


# ---------------- images ----------------
def _find_image(name):
    for folder in ("tanks", "ui", "weapons", ""):
        path = os.path.join(ASSET_DIR, "images", folder, name + ".png")
        if os.path.exists(path):
            return path
    return None


def has_image(name):
    return _find_image(name) is not None


def get_image(name, scale=1.0, rotate=0, size=None):
    """Load a PNG by name (without .png). Rotate is in degrees, counter-clockwise."""
    key = (name, scale, rotate, size)
    if key in _images:
        return _images[key]
    path = _find_image(name)
    if path is None:
        print("[assets] missing image:", name)
        image = pygame.Surface((24, 24), pygame.SRCALPHA)
        image.fill((255, 0, 255, 180))
    else:
        image = pygame.image.load(path)
        image = image.convert_alpha() if pygame.display.get_surface() else image
    if size is not None:
        image = pygame.transform.smoothscale(image, size)
    elif scale != 1.0:
        w, h = image.get_size()
        image = pygame.transform.smoothscale(image, (max(1, round(w * scale)), max(1, round(h * scale))))
    if rotate:
        image = pygame.transform.rotate(image, rotate)
    _images[key] = image
    return image


# ---------------- fonts ----------------
def get_font(size, kind="future"):
    """kind: 'title' (Bungee - big chunky titles), 'future' + 'narrow' (Pixelify Sans - UI and HUD),
    'pixel' (Kenney pixel font - tiny labels over tanks)."""
    key = (size, kind)
    if key not in _fonts:
        files = {"title": "bungee.ttf", "future": "pixelify.ttf", "narrow": "pixelify.ttf", "pixel": "pixel.ttf"}
        path = os.path.join(ASSET_DIR, "fonts", files.get(kind, "future.ttf"))
        try:
            _fonts[key] = pygame.font.Font(path, size)
        except (OSError, FileNotFoundError):
            _fonts[key] = pygame.font.Font(None, int(size * 1.3))
    return _fonts[key]


# ---------------- sounds ----------------
# game name -> sound files, all made by tools/make_audio.py (our own synth).
SOUND_FILES = {
    "explosion": ["sfx_explosion"],
    "big_explosion": ["sfx_big_explosion"],
    "shot_small": ["sfx_shot_small"],
    "shot_cannon": ["sfx_shot_cannon"],
    "shot_shotgun": ["sfx_shot_shotgun"],
    "shot_rail": ["sfx_shot_rail"],
    "shot_rocket": ["sfx_shot_rocket"],
    "shot_bouncer": ["sfx_shot_bouncer"],
    "hit": ["sfx_hit"],
    "break": ["sfx_break"],
    "pickup": ["sfx_pickup"],
    "heal": ["sfx_heal"],
    "spawn": ["sfx_spawn"],
    "empty": ["sfx_empty"],
    "click": ["sfx_click"],
    "select": ["sfx_select"],
    "confirm": ["sfx_confirm"],
    "go": ["sfx_go"],
    "crate_drop": ["sfx_crate_drop"],
    "countdown": ["sfx_countdown"],
    "switch": ["sfx_switch"],
    "zone_warning": ["sfx_zone_warning"],
    "zone_hurt": ["sfx_zone_hurt"],
}
SOUND_VOLUME = {"shot_small": 0.45, "hit": 0.6, "click": 0.6, "select": 0.5, "crate_drop": 0.6,
                "zone_hurt": 0.5, "explosion": 0.9, "big_explosion": 1.0}

# The same sound may only start again after GAP ms, and only MAX_AT_ONCE copies may ring
# together. Without this, 6 crates landing at the same moment (start of a match) or a
# machine gun + 3 explosions add up past the speaker's limit -> loud crackle.
GAP_MS = {"shot_small": 45, "crate_drop": 140, "explosion": 70, "big_explosion": 110, "hit": 50}
MAX_AT_ONCE = {"explosion": 3, "big_explosion": 2, "crate_drop": 2, "shot_small": 3}
_last_play = {}
_playing = {}       # name -> list of end times (ms)

_music_volume = 0.5
_music_mood = None           # "menu" / "battle" / "victory"
_music_track = None
_music_started = 0

# Music: several tracks per mood, played in a random order (never the same twice in a row).
PLAYLISTS = {
    "menu": ["menu_1", "menu_2", "menu_3"],
    "battle": ["battle_1", "battle_2", "battle_3", "battle_4", "battle_5", "battle_6"],
    "victory": ["victory"],
}


def init_sound():
    global _sound_ok
    if _sound_ok is not None:
        return _sound_ok
    if web.IS_WEB:                     # the browser plays all sound (see shared/web.py dtSfx / dtMusic)
        _sound_ok = True
        return True
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)
        pygame.mixer.set_num_channels(24)
        _sound_ok = True
    except pygame.error:
        _sound_ok = False
    return _sound_ok


def preload_web_sounds():
    """Web version: let the browser download + decode every effect now (not on the first shot)."""
    if web.IS_WEB:
        names = sorted({f for files in SOUND_FILES.values() for f in files})
        web.js("dtSfx.preload(%s)" % web.js_str(",".join(names)))


def set_volume(volume):
    global _volume
    _volume = max(0.0, min(1.0, volume))


def get_volume():
    return _volume


def _load_sound(file_name):
    if file_name not in _sounds:
        path = os.path.join(ASSET_DIR, "sounds", file_name + ".wav")
        if not os.path.exists(path):
            path = os.path.join(ASSET_DIR, "sounds", file_name + ".ogg")
        try:
            _sounds[file_name] = pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError):
            _sounds[file_name] = None
    return _sounds[file_name]


def _allowed(name, length_ms):
    """Rate limit: is this sound allowed to start now?"""
    now = pygame.time.get_ticks()
    if now - _last_play.get(name, -99999) < GAP_MS.get(name, 30):
        return False
    alive = [end for end in _playing.get(name, []) if end > now]
    if len(alive) >= MAX_AT_ONCE.get(name, 4):
        _playing[name] = alive
        return False
    alive.append(now + length_ms)
    _playing[name] = alive
    _last_play[name] = now
    return True


def play_sound(name, volume=1.0):
    if not init_sound() or _volume <= 0:
        return
    files = SOUND_FILES.get(name)
    if not files:
        return
    gain = _volume * volume * SOUND_VOLUME.get(name, 0.8)
    file_name = random.choice(files)
    if web.IS_WEB:
        if _allowed(name, 900):
            web.js("dtSfx.play(%s, %.3f)" % (web.js_str(file_name), gain))
        return
    sound = _load_sound(file_name)
    if sound is None or not _allowed(name, int(sound.get_length() * 1000)):
        return
    sound.set_volume(gain)
    sound.play()


# ---------------- music (shuffled playlists) ----------------
def set_music_volume(volume):
    global _music_volume
    _music_volume = max(0.0, min(1.0, volume))
    if web.IS_WEB:
        web.js("dtMusic.volume(%f)" % (_music_volume * 0.6))
        return
    if init_sound():
        pygame.mixer.music.set_volume(_music_volume * 0.6)


def _pick_track(mood):
    tracks = PLAYLISTS.get(mood, [mood])
    choices = [t for t in tracks if t != _music_track] or tracks
    return random.choice(choices)


def play_music(mood, loop=True, fade_ms=800):
    """Switch the music mood ("menu", "battle", "victory"). Same mood = keep playing.
    Inside a mood, tracks play one after another in a random order (see update_music)."""
    global _music_mood
    if mood == _music_mood:
        return
    _music_mood = mood
    if web.IS_WEB:
        tracks = PLAYLISTS.get(mood, [mood])
        web.js("dtMusic.volume(%f); dtMusic.playlist(%s, %s)" % (
            _music_volume * 0.6, web.js_str(",".join(tracks)), "true" if loop else "false"))
        return
    _start_track(_pick_track(mood), loop, fade_ms)


def _start_track(track, loop=True, fade_ms=800):
    global _music_track, _music_started
    if not init_sound():
        return
    path = os.path.join(ASSET_DIR, "music", track + ".mp3")
    if not os.path.exists(path):
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_music_volume * 0.6)
        # a playlist with one track (victory jingle) plays once; otherwise each track once, then the next
        pygame.mixer.music.play(0, fade_ms=fade_ms)
        _music_track = track
        _music_started = pygame.time.get_ticks()
    except pygame.error:
        _music_track = None


def update_music():
    """Call every frame (desktop): when a track ends, start a different random one."""
    if web.IS_WEB or not _music_mood or not init_sound():
        return
    if _music_mood == "victory":
        return
    if pygame.time.get_ticks() - _music_started > 1500 and not pygame.mixer.music.get_busy():
        _start_track(_pick_track(_music_mood), fade_ms=1500)


def stop_music(fade_ms=500):
    global _music_mood
    if web.IS_WEB:
        web.js("dtMusic.stop()")
    elif init_sound():
        pygame.mixer.music.fadeout(fade_ms)
    _music_mood = None
