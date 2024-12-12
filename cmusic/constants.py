"""cmusic constants"""

import os
import json
import objlog

from objlog.LogMessages import Info, Debug

# the path to the config file

# GREED /// CLIMAX
# Clair De Soleil

# this file contains all the constants used in the program
# it also contains the code to check if the required directories and files exist, and creates them if they don't
# if you want to add a new file / directory that the program needs, add it here.

CMUSIC_DIR = os.path.join(os.path.expanduser("~"), ".cmusic")

CONFIG_FILE = os.path.join(CMUSIC_DIR, "config.json")

LOG_FILE = os.path.join(CMUSIC_DIR, "cmusic.log")
MAIN = objlog.LogNode("CMUSIC")

QUEUE_FILE = os.path.join(CMUSIC_DIR, "queue.json")

PLAYBACK_CONFIG_FILE = os.path.join(CMUSIC_DIR, "playback.json")

PLAYBACK_CONFIG = {
    "loop": False,
    "shuffle": False,
}

# default config
# this is the default config that is written to the config file if it doesn't exist

DEFAULT_CONFIG = {
    "library": os.path.join(os.path.expanduser("~"), "cMusic Library"),
    "volume": 100,
}


class Song:
    """Should've made this sooner"""

    def __init__(self, id: int, path: str, title: str | None, artist: str | None, album: str | None, duration: float, genre: str | None, year: int | None):
        self.path = path
        self.title = title
        self.artist = artist
        self.album = album
        self.id = id
        self.duration = duration
        self.genre = genre
        self.year = year

    def export(self):
        return {
            "path": self.path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "id": self.id,
            "duration": self.duration,
            "genre": self.genre,
            "year": self.year
        }

    def __str__(self):
        return f"{self.title} by {self.artist} {f'({self.album})' if self.album else ''}"


# EXECUTION PAST THIS POINT
# ^^^ this sounds like a threat
# ^^^ shut up me from the past you're not funny
# ^^^ yes I am

# check if the cmusic directory exists
if not os.path.exists(CMUSIC_DIR):
    MAIN.log(Info("Creating cmusic directory"))
    os.makedirs(CMUSIC_DIR)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        f.write(json.dumps(DEFAULT_CONFIG, indent=4))
    MAIN.log(Info("Created config file"))
else:
    # assure all fields are present
    config = json.load(open(CONFIG_FILE))
    for key in DEFAULT_CONFIG:
        if key not in config:
            config[key] = DEFAULT_CONFIG[key]
            MAIN.log(Info(f"Added missing field to config: {key}"))
    with open(CONFIG_FILE, "w") as f:
        f.write(json.dumps(config, indent=4))

if not os.path.exists(QUEUE_FILE):
    MAIN.log(Info("generating queue file"))
    with open(QUEUE_FILE, "w") as f:
        json.dump([], f)

# create crashes directory
if not os.path.exists(os.path.join(CMUSIC_DIR, "crashes")):
    os.makedirs(os.path.join(CMUSIC_DIR, "crashes"))
    MAIN.log(Info("Created crashes directory"))

config = json.load(open(CONFIG_FILE))
LIBRARY = config["library"]
CRASH_FOLDER = os.path.join(CMUSIC_DIR, "crashes")

# create library directory
if not os.path.exists(LIBRARY):
    os.makedirs(LIBRARY)
    MAIN.log(Info("Created library directory"))

# create playback config file
if not os.path.exists(PLAYBACK_CONFIG_FILE):
    with open(PLAYBACK_CONFIG_FILE, "w") as f:
        f.write(json.dumps(PLAYBACK_CONFIG, indent=4))
    MAIN.log(Info("Created playback config file"))

# queue file

MAIN.log(Info("Constants OK"))

MAIN.set_output_file(LOG_FILE, preserve_old_messages=True)
