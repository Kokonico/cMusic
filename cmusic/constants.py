"""cmusic constants"""

import os
import json
import objlog

from objlog.LogMessages import Info, Debug

# the path to the config file

CMUSIC_DIR = os.path.join(os.path.expanduser("~"), ".cmusic")

CONFIG_FILE = os.path.join(CMUSIC_DIR, "config.json")

LOG_FILE = os.path.join(CMUSIC_DIR, "cmusic.log")
MAIN = objlog.LogNode("CMUSIC")

DEFAULT_CONFIG = {
    "library": os.path.join(os.path.expanduser("~"), "cMusic Library"),
    "volume": 100,
}

# check if the cmusic directory exists
if not os.path.exists(CMUSIC_DIR):
    MAIN.log(Info("Creating cmusic directory"))
    os.makedirs(CMUSIC_DIR)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        f.write(json.dumps(DEFAULT_CONFIG, indent=4))
    MAIN.log(Info("Created config file"))

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

MAIN.log(Info("Constants OK"))

MAIN.set_output_file(LOG_FILE, preserve_old_messages=True)
