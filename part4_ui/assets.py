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
# game name -> sound files. "sfx_*" are made by tools/make_audio.py (our own synth);
# a Kenney sound is mixed in for some, so repeated sounds don't feel robotic.
SOUND_FILES = {
    "explosion": ["sfx_explosion", "explosionCrunch_000", "explosionCrunch_002"],
    "big_explosion": ["sfx_big_explosion", "lowFrequency_explosion_000"],
    "shot_small": ["sfx_shot_small"],
    "shot_cannon": ["sfx_shot_cannon"],
    "shot_shotgun": ["sfx_shot_shotgun"],
    "shot_rail": ["sfx_shot_rail"],
    "shot_rocket": ["sfx_shot_rocket"],
    "shot_bouncer": ["sfx_shot_bouncer"],
    "hit": ["sfx_hit", "impactMetal_000"],
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
SOUND_VOLUME = {"shot_small": 0.3, "hit": 0.5, "click": 0.5, "select": 0.4, "shot_rocket": 0.6, "big_explosion": 0.9,
                "zone_hurt": 0.35, "explosion": 0.75}

_music_volume = 0.5
_music_name = None


def init_sound():
    global _sound_ok
    if _sound_ok is not None:
        return _sound_ok
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)
        pygame.mixer.set_num_channels(24)
        _sound_ok = True
    except pygame.error:
        _sound_ok = False
    return _sound_ok


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


def play_sound(name, volume=1.0):
    if not init_sound() or _volume <= 0:
        return
    files = SOUND_FILES.get(name)
    if not files:
        return
    sound = _load_sound(random.choice(files))
    if sound is None:
        return
    sound.set_volume(_volume * volume * SOUND_VOLUME.get(name, 0.8))
    sound.play()


# ---------------- music (one looping track at a time) ----------------
def set_music_volume(volume):
    global _music_volume
    _music_volume = max(0.0, min(1.0, volume))
    if init_sound():
        pygame.mixer.music.set_volume(_music_volume * 0.6)


def play_music(name, loop=True, fade_ms=800):
    """Start a track from assets/music (menu, battle, victory). Same track = keep playing."""
    global _music_name
    if not init_sound() or name == _music_name:
        return
    path = os.path.join(ASSET_DIR, "music", name + ".wav")
    if not os.path.exists(path):
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_music_volume * 0.6)
        pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
        _music_name = name
    except pygame.error:
        _music_name = None


def stop_music(fade_ms=500):
    global _music_name
    if init_sound():
        pygame.mixer.music.fadeout(fade_ms)
    _music_name = None
