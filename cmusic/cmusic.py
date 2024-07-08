#!/usr/bin/env python3.12
"""cmusic CLI script"""

import os

# prevent pygame support prompt (must do before importing anything from pygame)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from . import constants

from objlog.LogMessages import Debug, Info, Warn, Error, Fatal
from . import main as central

MAIN = central.MAIN
try:
    import argparse
    import subprocess
    from .constants import CRASH_FOLDER

    import traceback
    import time
except ImportError as e:
    MAIN.print = True
    MAIN.log(Fatal("Failed to import required module: " + str(e)))
    MAIN.log(e)
    MAIN.log(Error("Please install the required modules by running 'poetry install'"))
    MAIN.print = False
    exit(1)

def is_running_in_wsl():
    # Check for WSL-specific environment variable
    if "WSL_DISTRO_NAME" in os.environ:
        return True

def main():
    # verify the OS (to make sure it's supported)
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
            if is_running_in_wsl():
                if os.environ.get("CMUSIC_WSL_IGNORE") == "true":
                    MAIN.log(Info("WSL detected, but user has chosen to ignore it."))
                else:
                    MAIN.log(Warn("WSL detected, there will be issues if not properly configured!"))
                    result = input("Warning: you have been detected to be running in WSL, which will not work if not configured properly. \
                     do you want to continue? (you won't be asked this again if you do!) (y/n): ")
                    if result.lower() != "y":
                        exit(1)
                    else:
                        os.environ["CMUSIC_WSL_IGNORE"] = "true"
                        pulse_setup = input("would you like to try to automatically configure pulseaudio? (y/n): ")
                        if pulse_setup.lower() == "y":
                            print("Installing PulseAudio...")
                            subprocess.run(["sudo", "apt-get", "update"], check=True)
                            subprocess.run(["sudo", "apt-get", "install", "-y", "pulseaudio"], check=True)
                            print("PulseAudio installed.")
                            print("Configuring PulseAudio server...")
                            print("Configuring PULSE_SERVER environment variable...")
                            host_ip = subprocess.run(["grep", "nameserver", "/etc/resolv.conf"], capture_output=True,
                                                     text=True).stdout.split()[1]
                            with open(os.path.expanduser("~/.bashrc"), "a") as bashrc:
                                bashrc.write(f'\nexport PULSE_SERVER=tcp:{host_ip}\n')
                            print("PULSE_SERVER environment variable configured.")
                            print("All Done!")
                            # clear shell
                            os.system("clear")
                            print("WHAT TO DO NEXT:")
                            print("1: Download and install PulseAudio for Windows from https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/ (if you haven't already)")
                            print("2. (ON WINDOWS) Edit your default.pa within your pulse directory to load the TCP module with your local network.")
                            print("3. (ON WINDOWS) Edit your daemon.conf within your pulse directory and set 'exit-idle-time' to -1.")
                            print("4. (ON WINDOWS) Start Pulseaudio using bin\\pulseaudio.exe")
                            print("5. (ON WINDOWS) restart your WSL environment.")
                            print("these instructions have been saved to ~/cmusic_pulseaudio_instructions.txt")
                            with open(os.path.expanduser("~/cmusic_pulseaudio_instructions.txt"), "w") as f:
                                f.write("WHAT TO DO NEXT:\n")
                                f.write("1: Download and install PulseAudio for Windows from https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/ (if you haven't already)\n")
                                f.write("2. (ON WINDOWS) Edit your default.pa within your pulse directory to load the TCP module with your local network.\n")
                                f.write("3. (ON WINDOWS) Edit your daemon.conf within your pulse directory and set 'exit-idle-time' to -1.\n")
                                f.write("4. (ON WINDOWS) Start Pulseaudio using bin\\pulseaudio.exe\n")
                                f.write("5. (ON WINDOWS) restart your WSL environment.\n")
                            exit(1)

                        else:
                            print("Please configure PulseAudio manually if you haven't already, the program will "
                                  "start normally next time.")
                            exit(1)



            MAIN.log(Info("Detected POSIX OS, should work fine."))
        case _:
            MAIN.log(Warn("Unknown OS, here be dragons."))
            print("Unknown OS, here be dragons.")

    # assure tmux is installed
    tmux_check = subprocess.run(
        ["tmux", "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
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
                    "macOS (superior OS) detected, requesting installation of tmux via Homebrew."
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

    parser = argparse.ArgumentParser(description="cMusic, for all your music needs.")
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
        MAIN.log(Info(("Press any key to exit...")))
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
