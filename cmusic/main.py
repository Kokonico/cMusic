"""main internals for cmusic"""

__version__ = "2.0.0"

from .indexlib import index

extra = "Stable"

# VIOLENCE /// CLIMAX
# ...Like Antennas To Heaven

# this is the main file for cMusic, it contains the main function that is called when the program is run.
# make sure to add any new commands to the case statement in the main function.

import os
import subprocess

# local package imports
from . import indexlib
from . import bg_threads
from .constants import MAIN, config, CONFIG_FILE, LIBRARY, QUEUE_FILE, PLAYBACK_CONFIG_FILE, Song

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
                    exit(0)
                subprocess.run(
                    ["tmux", "detach", "-t", "cmusic_background"],
                    stderr=subprocess.PIPE,
                )

                if not background:
                    MAIN.log(Info("Pulling session to foreground."))
                    pull_session("cmusic_background")
                MAIN.log(Info("Background process started, peace out."))
                exit(0)
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
                    exit(1)
                songs = indexlib.get_playlist_contents(playlist)
                if songs is None:
                    MAIN.log(Warn(f"Playlist '{args['args'][0]}' is empty."))
                    print(f"Playlist '{args['args'][0]}' is empty.")
                    exit(1)
                MAIN.log(Info(f"Playlist '{args['args'][0]}' found, playing songs."))
                args["args"] = [song[2] for song in songs]

            # convert the song names to paths and data (tuple)
            songs = [scan_library(song) for song in args["args"] if song is not None]
            # remove any None values from the list
            songs = [song for song in songs if song is not None]
            # find any lists in the song list and add them to the song list
            for song in songs:
                if isinstance(song, list):
                    songs += song
                    songs.remove(song)

            if args["shuffle"]:
                random.shuffle(songs)

            # play the songs
            if not songs:
                MAIN.log(Warn("No songs found to play."))
                os.system("clear")
                print("No songs found to play.")
                input("Press enter to continue.")
            else:
                # load songs into queue
                exportable_songs = [song.export() for song in songs]
                with open(QUEUE_FILE, "w+") as f:
                    MAIN.log(Debug(songs))
                    json.dump(exportable_songs, f)
                try:
                    # TODO: make more readable
                    conf_playback = {
                        "loop": args["loop"],
                        "shuffle": args["shuffle"],
                    }
                    # write the playback config to the file
                    with open(PLAYBACK_CONFIG_FILE, "w") as f:
                        f.write(json.dumps(conf_playback, indent=4))
                    while True:  # we want to loop through the songs indefinitely (unless loop is set to False)
                        with open(QUEUE_FILE) as f:
                            songs = json.load(f)
                            songs = [Song(song["id"], song["path"], song["title"], song["artist"], song["album"], song["duration"], song["genre"], song["year"]) for song in songs]
                            MAIN.log(Debug(songs))
                        for song in songs:
                            play(song.path, song, conf_playback["loop"], conf_playback["shuffle"], config)
                            conf_playback = json.load(open(PLAYBACK_CONFIG_FILE))  # reload the playback config
                            if not conf_playback["loop"]:
                                songs.remove(song)
                            with open(QUEUE_FILE) as f:
                                new = json.load(f)
                                for stored in new:
                                    if stored == song.export():
                                        new.remove(stored)
                                        # if loop is on, add the song back to the queue at the end
                                        if conf_playback["loop"]:
                                            new.append(song.export())
                                with open(QUEUE_FILE, "w") as f:
                                    json.dump(new, f)
                                break

                        if not conf_playback["loop"] and len(new) <= 0:
                            break
                except (
                        KeyboardInterrupt
                ):  # catch the KeyboardInterrupt so the program can exit
                    MAIN.log(Info("User shutdown Program"))
                    print("User shutdown Program")
                    exit(0)

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
            print("\n".join([str(song) for song in songs]))
        case "search":
            # search for a song in the library
            songs = indexlib.search_index(config["library"], args["args"][0])
            MAIN.log(Info(f"Found {len(songs)} songs."))
            MAIN.log(
                Debug(
                    f"Songs IDs: {', '.join([str(song.id) for song in songs]).strip()}"
                )
            )
            print("\n".join([str(song) for song in songs]))
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
                    indexlib.edit_tags(s.path)
            else:
                MAIN.log(Info("Editing song."))
                indexlib.edit_tags(song.path)

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
                        f"Title: {s.title}\nArtist: {s.artist}\nAlbum: {s.album}\nGenre: {s.genre}\nYear: {s.year}"
                    )
                    print("-" * 30)
            else:
                MAIN.log(Info("Displaying song info."))
                print("-" * 30)
                print(
                    f"Title: {song.title}\nArtist: {song.artist}\nAlbum: {song.album}\nGenre: {song.genre}\nYear: {song.year}"
                )
                print("-" * 30)

        case "flush":
            # print out all log messages
            are_you_sure = input(
                "Are you sure you want to flush the log, this will print all lines and clear it (can "
                "be up to 1000 lines)? (y/n): "
            )
            if are_you_sure.lower() == "y":
                with open(MAIN.log_file, "r") as f:
                    for line in f.readlines():
                        print(line.strip())
                MAIN.wipe_messages(wipe_logfiles=True)
                print("Log flushed.")
                MAIN.log(Info("Log flushed."))
            else:
                print("Aborted.")

        case "playlist":
            # check playlist command
            match args["playlist_command"]:
                case "create":
                    # create a playlist
                    playlist_name = args["args"][0]
                    songs = args["args"][1:]
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
                        playlist = indexlib.search_playlist(args["args"][0])
                        # list a specific playlist
                        playlist = indexlib.get_playlist_contents(playlist)
                        if playlist is None:
                            MAIN.log(Warn(f"Playlist '{args['args'][0]}' not found."))
                            print(f"Playlist '{args['args'][0]}' not found.")
                            return
                        MAIN.log(Info(f"Playlist '{args['args'][0]}' contents:"))
                        print(f"Playlist '{args['args'][0]}' contents:")
                        for song in playlist:
                            print(
                                f"{song.title} by {song.artist} {f'({song.album})' if song.album not in [None, 'None'] else ''}"
                            )
                            MAIN.log(
                                Debug(
                                    f"{song.title} by {song.artist} {f'({song.album})' if song.album not in [None, 'None'] else ''}"
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
                        playlist_name = args["args"][0]
                        song_name = args["args"][1]
                        playlist = indexlib.search_playlist(playlist_name)
                        songs = [scan_library(song_name) for song in args["args"][2:]]
                        # add any lists to the song list
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
                        playlist_name = args["args"][0]
                        songs = [scan_library(song) for song in args["args"][1:]]
                        # add any lists to the song list
                        for song in songs:
                            if isinstance(song, list):
                                songs += song
                                songs.remove(song)
                        # remove any None values from the list
                        songs = [tuple(song) for song in songs if song is not None]
                        if songs == []:
                            MAIN.log(Warn("No songs found to add."))
                            print("No songs found to add.")
                            return
                        playlist = indexlib.search_playlist(playlist_name)
                        for song in songs:
                            indexlib.add_to_playlist(playlist, song)
                            print(f"added {song[2]} to {playlist_name}")
                    except IndexError:
                        MAIN.log(Warn("Playlist and song name must be provided."))
                        print("Playlist and song name must be provided.")
                        return
                case "delete":
                    # delete a playlist
                    try:
                        playlist_name = args["args"][0]
                        playlist = indexlib.search_playlist(playlist_name)
                        if playlist:
                            indexlib.delete_playlist(playlist)
                        else:
                            MAIN.log(Warn(f"Playlist '{playlist_name}' not found."))
                    except IndexError:
                        MAIN.log(Warn("Playlist name must be provided."))
                        print("Playlist name must be provided.")
                        return
        case "queue":
            # queue a song to play after
            songs = [scan_library(song) for song in args["args"]]
            songs = [song for song in songs if song is not None]
            for song in songs:

                if isinstance(song, list):
                    songs += song
                    songs.remove(song)
            songs = [list(song) for song in songs]
            with open(QUEUE_FILE, "r") as f:
                current = json.load(f)
            with open(QUEUE_FILE, "w") as f:
                for song in songs:
                    current.append(song)
                json.dump(current, f)
            MAIN.log(Info(f"Queued {len(songs)} songs."))
            for song in songs:
                print(
                    f"Queued {song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}"
                )


        case "del":
            # delete a song from the library
            try:
                song = scan_library(args["args"][0])
            except IndexError:
                MAIN.log(Warn("Song name must be provided."))
                print("Song name must be provided.")
                return
            if song is None:
                MAIN.log(Warn(f"Could not find song '{args['args'][0]}' in library."))
                print(f"Could not find song '{args['args'][0]}' in library.")
                return
            if isinstance(song, list):
                print("Are you sure you want to delete the following songs?")
                for s in song:
                    print(
                        f"{s[2]} by {s[3]} {f'({s[4]})' if s[4] not in [None, 'None'] else ''}"
                    )
                are_you_sure = input("y/n: ")
                if are_you_sure.lower() == "y":
                    MAIN.log(Info("Multiple songs found, deleting all."))
                    for s in song:
                        indexlib.delete_song(s)
                else:
                    print("Aborted.")
                    return
            else:
                print(
                    f"Are you sure you want to delete '{song[2]} by {song[3]} {f'({song[4]})' if song[4] not in [None, 'None'] else ''}'?"
                )
                are_you_sure = input("y/n: ")
                if are_you_sure.lower() == "y":
                    MAIN.log(Info("Deleting song."))
                    indexlib.delete_song(song)


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
                    choices=[song.title for song in songs] + ["^^^ All of the above ^^^"],
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
                if song.title == songname:
                    MAIN.log(Info(f"User selected song '{song.title}'."))
                    return song


def proper(time_int):
    """
    returns a proper time string (xx) from an integer

    :param time_int:
    :return:
    """
    # TODO: make this work for hours and up
    return time_int if len(str(time_int)) >= 2 else "0" + str(time_int)


def draw_interface(tags, song_data, looped, shuffle, lyrics: list | None = None):
    """draw the music player interface once."""
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
    if lyrics is not None:
        current_lyric = indexlib.get_lyric(lyrics, elapsed)
    else:
        current_lyric = None
    final_playing = f"NOW PLAYING: {song_data.title if song_data.title is not None else tags.title if tags.title is not None else song_data.path.split('/')[-1].split('.')[0]} by {song_data.artist if song_data.artist is not None else tags.artist} {f'({song_data.album})' if song_data.album not in ['None', None] else f'({tags.album})' if tags.album not in ['None', None] else ''}"
    double_newline = "\n\n"  # used for compatibility with python 3.11 and under
    new_state = f"\r{final_playing}\n{final_bar}\n<< {state} >> {proper(int(elapsed_minutes))}:{proper(int(elapsed_seconds))} / {proper(int(duration_minutes))}:{proper(int(duration_seconds))} {final_slider} {'🔁' if looped else ''}{'🔀' if shuffle else ''}{f'{double_newline}{current_lyric}' if current_lyric and current_lyric != '' else ''}"
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
        MAIN.log(FileNotFoundError(f"Could not find song '{song_data[2]}' in library."))
        raise FileNotFoundError(f"Could not find song '{song_data[2]}' in library.")
    # play the song
    MAIN.log(Info(f"Playing song '{song_path}'..."))
    tags = TinyTag.get(song_path)
    pygame.mixer.init()
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.set_volume(config["volume"] / 100)
    pygame.mixer.music.play()
    key_thread = bg_threads.KeyHandler(bg)
    lyrics = indexlib.grab_sylt_lyrics(song_data)
    try:
        # start the key press listener
        key_thread.start()
        while pygame.mixer.music.get_pos() != -1:
            # grab playback info
            with open(PLAYBACK_CONFIG_FILE) as f:
                playback_config = json.load(f)
                looped = playback_config["loop"]
                shuffle = playback_config["shuffle"]
            # draw the interface
            interface_frame = draw_interface(tags, song_data, looped, shuffle, lyrics)
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
    # reset the status bar
    subprocess.run(["tmux", "set", "-g", "status", f"{status}"], stderr=subprocess.PIPE)

