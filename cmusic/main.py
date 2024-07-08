"""main internals for cmusic"""

__version__ = "1.0.8"
extra = "Stable"

import os
import subprocess

# local package imports
from . import indexlib
from . import bg_threads
from .constants import MAIN, config, CONFIG_FILE, LIBRARY

import math
import random
import json

from objlog.LogMessages import Debug, Info, Warn, Error, Fatal

import inquirer
import pygame
from tinytag import TinyTag


def main(args: dict):
    """Main function for cMusic."""

    if args["_crash"] and args["command"] != "play":
        raise Exception("Manual Crash Triggered.")

    indexlib.init_index(LIBRARY)

    if args["reformat"]:
        # reformat the library
        indexlib.reformat()

    if args["reindex"]:
        indexlib.index_library(config["library"])

    match args["command"]:
        case "play":

            # check if the background process is running
            if not args["_background_process"]:
                MAIN.log(
                    Info(
                        "This is a direct call to play a song, creating a new tmux session."
                    )
                )
                # activate tmux session (same command as this one, but with the _background_process flag and no
                # --background flag)
                args["_background_process"] = True
                background = args["background"]
                args["background"] = False
                # load tmux session

                # get all flags from the args dict
                flags = [f"--{flag}" for flag in args if args[flag] is True]
                # get all args from the args dict
                args = [args["command"]] + [
                    arg for arg in args["args"] if "--" + arg not in flags
                ]

                MAIN.log(Debug(f"args: {args}"))
                MAIN.log(Debug(f"flags: {flags}"))

                constructed_command = (
                    ["tmux", "new-session", "-d", "-s", "cmusic_background", "cmusic"]
                    + args
                    + flags
                )

                MAIN.log(Debug(f"Running command: {constructed_command}"))

                tmux = subprocess.run(constructed_command, stderr=subprocess.PIPE)
                if tmux.returncode != 0:
                    MAIN.log(Error("Failed to start background process."))
                    MAIN.log(Error(tmux.stderr.decode("utf-8")))
                    print(
                        f"Failed to Initiate song playback. ({tmux.stderr.decode('utf-8')})"
                    )
                    return
                subprocess.run(
                    ["tmux", "detach", "-t", "cmusic_background"],
                    stderr=subprocess.PIPE,
                )

                if not background:
                    MAIN.log(Info("Pulling session to foreground."))
                    pull_session("cmusic_background")
                MAIN.log(Info("Background process started, peace out."))
                return
            MAIN.log(Info("Starting cMusic (for real this time)"))
            if args["_crash"]:
                raise Exception("Manual Crash Triggered.")

            # check if --playlist was provided
            if args["playlist"]:
                # change song args to the playlist contents
                playlist = indexlib.search_playlist(args["args"][0])
                if playlist is None:
                    MAIN.log(Warn(f"Playlist '{args['args'][0]}' not found."))
                    print(f"Playlist '{args['args'][0]}' not found.")
                    return
                songs = indexlib.get_playlist_contents(playlist)
                if songs is None:
                    MAIN.log(Warn(f"Playlist '{args['args'][0]}' is empty."))
                    print(f"Playlist '{args['args'][0]}' is empty.")
                    return
                MAIN.log(Info(f"Playlist '{args['args'][0]}' found, playing songs."))
                args["args"] = [song[2] for song in songs]

            if args["shuffle"]:
                # shuffle the songs (args.args)
                random.shuffle(args["args"])
            # convert the song names to paths & data (tuple)
            songs = [scan_library(song) for song in args["args"] if song is not None]
            # remove any None values from the list
            songs = [song for song in songs if song is not None]
            # find any lists in the song list and add them to the song list
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
                        play(song[1], song, args["loop"], args["shuffle"], config)
                    if not args["loop"]:
                        break
            except (
                KeyboardInterrupt
            ):  # catch the KeyboardInterrupt so the program can exit
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
                print(
                    f"{song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}"
                )
        case "search":
            # search for a song in the library
            songs = indexlib.search_index(config["library"], args["args"][0])
            MAIN.log(Info(f"Found {len(songs)} songs."))
            MAIN.log(
                Debug(
                    f"Songs IDs: {', '.join([str(song[0]) for song in songs]).strip()}"
                )
            )
            for song in songs:
                print(
                    f"{song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}"
                )

        case "c":
            try:
                pull_session("cmusic_background")
            except FileNotFoundError:
                MAIN.log(Warn("Background process not found."))
                print("Background process not found, is it running?")

        case "p":
            # toggle the background process
            # check if the background process is running
            tmux_check = subprocess.run(
                ["tmux", "has-session", "-t", "cmusic_background"],
                stdout=subprocess.PIPE,
            )
            if tmux_check.returncode == 0:
                # session exists, send space to the session
                subprocess.run(
                    ["tmux", "send-keys", "-t", "cmusic_background", " ", "C-m"]
                )
            else:
                print("Background process not found, is it running?")

        case "v":
            # set the volume, will automatically save to the config file (and apply to the background process)
            try:
                volume = int(args["args"][0])
                if volume > 100:
                    volume = 100
                    MAIN.log(Warn("Volume must be between 0 and 100, correcting."))
                elif volume < 0:
                    volume = 0
                    MAIN.log(Warn("Volume must be between 0 and 100, correcting."))
                with open(CONFIG_FILE, "w") as f:
                    config["volume"] = volume
                    f.write(json.dumps(config, indent=4))
                    MAIN.log(Info(f"Volume set to {volume}"))
            except ValueError:
                MAIN.log(Warn("Volume must be an integer."))
                print("Volume must be an integer.")
            except IndexError:
                MAIN.log(Warn("Volume must be provided."))
                print("Volume must be provided.")

        case "q":
            # quit the background process
            status = subprocess.run(
                ["tmux", "kill-session", "-t", "cmusic_background"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            if status.returncode != 0:
                MAIN.log(Warn("Background process not found."))
                print("Background process not found.")

        case "edit":
            # edit the song's tags
            song = scan_library(args["args"][0])
            if song is None:
                MAIN.log(Warn(f"Could not find song '{args['args'][0]}' in library."))
                print(f"Could not find song '{args['args'][0]}' in library.")
                return
            if isinstance(song, list):
                MAIN.log(Info("Multiple songs found, editing all."))
                for s in song:
                    indexlib.edit_tags(s[0])
            else:
                MAIN.log(Info("Editing song."))
                indexlib.edit_tags(song[0])

        case "info":
            # get the info of a song
            song = scan_library(args["args"][0])
            if song is None:
                MAIN.log(Warn(f"Could not find song '{args['args'][0]}' in library."))
                print(f"Could not find song '{args['args'][0]}' in library.")
                return
            if isinstance(song, list):
                MAIN.log(Info("Multiple songs found, displaying all."))
                print("-" * 30)
                for s in song:
                    print(
                        f"Title: {s[2]}\nArtist: {s[3]}\nAlbum: {s[4]}\nGenre: {s[6]}\nYear: {s[7]}"
                    )
                    print("-" * 30)
            else:
                MAIN.log(Info("Displaying song info."))
                print("-" * 30)
                print(
                    f"Title: {song[2]}\nArtist: {song[3]}\nAlbum: {song[4]}\nGenre: {song[6]}\nYear: {song[7]}"
                )
                print("-" * 30)

        case "flush":
            # print out all log messages
            are_you_sure = input(
                "Are you sure you want to flush the log, this will print all lines and clear it (can "
                "be up to 1000 lines)? (y/n): "
            )
            if are_you_sure.lower() == "y":
                MAIN.dump_messages_to_console(None)
                MAIN.wipe_messages(wipe_logfiles=True)
                print("Log flushed.")
                MAIN.log(Info("Log flushed."))
            else:
                print("Aborted.")

        case "playlist":
            # check playlist command
            match args["args"][0]:
                case "create":
                    # create a playlist
                    playlist_name = args["args"][1]
                    songs = args["args"][2:]
                    # get the songs from the library
                    songs = [scan_library(song) for song in songs]
                    # find any lists in the song list and add them to the song list
                    for song in songs:
                        if isinstance(song, list):
                            songs += song
                            songs.remove(song)
                    # remove any None values from the list
                    songs = [song for song in songs if song is not None]
                    # create the playlist
                    indexlib.create_playlist(playlist_name, songs)
                    MAIN.log(Info(f"Playlist '{playlist_name}' created."))
                    print(f"Playlist '{playlist_name}' created.")
                case "list":
                    # list all playlists
                    try:
                        playlist = indexlib.search_playlist(args["args"][1])
                        # list a specific playlist
                        playlist = indexlib.get_playlist_contents(playlist)
                        if playlist is None:
                            MAIN.log(Warn(f"Playlist '{args['args'][1]}' not found."))
                            print(f"Playlist '{args['args'][1]}' not found.")
                            return
                        MAIN.log(Info(f"Playlist '{args['args'][1]}' contents:"))
                        print(f"Playlist '{args['args'][1]}' contents:")
                        for song in playlist:
                            print(
                                f"{song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}"
                            )
                            MAIN.log(
                                Debug(
                                    f"Song: {song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}"
                                )
                            )
                    except IndexError:
                        # list all playlists
                        playlists = indexlib.list_playlists()
                        MAIN.log(Info("Playlists:"))
                        print("Playlists:")
                        for playlist in playlists:
                            print(playlist[1])
                            MAIN.log(Debug(playlist))
                case "remove":
                    # remove a song from a playlist
                    try:
                        playlist_name = args["args"][1]
                        song_name = args["args"][2]
                        playlist = indexlib.search_playlist(playlist_name)
                        songs = [scan_library(song_name) for song in args["args"][2:]]
                        # add any lists to the songs list
                        for song in songs:
                            if isinstance(song, list):
                                songs += song
                                songs.remove(song)
                        # remove any None values from the list
                        songs = [tuple(song) for song in songs if song is not None]
                        for song in songs:
                            indexlib.remove_from_playlist(playlist, song)
                    except IndexError:
                        MAIN.log(Warn("Playlist and song name must be provided."))
                        print("Playlist and song name must be provided.")
                        return
                case "add":
                    # add a song to a playlist
                    try:
                        playlist_name = args["args"][1]
                        songs = [scan_library(song) for song in args["args"][2:]]
                        # add any lists to the songs list
                        for song in songs:
                            if isinstance(song, list):
                                songs += song
                                songs.remove(song)
                        # remove any None values from the list
                        songs = [tuple(song) for song in songs if song is not None]
                        playlist = indexlib.search_playlist(playlist_name)
                        for song in songs:
                            indexlib.add_to_playlist(playlist, song)
                    except IndexError:
                        MAIN.log(Warn("Playlist and song name must be provided."))
                        print("Playlist and song name must be provided.")
                        return
                case "delete":
                    # delete a playlist
                    try:
                        playlist_name = args["args"][1]
                        playlist = indexlib.search_playlist(playlist_name)
                        indexlib.delete_playlist(playlist)
                    except IndexError:
                        MAIN.log(Warn("Playlist name must be provided."))
                        print("Playlist name must be provided.")
                        return


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
        MAIN.log(Info(f"Found song '{songname}' in library."))
        return songs[0]
    else:
        # multiple songs found, ask the user which one they want to play
        if len(songs) > 1:
            MAIN.log(
                Info(f"Found {len(songs)} songs matching '{songname}' in library.")
            )
            # ask the user which song they want to play
            questions = [
                inquirer.List(
                    "song",
                    message=f"Select the song that matches '{songname}'",
                    choices=[song[2] for song in songs] + ["^^^ All of the above ^^^"],
                )
            ]
            answers = inquirer.prompt(questions)
            if answers is not None:
                songname = answers["song"]
                MAIN.log(Info(f"User selected song '{songname}'."))
            else:
                # user cancelled
                MAIN.log(Warn("User cancelled song selection."))
                return None

            if songname == "^^^ All of the above ^^^":  # TODO: code is kinda crap, fix
                return [song for song in songs]
            for song in songs:
                if song[2] == songname:
                    MAIN.log(Info(f"User selected song '{song[2]}'."))
                    return song


def proper(time_int):
    """
    returns a proper time string (xx) from an integer

    :param time_int:
    :return:
    """
    # TODO: make this work for hours and up
    return time_int if len(str(time_int)) >= 2 else "0" + str(time_int)


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
    # ──────────────────────█──────
    # length of bar is 30 characters with a █ at the percentage
    bar_length = 30
    bar = "─" * bar_length
    bar = list(bar)
    try:
        bar[int(bar_length * percentage)] = "█"
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
    slider[
        min(max(math.floor((volume / 100) * slider_length), 0), slider_length - 1)
    ] = "○"
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


def play(
    song_path, song_data, looped, shuffle, config
):  # will error if config is not passed, idk why
    """play a song."""
    # get the song path
    if "TMUX" in os.environ:
        bg = True
    else:
        bg = False
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
    key_thread = bg_threads.KeyHandler(bg)
    try:
        # start the key press listener
        key_thread.start()
        while pygame.mixer.music.get_pos() != -1:

            # draw the interface
            interface_frame = draw_interface(tags, song_data, looped, shuffle)
            if interface_frame != last_printed_state:
                print(interface_frame)
                last_printed_state = interface_frame
            # check config for volume changes
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
                    pygame.mixer.music.set_volume(config["volume"] / 100)
            except json.JSONDecodeError:
                MAIN.log(
                    Warn(
                        "Unable to read config file, this may be due to changing the volume while the song is "
                        "playing, ignoring."
                    )
                )
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
        raise KeyboardInterrupt(
            "User shutdown Program"
        )  # re-raise the KeyboardInterrupt so the program can exit


def pull_session(session_name):
    """Pull a tmux session to the foreground."""
    # check if the session exists
    tmux_check = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if tmux_check.returncode != 0:
        MAIN.log(Warn(f"Session '{session_name}' not found."))
        raise FileNotFoundError(f"Session '{session_name}' not found.")
    # figure out the current setting for status bar
    status = (
        subprocess.run(
            ["tmux", "show", "-g", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        .stdout.decode("utf-8")
        .strip()
        .split(" ")[-1]
    )
    subprocess.run(["tmux", "set", "-g", "status", "off"], stderr=subprocess.PIPE)
    subprocess.run(["tmux", "attach", "-t", session_name], stderr=subprocess.PIPE)
    subprocess.run(["tmux", "set", "-g", "status", f"{status}"], stderr=subprocess.PIPE)
