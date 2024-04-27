"""main internals for cmusic"""

__version__ = "1.0.0"
extra = "Alpha Somewhat Messy™️edition (almost done doing: remove dumpster fire from code)"

import os
import multiprocessing
import queue
# local package imports
from . import indexlib
from . import bg_threads
from .constants import MAIN, config, CONFIG_FILE

import math
import random
import json

from objlog.LogMessages import Debug, Info, Warn, Error, Fatal

import inquirer
import pygame
from tinytag import TinyTag

def main(args: dict):
    """Main function for cMusic."""

    if args["reformat"]:
        # reformat the library
        indexlib.reformat()

    if args["reindex"]:
        indexlib.index_library(config["library"])

    match args["command"]:
        case "play":
            if args["shuffle"]:
                # shuffle the songs (args.args)
                random.shuffle(args["args"])
            # convert the song names to paths & data (tuple)
            songs = [scan_library(song) for song in args["args"] if song is not None]
            # remove any None values from the list
            songs = [song for song in songs if song is not None]
            # find any lists in the song list and add them to the songs list
            for song in songs:
                if isinstance(song, list):
                    songs += song
                    songs.remove(song)

            # play the songs
            if not songs:
                MAIN.log(Warn("No songs found to play."))
                print("No songs found to play.")
                return
            try:
                while True:
                    for song in songs:
                        play(song[1], song, args["loop"], args["shuffle"])
                    if not args["loop"]:
                        break
            except KeyboardInterrupt:  # catch the KeyboardInterrupt so the program can exit
                MAIN.log(Info("User shutdown Program"))
                print("User shutdown Program")

        case "index":
            # add a file to the library
            for song_file in args["args"]:
                if os.path.exists(song_file) and song_file.endswith(".mp3"):
                    indexlib.index(song_file)

        case "version":
            print(f"cMusic v{__version__} {extra}")

        case "list":
            # list all songs in the library (through the index)
            songs = indexlib.search_index(config["library"], "")
            for song in songs:
                print(f"{song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}")
        case "search":
            # search for a song in the library
            songs = indexlib.search_index(config["library"], args["args"][0])
            for song in songs:
                print(f"{song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}")


def scan_library(songname):
    """
    :param songname:
    :return:
    """
    # scan the library for songs. basically, all this does is look for a file with the name of the song
    # (assuming the song doesn't contain the file extension), no case/whitespace sensitivity

    # get the library path
    library = config["library"]
    # scan the library via the index
    songs = indexlib.search_index(library, songname)
    # use Inquirer to ask the user which song they want to play (if there are multiple matches) else, just play
    # the song.
    if len(songs) == 0:
        MAIN.log(Warn(f"Could not find song '{songname}' in library."))
        return None
    elif len(songs) == 1:
        # get the song path (file)
        return songs[0]
    else:
        # multiple songs found, ask the user which one they want to play
        if len(songs) > 1:
            # ask the user which song they want to play
            questions = [
                inquirer.List("song", message=f"Select the song that matches '{songname}'",
                              choices=[song[2] for song in songs] + ["^^^ All of the above ^^^"])
            ]
            answers = inquirer.prompt(questions)
            if answers is not None:
                songname = answers["song"]
            else:
                # user cancelled
                return None

            if songname == "^^^ All of the above ^^^":  # TODO: code is crap, fix
                return [song for song in songs]
            for song in songs:
                if song[2] == songname:
                    return song


def proper(time_int):
    """
    returns a proper time string (xx) from an integer

    :param time_int:
    :return:
    """
    # TODO: make this work for hours and up
    return time_int if len(str(time_int)) >= 2 else '0' + str(time_int)


def draw_interface(tags, song_data, looped, shuffle):
    """draw the music player interface once."""
    # play the song
    # set volume from config
    pygame.mixer.music.set_volume(config["volume"] / 100)

    # build music player
    # figure out percentage of song done
    elapsed = pygame.mixer.music.get_pos()
    duration = tags.duration * 1000
    percentage = elapsed / duration
    # print progress bar
    # like the following:
    # ──────────────────────⬤️──────
    # length of bar is 30 characters with a ⬤️ at the percentage
    bar_length = 30
    bar = "─" * bar_length
    bar = list(bar)
    try:
        bar[int(bar_length * percentage)] = "⬤️"
    except IndexError:
        # song is done
        return
    final_bar = "".join(bar)

    # get volume from config

    volume = int(config["volume"])

    # calculate volume slider (volume is 0-100, so 70% would be 70% of 4 characters)
    # ex:
    # ──○─ 🔊 70%

    if volume > 100:
        volume = 100
        # reset volume to 100 in config file
        with open(CONFIG_FILE, "w") as f:
            config["volume"] = 100
            f.write(json.dumps(config, indent=4))
    elif volume < 0:
        volume = 0
        with open(CONFIG_FILE, "w") as f:
            config["volume"] = 0
            f.write(json.dumps(config, indent=4))
    slider_length = 5
    slider = "─" * slider_length
    slider = list(slider)
    # position the slider "○" at the volume percentage
    slider[min(max(math.floor((volume / 100) * slider_length), 0), slider_length - 1)] = "○"
    final_slider = "".join(slider) + " 🔊 " + str(volume) + "%"

    # get the time elapsed (in minutes and seconds) (xx:xx)
    elapsed_seconds = elapsed / 1000
    elapsed_minutes = elapsed_seconds // 60
    elapsed_seconds %= 60
    # get the duration (in minutes and seconds) (xx:xx)
    duration_seconds = tags.duration
    duration_minutes = duration_seconds // 60
    duration_seconds %= 60

    # get state of music (paused, or playing)
    state = "|>" if not pygame.mixer.music.get_busy() else "||"
    # this line is a disaster
    # please don't touch it
    final_playing = f"NOW PLAYING: {song_data[2] if song_data[2] is not None else tags.title if tags.title is not None else song_data[1].split('/')[-1].split('.')[0]} by {song_data[3] if song_data[3] is not None else tags.artist} {f'({song_data[4]})' if song_data[4] not in ['None', None] else f'({tags.album})' if tags.album not in ['None', None] else ''}"

    new_state = f"\r{final_playing}\n{final_bar}\n<< {state} >> {proper(int(elapsed_minutes))}:{proper(int(elapsed_seconds))} / {proper(int(duration_minutes))}:{proper(int(duration_seconds))} {final_slider} {'🔁' if looped else ''}{'🔀' if shuffle else ''}"
    return "\033c" + new_state


def play(song_path, song_data, looped, shuffle):
    """play a song."""
    # get the song path
    last_printed_state = None
    if song_path is None:
        MAIN.log(FileNotFoundError(f"Could not find song '{song_data[1]}' in library."))
        raise FileNotFoundError(f"Could not find song '{song_data[2]}' in library.")
    # play the song
    MAIN.log(Info(f"Playing song '{song_path}'..."))
    tags = TinyTag.get(song_path)
    pygame.mixer.init()
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.set_volume(config["volume"] / 100)
    pygame.mixer.music.play()
    key_thread = bg_threads.KeyHandler()
    try:
        # start the key press listener
        key_thread.start()
        while pygame.mixer.music.get_pos() != -1:

            # draw the interface
            interface_frame = draw_interface(tags, song_data, looped, shuffle)
            if interface_frame != last_printed_state:
                print(interface_frame)
                last_printed_state = interface_frame
            pygame.time.delay(100)

        # song is done
        # kill the key press listener
        key_thread.stop()
        key_thread.join()
    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        # kill the key press listener
        if key_thread.is_alive():
            key_thread.stop()
            key_thread.join()
        raise KeyboardInterrupt("User shutdown Program")  # re-raise the KeyboardInterrupt so the program can exit
