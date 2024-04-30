"""Background Threads for cmusic"""

import os
import sys
import json
import tty
import termios
import select
import threading
import pygame
import subprocess

from .constants import config, CONFIG_FILE, MAIN

from objlog.LogMessages import Info, Error

class KeyHandler(threading.Thread):
    """Handles key presses for cmusic in the background."""
    def __init__(self, is_bg: bool = False):
        super(KeyHandler, self).__init__()
        self.stop_flag = threading.Event()
        self.is_bg = is_bg

    def run(self):
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while not self.stop_flag.is_set():
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    key = sys.stdin.read(1)
                    match key:
                        case "+":
                            config["volume"] += 5
                            with open(os.path.join(CONFIG_FILE), "w") as f:
                                f.write(json.dumps(config, indent=4))
                        case "_":  # seems weird, but it's the minus key (shift + -), just for consistency.
                            config["volume"] -= 5
                            # load the config file and set the volume
                            with open(os.path.join(CONFIG_FILE), "w") as f:
                                f.write(json.dumps(config, indent=4))
                        case " ":
                            # pause/unpause the song
                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.pause()
                            else:
                                pygame.mixer.music.unpause()
                        case "e":
                            # detach tmux session (this process is within it)
                            subprocess.run(["tmux", "detach", "-s", "cmusic_background"], stderr=subprocess.PIPE)
        except Exception as e:
            if self.stop_flag.is_set():
                return
            # clean up terminos
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            MAIN.log(Error(f"Error in key handler (time to panic!)"))
            MAIN.log(e)
            # raise in the main thread
            raise e

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def stop(self):
        self.stop_flag.set()

    def join(self, timeout: float | None = None) -> None:
        MAIN.log(Info("Key Handler is stopping, please hold."))
        return super().join(timeout)
