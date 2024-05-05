"""song indexer for cmusic"""

import re
import os
import tinytag
import sqlite3
import mutagen
import mutagen.id3
from tinytag import TinyTag

import inquirer

from .constants import config

import objlog
from objlog.LogMessages import Debug, Info, Warn, Error, Fatal

log = objlog.LogNode(
    "INDEXER", log_file=os.path.join(os.path.expanduser("~"), ".cmusic", "cmusic.log")
)


def safe(filename):
    if filename is None:
        return None
    return re.sub(r'[\\/*?:"<>| ]', "_", filename)


def init_index(library_file: str):
    """initialize an index file for a library"""
    conn = sqlite3.connect(os.path.join(library_file, "index.db"))
    c = conn.cursor()
    # create table to link tags to file paths
    c.execute(
        "CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, duration REAL, genre TEXT, year INTEGER)"
    )
    conn.commit()
    # playlists (many to many)
    c.execute(
        "CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY, name TEXT)"
    )
    conn.commit()
    c.execute(
        "CREATE TABLE IF NOT EXISTS playlist_songs (playlist_id INTEGER, song_id INTEGER)"
    )
    conn.commit()
    conn.close()


def index_library(library_file: str):
    """index a library of songs, and store the information in a file for easier lookup"""
    if os.path.exists(os.path.join(library_file, "index.db")):
        log.log(Warn("Library already indexed, deleting old index"))
        os.remove(os.path.join(library_file, "index.db"))

    conn = sqlite3.connect(os.path.join(library_file, "index.db"))
    c = conn.cursor()
    # create table to link tags to file paths
    c.execute(
        "CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, duration REAL, genre TEXT, year INTEGER)"
    )
    conn.commit()

    # get all files in the library
    for root, _, files in os.walk(library_file):
        for file in files:
            if file.endswith(".mp3"):
                path = os.path.join(root, file)
                # get the tags of the file
                tags = tinytag.TinyTag.get(path)
                log.log(Info(f"Indexing {tags.title} by {tags.artist}"))
                # insert the tags into the database
                c.execute(
                    "INSERT INTO songs (path, title, artist, album, duration, genre, year) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        path,
                        tags.title,
                        tags.artist,
                        tags.album,
                        tags.duration,
                        tags.genre,
                        tags.year,
                    ),
                )
                conn.commit()
    conn.close()


def index_file(library_file: str, file: str):
    """index a single file"""
    conn = sqlite3.connect(os.path.join(library_file, "index.db"))
    c = conn.cursor()
    # create table to link tags to file paths
    c.execute(
        "CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, duration REAL, genre TEXT, year INTEGER)"
    )
    conn.commit()

    # get all files in the library
    path = file
    # get the tags of the file
    tags = tinytag.TinyTag.get(path)
    log.log(Info(f"Indexing {tags.title} by {tags.artist}"))
    # insert the tags into the database
    c.execute(
        "INSERT INTO songs (path, title, artist, album, duration, genre, year) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            path,
            tags.title,
            tags.artist,
            tags.album,
            tags.duration,
            tags.genre,
            tags.year,
        ),
    )
    conn.commit()
    conn.close()


def search_index(library_file: str, search_term: str):
    """search the index for a song"""
    conn = sqlite3.connect(os.path.join(library_file, "index.db"))
    c = conn.cursor()
    c.execute(
        "SELECT * FROM songs WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? OR genre LIKE ? OR year LIKE ?",
        (
            "%" + search_term + "%",
            "%" + search_term + "%",
            "%" + search_term + "%",
            "%" + search_term + "%",
            "%" + search_term + "%",
        ),
    )
    return c.fetchall()


def index(song_file):
    if not os.path.exists(song_file):
        log.log(Warn(f"File '{song_file}' not found."))
        print("File not found.")
        return
    if not song_file.endswith(".mp3"):
        log.log(Warn("Non mp3 files have not been tested, here be dragons."))
        print("Non mp3 files have not been tested, here be dragons.")
    # get the song name
    tags = TinyTag.get(song_file)
    song_name = tags.title
    artist = tags.artist
    album = tags.album
    year = tags.year
    genre = tags.genre
    inquirer_questions = [
        inquirer.List(
            "what_to_edit",
            message="What field would you like to edit?",
            choices=[
                f"Song Name ({song_name})",
                f"Artist ({artist})",
                f"Album ({album})",
                f"Year ({year})",
                f"Genre ({genre})",
                f"Stop Editing",
                "Cancel",
            ],
        ),
    ]
    stop = False
    while not stop:
        what_to_edit = inquirer.prompt(inquirer_questions)["what_to_edit"]
        if what_to_edit == f"Song Name ({song_name})":
            song_name = input(
                f"Enter the song name (leave blank to keep '{tags.title}'): "
            )
            if song_name == "":
                song_name = tags.title
        elif what_to_edit == f"Artist ({artist})":
            artist = input(f"Enter the artist (leave blank to keep '{tags.artist}'): ")
            if artist == "":
                artist = tags.artist
        elif what_to_edit == f"Album ({album})":
            album = input(f"Enter the album (leave blank to keep '{tags.album}'): ")
            if album == "":
                album = tags.album
        elif what_to_edit == f"Year ({year})":
            year = input(f"Enter the year (leave blank to keep '{tags.year}'): ")
            if year == "":
                year = tags.year
        elif what_to_edit == f"Genre ({genre})":
            genre = input(f"Enter the genre (leave blank to keep '{tags.genre}'): ")
            if genre == "":
                genre = tags.genre
        elif what_to_edit == "Stop Editing":
            stop = True
        elif what_to_edit == "Cancel":
            log.log(Info("User cancelled song editing."))
            print("Not indexing song.")
            return
        # update the questions
        log.log(Debug(f"Values: {song_name}, {artist}, {album}, {year}, {genre}"))
        inquirer_questions = [
            inquirer.List(
                "what_to_edit",
                message="What field would you like to edit?",
                choices=[
                    f"Song Name ({song_name})",
                    f"Artist ({artist})",
                    f"Album ({album})",
                    f"Year ({year})",
                    f"Genre ({genre})",
                    f"Stop Editing",
                ],
            ),
        ]
    # copy the file to the library
    log.log(Info(f"Copying '{song_file}' to library..."))
    with open(song_file, "rb") as f:
        new_song = os.path.join(
            config["library"], song_name + "." + song_file.split(".")[-1]
        )
        with open(new_song, "wb") as f2:
            f2.write(f.read())
    # load metadata into the mp3 file (post write, because mutagen doesn't like writing to open files)
    tags = TinyTag.get(
        os.path.join(config["library"], song_name + "." + song_file.split(".")[-1])
    )
    tags.artist = artist
    tags.album = album
    # save the metadata (mutagen)
    try:
        muta = mutagen.File(new_song)
    except mutagen.mp3.HeaderNotFoundError:
        log.log(Error(f"Unable to read file '{song_name}' due to Bad Header."))
        print(
            f"Unable to read file '{song_name}', is it a valid mp3 file? try playing it with an external player."
        )
        return
    muta["TPE1"] = mutagen.id3.TPE1(encoding=3, text=["{}".format(artist)])
    muta["TALB"] = mutagen.id3.TALB(encoding=3, text=["{}".format(album)])
    muta["TIT2"] = mutagen.id3.TIT2(encoding=3, text=["{}".format(song_name)])
    muta["TDRC"] = mutagen.id3.TDRC(encoding=3, text=["{}".format(tags.year)])
    muta["TCON"] = mutagen.id3.TCON(encoding=3, text=["{}".format(tags.genre)])

    log.log(Debug(f"Values: {artist}, {album}, {song_name}, {year}, {genre}"))

    muta.save()

    log.log(Info(f"File '{song_name}' copied to library."))
    index_file(
        config["library"],
        str(
            os.path.join(config["library"], song_name + "." + song_file.split(".")[-1])
        ),
    )
    print(f"File '{song_name}' copied to library.")


def reformat():
    """reformat all audio files in the library according to the index"""
    cleanup()  # clean up the library first (remove ghost files)
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM songs")
    songs = c.fetchall()

    for song in songs:
        try:
            new_name = f"{safe(song[2])}.mp3"
        except TypeError:
            # no song name, get from file
            tags = TinyTag.get(song[1])
            if tags.title is None:
                # no title, use file name
                new_name = os.path.basename(song[1])
            else:
                new_name = f"{safe(tags.title)}.mp3"

        new_path = os.path.join(config["library"], new_name)
        log.log(Info(f"Reformatting '{song[2]}'..."))
        # rename the file
        os.rename(song[1], new_path)
        muta = mutagen.File(new_path)
        with open("debug.txt", "w") as f:
            f.write(str(song))
        # set title
        muta["TIT2"] = mutagen.id3.TIT2(encoding=3, text=["{}".format(song[2])])
        # set artist
        muta["TPE1"] = mutagen.id3.TPE1(encoding=3, text=["{}".format(song[3])])
        # set album
        muta["TALB"] = mutagen.id3.TALB(encoding=3, text=["{}".format(song[4])])
        # set year
        muta["TDRC"] = mutagen.id3.TDRC(encoding=3, text=["{}".format(song[7])])
        # set genre
        muta["TCON"] = mutagen.id3.TCON(encoding=3, text=["{}".format(song[6])])
        muta.save()
        log.log(Info(f"File '{song[2]}' reformatted."))
        # update the index (song paths)
        c.execute(
            """
        UPDATE songs
        SET path = ?
        WHERE id = ?
        """,
            (new_path, song[0]),
        )
        conn.commit()
    conn.close()
    log.log(Info("All songs reformatted."))


def cleanup():
    """clean up the library, ghost files, etc."""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM songs")
    songs = c.fetchall()

    for song in songs:
        try:
            with open(song[1], "rb") as f:
                pass
        except FileNotFoundError:
            log.log(Warn(f"File '{song[2]}' not found, removing from index."))
            c.execute("DELETE FROM songs WHERE id = ?", (song[0],))

    # remove any files that are not in the index
    for root, _, files in os.walk(config["library"]):
        for file in files:
            if file.endswith(".mp3"):
                path = os.path.join(root, file)
                c.execute("SELECT * FROM songs WHERE path = ?", (path,))
                if c.fetchone() is None:
                    log.log(Warn(f"File '{path}' not in index, removing."))
                    os.remove(path)
            elif not file.endswith(".db"):
                log.log(Warn(f"File '{file}' not an mp3 or database file, removing."))
                os.remove(os.path.join(root, file))

    conn.commit()
    conn.close()
    log.log(Info("Library cleaned up."))


def edit_tags(id: int):
    """edit the tags of a song"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM songs WHERE id = ?", (id,))
    song = c.fetchone()
    new_title, new_artist, new_album, new_year, new_genre = (
        song[2],
        song[3],
        song[4],
        song[7],
        song[6],
    )  # get the current values
    if song is None:
        log.log(Warn(f"Song with id '{id}' not found."))
        print("Song not found.")
        return
    print(f"Editing song '{song[2]}'")
    print("Leave blank to keep the current value.")
    stop = False
    inquirer_edit_options = [
        inquirer.List(
            "edit_option",
            message="What would you like to edit?",
            choices=["Title", "Artist", "Album", "Year", "Genre", "Stop Editing"],
        )
    ]
    while not stop:
        edit_option = inquirer.prompt(inquirer_edit_options)["edit_option"]
        if edit_option == "Title":
            new_title = input(
                f"Enter the new title for '{song[2]}' (leave blank to keep '{song[2]}'): "
            )
            if new_title == "":
                new_title = song[2]
        elif edit_option == "Artist":
            new_artist = input(
                f"Enter the new artist for '{song[2]}' (leave blank to keep '{song[3]}'): "
            )
            if new_artist == "":
                new_artist = song[3]
        elif edit_option == "Album":
            new_album = input(
                f"Enter the new album for '{song[2]}' (leave blank to keep '{song[4]}'): "
            )
            if new_album == "":
                new_album = song[4]
        elif edit_option == "Year":
            new_year = input(
                f"Enter the new year for '{song[2]}' (leave blank to keep '{song[7]}'): "
            )
            if new_year == "":
                new_year = song[7]
        elif edit_option == "Genre":
            new_genre = input(
                f"Enter the new genre for '{song[2]}' (leave blank to keep '{song[6]}'): "
            )
            if new_genre == "":
                new_genre = song[6]
        elif edit_option == "Stop Editing":
            stop = True
    log.log(
        Debug(
            f"New values: {new_title}, {new_artist}, {new_album}, {new_year}, {new_genre}"
        )
    )
    # update the index
    c.execute(
        """
    UPDATE songs
    SET title = ?, artist = ?, album = ?, year = ?, genre = ?
    WHERE id = ?
    """,
        (new_title, new_artist, new_album, new_year, new_genre, id),
    )
    conn.commit()
    conn.close()
    log.log(Info(f"Song '{song[2]}' edited."))
    print(f"Song '{song[2]}' edited.")
    reformat()  # reformat the library to apply changes


def create_playlist(name: str, songs: list):
    """create a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM playlists WHERE name = ?", (name,))
    if c.fetchone() is not None:
        log.log(Warn(f"Playlist '{name}' already exists."))
        print(f"Playlist '{name}' already exists.")
        return
    c.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
    conn.commit()
    c.execute("SELECT * FROM playlists WHERE name = ?", (name,))
    playlist_id = c.fetchone()[0]
    for song in songs:
        c.execute(
            "INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
            (playlist_id, song[0]),
        )
        conn.commit()
    conn.close()
    log.log(Info(f"Playlist '{name}' created."))


def delete_playlist(playlist: tuple):
    """delete a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("DELETE FROM playlists WHERE id = ?", (playlist[0],))
    conn.commit()
    # delete all songs in the playlist
    c.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist[0],))
    conn.close()
    log.log(Info(f"Playlist '{playlist[1]}' deleted."))


def list_playlists():
    """list all playlists"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM playlists")
    playlists = c.fetchall()
    conn.close()
    return playlists


def list_playlist(playlist: tuple):
    """list all songs in a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM playlist_songs WHERE playlist_id = ?", (playlist[0],))
    songs = c.fetchall()
    song_data = []
    for song in songs:
        c.execute("SELECT * FROM songs WHERE id = ?", (song[1],))
        song_info = c.fetchone()
        song_data.append(song_info)
    conn.close()
    return song_data


def add_to_playlist(playlist: tuple, song: tuple):
    """add a song to a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute(
        "INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
        (playlist[0], song[0]),
    )
    conn.commit()
    conn.close()
    log.log(Info(f"Song '{song}' added to playlist '{playlist[1]}'."))


def remove_from_playlist(playlist: tuple, song: tuple):
    """remove a song from a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute(
        "DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
        (playlist[0], song[0]),
    )
    conn.commit()
    conn.close()
    log.log(Info(f"Song '{song}' removed from playlist '{playlist[1]}'."))


def edit_playlist_name(playlist: tuple, new_name: str):
    """edit a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist[0]))
    conn.commit()
    conn.close()
    log.log(Info(f"Playlist '{playlist[1]}' edited to '{new_name}'."))


def get_playlist_contents(playlist: tuple):
    """get the contents of a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    if playlist is None:
        log.log(Warn(f"Playlist not found."))
        print(f"Playlist not found.")
        return
    c.execute("SELECT * FROM playlist_songs WHERE playlist_id = ?", (playlist[0],))
    songs = c.fetchall()
    song_data = []
    for song in songs:
        c.execute("SELECT * FROM songs WHERE id = ?", (song[1],))
        song_info = c.fetchone()
        song_data.append(song_info)
    conn.close()
    return song_data


def search_playlist(name: str):
    """search for the data of a playlist"""
    conn = sqlite3.connect(os.path.join(config["library"], "index.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM playlists WHERE name LIKE ?", (name,))
    playlist = c.fetchall()
    conn.close()
    # if multiple playlists, ask the user to choose
    if len(playlist) > 1:
        playlists = []
        for p in playlist:
            playlists.append(p[1])
        inquirer_questions = [
            inquirer.List(
                "playlist",
                message="Which playlist would you like to choose?",
                choices=playlists,
            )
        ]
        playlist = inquirer.prompt(inquirer_questions)["playlist"]
        return playlist
    elif len(playlist) == 0:
        log.log(Warn(f"Playlist '{name}' not found."))
        print(f"Playlist '{name}' not found.")
        return
    else:
        return playlist[0]
