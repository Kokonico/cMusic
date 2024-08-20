#!/usr/bin/env python3.12
"""cmusic CLI script"""

import os

# prevent pygame support prompt (must do before importing anything from pygame)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Limbo /// Climax
# Clair De Lune

# this is the entry point for cMusic, this is the script that is run when the user runs `cmusic` in the terminal.
# it is responsible for parsing the arguments and running the correct command.
# it also handles some basic error handling and logging.

from cmusic import constants

from objlog.LogMessages import Debug, Info, Warn, Error, Fatal
from cmusic import main as central

MAIN = central.MAIN
try:
    import argparse
    import subprocess

    import traceback
    import time
except ImportError as e:
    MAIN.print = True
    MAIN.log(Fatal("Failed to import required module: " + str(e)))
    MAIN.log(e)
    MAIN.log(Error("Please install the required modules by running 'pip install'"))
    MAIN.print = False
    exit(1)

try:
    from cmusic.constants import CRASH_FOLDER
except ImportError:
    MAIN.print = True
    MAIN.log(Fatal("Failed to import internal variable: constants -> CRASH_FOLDER"))
    MAIN.log(Error("Please check the integrity of the installation"))
    MAIN.print = False
    exit(1)

def main():
    # verify the OS (to make sure it's supported)
    # PS: if your adding support for a new OS, please make sure to change this code to reflect that.
    os_name = os.name
    match os_name:
        case "nt":
            # windows
            try:
                os.environ["CMUSIC_HIDE_UNSUPPORTED_OS"]
            except KeyError:
                MAIN.log(
                    Warn(
                        "Windows is not supported, and will probably not work correctly."
                    )
                )
                print(
                    "Windows is not supported, and will most likely not work correctly, this program will now exit."
                )
                exit(1)
        case "posix":
            MAIN.log(Info("Detected POSIX OS, should work fine."))
        case _:
            MAIN.log(Warn("Unknown OS, here be dragons."))
            print("Unknown OS, here be dragons.")

    # assure tmux is installed
    tmux_check = subprocess.run(["tmux", "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if tmux_check.returncode != 0:
        # tmux isn't installed
        MAIN.log(Warn("tmux is not installed."))
        specific_os = (
            subprocess.run(
                ["uname", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            .stdout.decode("utf-8")
            .strip()
        )
        if specific_os == "Darwin":
            MAIN.log(
                Info(
                    "macOS detected, requesting installation of tmux via Homebrew."
                )
            )
            tmux_install = input("Would you like to install tmux via Homebrew? (y/n): ")
            if tmux_install.lower() == "y":
                brew_install = subprocess.run(["brew", "install", "tmux"])
                if brew_install.returncode != 0:
                    MAIN.log(Error("Failed to install tmux via Homebrew."))
                    print(
                        "Failed to install tmux via Homebrew, do you have Homebrew installed?"
                    )
                    exit(1)
            else:
                MAIN.log(
                    Warn("tmux is required for background playback, please install it.")
                )
                print(
                    "tmux is required for background playback, please install it in some way or another."
                )
                exit(1)

        elif specific_os == "Linux":
            # linux
            # if someone could provide a way to ask the user to install tmux on linux, that would be great.
            MAIN.log(Warn("tmux is not installed."))
            print(
                "tmux is not installed, please install it via your package manager or add it to your PATH."
            )
            exit(1)
        else:
            MAIN.log(Warn("Unable to determine OS, please install tmux manually."))
            print("Unable to determine OS, please install tmux manually.")

    parser = argparse.ArgumentParser(description="cMusic, for all your music needs.")
    # arguments
    # if you add a new command, make sure to add it to the choices list or it won't work.
    parser.add_argument(
        "command",
        help="The command to run.",
        choices=[
            "play",
            "index",
            "version",
            "list",
            "search",
            "c",
            "p",
            "v",
            "q",
            "edit",
            "info",
            "flush",
            "playlist",
            "del",
            "queue"
        ],
    )
    parser.add_argument("args", help="Arguments for the command.", nargs="*")
    parser.add_argument("--loop", help="Loops the song if set", action="store_true")
    parser.add_argument(
        "--shuffle", help="Shuffles the songs if set", action="store_true"
    )
    parser.add_argument(
        "--background",
        help="Makes the song play, but doesn't stop you from controlling the "
        "terminal.",
        action="store_true",
    )
    parser.add_argument(
        "--reindex", help="Re-index the whole library", action="store_true"
    )
    parser.add_argument(
        "--reformat",
        help="Reformat the library, actually edits the files, is done automatically before re-indexing.",
        action="store_true",
    )
    parser.add_argument(
        "--cleanup",
        help="Clean up the library, removing any files that are not in the index, or vice-versa",
        action="store_true",
    )
    parser.add_argument(
        "--_background_process",
        help="Internal use only, do not use.",
        action="store_true",
    )
    parser.add_argument(
        "--playlist",
        help="Search for a playlist instead of a song.",
        action="store_true",
    )
    parser.add_argument(
        "--_crash",
        help="crash the program for testing purposes",
        action="store_true",
    )
    args = parser.parse_args()
    args = vars(args)
    try:

        central.main(args)
    except KeyboardInterrupt:
        MAIN.log(Info("User shutdown Program"))
        print("User shutdown Program")
    except Exception as e:
        MAIN.print = True
        MAIN.log(Fatal(f"Oh No, cMusic has crashed!"))
        MAIN.log(Info(f"Crash log saved to {CRASH_FOLDER}"))
        MAIN.log(Info(("Press enter to exit...")))
        MAIN.print = False
        MAIN.log(e)
        MAIN.log(Error(f"Traceback: \n{traceback.format_exc()}"))
        MAIN.dump_messages(
            os.path.join(
                CRASH_FOLDER, f"crash_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
            )
        )
        # wait for any key press
        input()

if __name__ == "__main__":
    main()
