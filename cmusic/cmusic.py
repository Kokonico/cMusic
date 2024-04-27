#!/usr/bin/env python3.12
"""cmusic CLI script"""

import os

# prevent pygame support prompt (must do before importing anything from pygame)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import argparse
from . import main as central
from .constants import CRASH_FOLDER

from objlog.LogMessages import Debug, Info, Warn, Error, Fatal
import traceback
import time

MAIN = central.MAIN


def main():

    # verify the OS (to make sure it's supported)
    os_name = os.name
    match os_name:
        case "nt":
            # windows
            try:
                os.environ["CMUSIC_HIDE_UNSUPPORTED_OS"]
            except KeyError:
                MAIN.log(Warn("Windows is not supported, and will probably not work correctly."))
                print("Windows is not supported, and will most likely not work correctly.")
        case "posix":
            MAIN.log(Info("Detected POSIX OS, should work fine."))
        case _:
            MAIN.log(Warn("Unknown OS, here be dragons."))
            print("Unknown OS, here be dragons.")

    parser = argparse.ArgumentParser(description="cMusic, for all your music needs.")
    parser.add_argument("command", help="The command to run.", choices=["play", "index", "version", "list", "search"])
    parser.add_argument("args", help="Arguments for the command.", nargs="*")
    parser.add_argument("--loop", help="Loops the song if set", action="store_true")
    parser.add_argument("--shuffle", help="Shuffles the songs if set", action="store_true")
    parser.add_argument("--background", help="Makes the song play, but doesn't stop you from controlling the "
                                             "terminal.")  # TODO: implement
    parser.add_argument("--reindex", help="Re-index the whole library",
                        action="store_true")
    parser.add_argument("--reformat", help="Reformat the library, actually edits the files, is done automatically before re-indexing.", action="store_true")
    parser.add_argument("--cleanup", help="Clean up the library, removing any files that are not in the index, or vice-versa", action="store_true")
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
        MAIN.print = False
        MAIN.log(e)
        MAIN.log(Error(f"Traceback: \n{traceback.format_exc()}"))
        MAIN.dump_messages(os.path.join(CRASH_FOLDER, f"crash_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"))
