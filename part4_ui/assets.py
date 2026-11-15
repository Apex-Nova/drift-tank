import pygame
from pathlib import Path


ASSET_DIR = Path(__file__).parent / "assets"
IMAGE_DIR = ASSET_DIR / "images"
SOUND_DIR = ASSET_DIR / "sounds"

images = {}
sounds = {}

music_enabled = True
assets_loaded = False

IMAGE_FILES = {
    "tank_p1": "tank_p1.png",
    "tank_p2": "tank_p2.png",
    "tank_p3": "tank_p3.png",
    "tree_large": "tree_large.png",
    "tree_Small": "treeSmall.png",
    "barrel_green": "barrel_green.png",
    "barrel_red": "barrel_red.png",
    "bullet": "bullet.png",
    "smoke_grey": "smoke_grey.png",
    "smoke_orange": "smoke_orange.png",
    "smoke_white": "smoke_white.png"
}

SOUND_FILES = {
    "shoot": "shoot.ogg",
    "explosion": "explosion.ogg",
    "pickup": "pickup.ogg",
    "hit": "hit.ogg",
    "bullet_hit": "bullet_hit.ogg",
    "explosion_hit": "explosion_hit.ogg",
}

MUSIC_FILE = "music.ogg"

def load_assets(tile_size=None):

    global assets_loaded

    if assets_loaded:
        return
    
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except pygame.error as error:
        print(f"Warning: Sound mixer could not initialize: {error}")

    for name, filename in IMAGE_FILES.items():

        image_path = IMAGE_DIR / filename

        try:
            image = pygame.image.load(str(image_path))

            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            if tile_size is not None:
                image = pygame.transform.scale(
                    image,
                    (tile_size, tile_size)
                )

            images[name] = image
        except (pygame.error, FileNotFoundError) as error:
            print(f"Warning: Image '{filename}' could not load: {error}")

    
    if pygame.mixer.get_init():

        for name, filename in SOUND_FILES.items():

            sound_path = SOUND_DIR / filename

            try:
                sounds[name] = pygame.mixer.Sound(str(sound_path))

            except (pygame.error, FileNotFoundError) as error:
                print(f"Warning: Sound '{filename}' could not load: {error}")

    else:
        print("Warning: Sounds are unavailable because mixer is not initialized.")

    assets_loaded = True

    print("UI assets loading completed.")

def get_image(name):

    image = images.get(name)

    if image is None:
        print(f"Warning: Image '{name}' not found.")

    return image 
def play_sound(name):

    sound = sounds.get(name)

    if sound is None:
        print(f"Warning: Sound '{name}' not found.")
        return

    try:
        sound.play()

    except pygame.error as error:
        print(f"Warning: Could not play sound '{name}': {error}")

def play_music(loop=True):

    if not music_enabled:
        return

    music_path = SOUND_DIR / MUSIC_FILE

    if not music_path.exists():
        print(f"Warning: Background music not found: {music_path}")
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(str(music_path))

        loops = -1 if loop else 0

        pygame.mixer.music.play(loops)

    except pygame.error as error:
        print(f"Warning: Background music could not play: {error}")

def stop_music():

    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    except pygame.error as error:
        print(f"Warning: Could not stop music: {error}")

def set_music_enabled(enabled):

    global music_enabled

    music_enabled = bool(enabled)

    if music_enabled:
        play_music()
    else:
        stop_music()
def set_sound_volume(volume):

    volume = max(0.0, min(1.0, float(volume)))

    for sound in sounds.values():
        sound.set_volume(volume)