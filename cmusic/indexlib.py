"""song indexer for cmusic"""

import re
import os
import sys
import tinytag
import sqlite3
import mutagen
import mutagen.id3
from tinytag import TinyTag

from .constants import config

import objlog
from objlog.LogMessages import Debug, Info, Warn, Error, Fatal

log = objlog.LogNode("INDEXER", log_file=os.path.join(os.path.expanduser("~"), ".cmusic", 'cmusic.log'))


def safe(filename):
    if filename is None:
        return None
    return re.sub(r'[\\/*?:"<>| ]', '_', filename)


def index_library(library_file: str):
    """index a library of songs, and store the information in a file for easier lookup"""
    if os.path.exists(os.path.join(library_file, 'index.db')):
        log.log(Warn("Library already indexed, deleting old index"))
        os.remove(os.path.join(library_file, 'index.db'))

    conn = sqlite3.connect(os.path.join(library_file, 'index.db'))
    c = conn.cursor()
    # create table to link tags to file paths
    c.execute(
        'CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, duration REAL, genre TEXT, year INTEGER)')
    conn.commit()

    # get all files in the library
    for root, _, files in os.walk(library_file):
        for file in files:
            if file.endswith('.mp3'):
                path = os.path.join(root, file)
                # get the tags of the file
                tags = tinytag.TinyTag.get(path)
                log.log(Info(f"Indexing {tags.title} by {tags.artist}"))
                # insert the tags into the database
                c.execute(
                    'INSERT INTO songs (path, title, artist, album, duration, genre, year) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (path, tags.title, tags.artist, tags.album, tags.duration, tags.genre, tags.year))
                conn.commit()
    conn.close()


def index_file(library_file: str, file: str):
    """index a single file"""
    conn = sqlite3.connect(os.path.join(library_file, 'index.db'))
    c = conn.cursor()
    # create table to link tags to file paths
    c.execute(
        'CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, path TEXT, title TEXT, artist TEXT, album TEXT, duration REAL, genre TEXT, year INTEGER)')
    conn.commit()

    # get all files in the library
    path = file
    # get the tags of the file
    tags = tinytag.TinyTag.get(path)
    log.log(Info(f"Indexing {tags.title} by {tags.artist}"))
    # insert the tags into the database
    c.execute(
        'INSERT INTO songs (path, title, artist, album, duration, genre, year) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (path, tags.title, tags.artist, tags.album, tags.duration, tags.genre, tags.year))
    conn.commit()
    conn.close()


def search_index(library_file: str, search_term: str):
    """search the index for a song"""
    conn = sqlite3.connect(os.path.join(library_file, 'index.db'))
    c = conn.cursor()
    c.execute('SELECT * FROM songs WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?',
              ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
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
    song_name = input(f"Enter the name of the song '{song_file}' (leave blank for metadata name): ")
    artist = input(f"Enter the artist of the song '{song_file}' (leave blank for metadata artist): ")
    album = input(f"Enter the album of the song '{song_file}' (leave blank for metadata album): ")
    tags = TinyTag.get(song_file)
    if song_name == "":
        song_name = tags.title if tags.title is not None else os.path.basename(song_file)
    if artist == "":
        artist = tags.artist if tags.artist is not None else "Unknown"
    if album == "":
        album = tags.album if tags.album is not 'None' else None
    # copy the file to the library
    log.log(Info(f"Copying '{song_file}' to library..."))
    with open(song_file, "rb") as f:
        new_song = os.path.join(config["library"], song_name + "." + song_file.split(".")[-1])
        with open(new_song, "wb") as f2:
            f2.write(f.read())
    # load metadata into the mp3 file (post write, because mutagen doesn't like writing to open files)
    tags = TinyTag.get(os.path.join(config["library"], song_name + "." + song_file.split(".")[-1]))
    tags.artist = artist
    tags.album = album
    # save the metadata (mutagen)
    try:
        muta = mutagen.File(new_song)
    except mutagen.mp3.HeaderNotFoundError:
        log.log(Error(f"Unable to read file '{song_name}' due to Bad Header."))
        print(f"Unable to read file '{song_name}', is it a valid mp3 file? try playing it with an external player.")
        return
    muta["TPE1"] = mutagen.id3.TPE1(encoding=3, text=[u"{}".format(artist)])
    muta["TALB"] = mutagen.id3.TALB(encoding=3, text=[u"{}".format(album)])
    muta["TIT2"] = mutagen.id3.TIT2(encoding=3, text=[u"{}".format(song_name)])

    muta.save()

    log.log(Info(f"File '{song_name}' copied to library."))
    index_file(config["library"], str(os.path.join(config["library"], song_name + "." + song_file.split(".")[-1])))
    print(f"File '{song_name}' copied to library.")


def reformat():
    """reformat all audio files in the library according to the index"""
    cleanup()  # clean up the library first (remove ghost files)
    conn = sqlite3.connect(os.path.join(config["library"], 'index.db'))
    c = conn.cursor()
    c.execute('SELECT * FROM songs')
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
        muta["TIT2"] = mutagen.id3.TIT2(encoding=3, text=[u"{}".format(song[2])])
        # set artist
        muta["TPE1"] = mutagen.id3.TPE1(encoding=3, text=[u"{}".format(song[3])])
        # set album
        muta["TALB"] = mutagen.id3.TALB(encoding=3, text=[u"{}".format(song[4])])
        muta.save()
        log.log(Info(f"File '{song[2]}' reformatted."))
        # update the index (song paths)
        c.execute("""
        UPDATE songs
        SET path = ?
        WHERE id = ?
        """, (new_path, song[0]))
        conn.commit()
    conn.close()
    log.log(Info("All songs reformatted."))

def cleanup():
    """clean up the library, ghost files, etc."""
    conn = sqlite3.connect(os.path.join(config["library"], 'index.db'))
    c = conn.cursor()
    c.execute('SELECT * FROM songs')
    songs = c.fetchall()

    for song in songs:
        try:
            with open(song[1], "rb") as f:
                pass
        except FileNotFoundError:
            log.log(Warn(f"File '{song[2]}' not found, removing from index."))
            c.execute('DELETE FROM songs WHERE id = ?', (song[0],))

    conn.commit()
    conn.close()
    log.log(Info("Library cleaned up."))
