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

from .constants import config, CONFIG_FILE, LOG_FILE

from objlog.LogMessages import Info, Error

from objlog import LogNode


class KeyHandler(threading.Thread):
    """Handles key presses for cmusic in the background."""

    def __init__(self, is_bg: bool = False):
        super(KeyHandler, self).__init__()
        self.stop_flag = threading.Event()
        self.is_bg = is_bg
        self.MAIN = LogNode("KeyHandler", log_file=LOG_FILE)
        self.MAIN.log(
            Info(
                f"Key Handler initialized with parent thread: {threading.current_thread().name}"
            )
        )

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
                            self.MAIN.log(Info(f"Volume set to {config['volume']}"))
                        case (
                            "_"
                        ):  # seems weird, but it's the minus key (shift + -), just for consistency.
                            config["volume"] -= 5
                            # load the config file and set the volume
                            with open(os.path.join(CONFIG_FILE), "w") as f:
                                f.write(json.dumps(config, indent=4))
                            self.MAIN.log(Info(f"Volume set to {config['volume']}"))
                        case " ":
                            # pause/unpause the song
                            if pygame.mixer.music.get_busy():
                                self.MAIN.log(Info("Pausing the song."))
                                pygame.mixer.music.pause()
                            else:
                                self.MAIN.log(Info("Unpausing the song."))
                                pygame.mixer.music.unpause()
                        case "e":
                            # detach tmux session (this process is within it)
                            self.MAIN.log(Info("Detaching tmux session."))
                            subprocess.run(
                                ["tmux", "detach", "-s", "cmusic_background"],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                            )
                        case "q":
                            # stop the song
                            self.MAIN.log(Info("Stopping the song."))
                            pygame.mixer.music.stop()
                            self.stop_flag.set()
        except Exception as e:
            # clean up terminos
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.MAIN.log(Error(f"Error in key handler (time to panic!)"))
            self.MAIN.log(e)
            self.MAIN.log(Error("Stack trace:"))
            self.MAIN.log(Error(f"{e.__traceback__}"))
            pygame.mixer.music.stop()
            # raise in the main thread
            raise e

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def stop(self):
        """Stops the key handler."""
        self.MAIN.log(Info("Shutting down, attempting shutdown..."))
        self.stop_flag.set()

    def join(self, timeout: float | None = None) -> None:
        self.MAIN.log(Info("Key Handler is stopping, please hold."))
        return super().join(timeout)
