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

# TODO: better argument auto-completion

from cmusic import constants

from objlog import LogNode
from objlog.LogMessages import Debug, Info, Warn, Error, Fatal
from cmusic import main as central

BOOTLOADER = LogNode(name="BOOTLOADER", log_file=constants.LOG_FILE)
try:
    import argparse
    import subprocess
    import readline
    import traceback
    import time
except ImportError as e:
    BOOTLOADER.print = True
    BOOTLOADER.log(Fatal("Failed to import required python module: " + str(e)))
    BOOTLOADER.log(e)
    BOOTLOADER.log(Error("If you have compiled python from source, make sure all dependencies are installed and recompile, "
                   "otherwise your python installation may be corrupt/out of version."))
    BOOTLOADER.print = False
    exit(1)

try:
    from cmusic.constants import CRASH_FOLDER
except ImportError:
    BOOTLOADER.print = True
    BOOTLOADER.log(Fatal("Failed to import internal variable: constants -> CRASH_FOLDER"))
    BOOTLOADER.log(Error("Please check the integrity of the installation"))
    BOOTLOADER.print = False
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
                BOOTLOADER.log(
                    Warn(
                        "Windows is not supported, and will probably not work correctly."
                    )
                )
                print(
                    "Windows is not supported, and will most likely not work correctly, this program will now exit."
                )
                exit(1)
        case "posix":
            BOOTLOADER.log(Info("Detected POSIX OS, should work fine."))
        case _:
            BOOTLOADER.log(Warn("Unknown OS, here be dragons."))
            print("Unknown OS, here be dragons.")

    # assure tmux is installed
    tmux_check = subprocess.run(["tmux", "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if tmux_check.returncode != 0:
        # tmux isn't installed
        BOOTLOADER.log(Warn("tmux is not installed."))
        specific_os = (
            subprocess.run(
                ["uname", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            .stdout.decode("utf-8")
            .strip()
        )
        if specific_os == "Darwin":
            BOOTLOADER.log(
                Info(
                    "macOS detected, requesting installation of tmux via Homebrew."
                )
            )
            tmux_install = input("Would you like to install tmux via Homebrew? (y/n): ")
            if tmux_install.lower() == "y":
                brew_install = subprocess.run(["brew", "install", "tmux"])
                if brew_install.returncode != 0:
                    BOOTLOADER.log(Error("Failed to install tmux via Homebrew."))
                    print(
                        "Failed to install tmux via Homebrew, do you have Homebrew installed?"
                    )
                    exit(1)
            else:
                BOOTLOADER.log(
                    Warn("tmux is required for background playback, please install it.")
                )
                print(
                    "tmux is required for background playback, please install it in some way or another."
                )
                exit(1)

        elif specific_os == "Linux":
            # linux
            # if someone could provide a way to ask the user to install tmux on linux, that would be great.
            BOOTLOADER.log(Warn("tmux is not installed."))
            print(
                "tmux is not installed, please install it via your package manager or add it to your PATH."
            )
            exit(1)
        else:
            BOOTLOADER.log(Warn("Unable to determine OS, please install tmux manually."))
            print("Unable to determine OS, please install tmux manually.")

    # this may break everything
    # god take the wheel
    parser = argparse.ArgumentParser(description="cMusic, for all your music needs.")
    command_subparsers = parser.add_subparsers(dest="command", help="The command to run.", required=True)

    command_subparsers.add_parser("play", help="Play a song.")
    command_subparsers.add_parser("index", help="Index the music library.")
    command_subparsers.add_parser("version", help="Show version information.")
    command_subparsers.add_parser("list", help="List songs.")
    command_subparsers.add_parser("search", help="Search for a song.")
    command_subparsers.add_parser("c", help="Connect to the background session.")
    command_subparsers.add_parser("p", help="Pause the background session.")
    command_subparsers.add_parser("v", help="Change the volume of the background session.")
    command_subparsers.add_parser("q", help="Quit the background session.")
    command_subparsers.add_parser("edit", help="Edit a song.")
    command_subparsers.add_parser("info", help="Show song information.")
    command_subparsers.add_parser("flush", help="Flush the logs.")
    command_subparsers.add_parser("del", help="Delete a song.")
    command_subparsers.add_parser("queue", help="Add a song to queue")

    playlist_parser = command_subparsers.add_parser("playlist", help="Manage playlists.")
    playlist_subparsers = playlist_parser.add_subparsers(dest="playlist_command", help="The playlist command to "
                                                                                       "execute.")
    playlist_subparsers.required = True
    playlist_parser.required = False  # we don't need to require the playlist command, it's just a single command
    # that can be run.

    playlist_subparsers.add_parser("create", help="Create a new playlist.")
    playlist_subparsers.add_parser("delete", help="Delete a playlist.")
    playlist_subparsers.add_parser("add", help="Add a song to a playlist.")
    playlist_subparsers.add_parser("remove", help="Remove a song from a playlist.")
    playlist_subparsers.add_parser("list", help="List all playlists or a playlist's songs if it is fed a name.")

    # flags

    parser.add_argument("--loop", help="Loops the song if set", action="store_true")
    parser.add_argument("--shuffle", help="Shuffles the songs if set", action="store_true")
    parser.add_argument("--background", help="Makes the song play, but doesn't stop you from controlling the terminal.",
                        action="store_true")
    parser.add_argument("--reindex", help="Re-index the whole library", action="store_true")
    parser.add_argument("--reformat",
                        help="Reformat the library, actually edits the files, is done automatically before re-indexing.",
                        action="store_true")
    parser.add_argument("--cleanup",
                        help="Clean up the library, removing any files that are not in the index, or vice-versa",
                        action="store_true")
    parser.add_argument("--_background_process", help="Internal use only, do not use.", action="store_true")
    parser.add_argument("--_crash", help="Crash the program for testing purposes", action="store_true")
    parser.add_argument("--playlist", help="whether to execute the command in the context of a playlist or not",
                        action="store_true")

    # capture subsequent arguments
    args, unknown_args = parser.parse_known_args()

    args = vars(args)
    args_list = [args["command"]]
    args_list += list(key for key in args.keys() if args[key] is True)

    all_arguments = args_list + unknown_args

    # capture any flags that were set in arguments

    for arg in all_arguments:
        if arg.startswith("--"):
            args[arg[2:]] = True
            # remove the flag from the unknown_args
            unknown_args.remove(arg)
        elif arg.startswith("-"):
            args[arg[1:]] = True
            # also remove the flag from the unknown_args
            unknown_args.remove(arg)

    args["args"] = unknown_args

    try:

        central.main(args)
    except KeyboardInterrupt:
        BOOTLOADER.log(Info("User shutdown Program"))
        print("User shutdown Program")
    except Exception as e:
        BOOTLOADER.print = True
        BOOTLOADER.log(Fatal(f"Oh No, cMusic has crashed!"))
        BOOTLOADER.log(Info(f"Crash log saved to {CRASH_FOLDER}"))
        BOOTLOADER.log(Info("Press enter to exit..."))
        BOOTLOADER.print = False
        BOOTLOADER.log(e)
        BOOTLOADER.log(Error(f"Traceback: \n{traceback.format_exc()}"))
        BOOTLOADER.dump_messages(
            os.path.join(
                CRASH_FOLDER, f"crash_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
            )
        )
        # wait for any key press
        input()


if __name__ == "__main__":
    main()
