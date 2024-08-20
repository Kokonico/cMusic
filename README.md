# cMusic
> A simple CLI music player written in Python.

## NOTICE
Although this player can play any audio file, *I do not condone piracy.* Please only use this player to play music that you own or have the rights to play. By using this player, you agree to take full responsibility for any legal consequences that may arise from your use of this player.

## Table of Contents
- [Notice](#notice)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Music Controls](#music-controls)
  - [Commands](#commands)
    - [Background Mode Commands](#background-mode-commands)
    - [Playlist Commands](#playlist-commands)

## Requirements
- Python 3.12+ & dependencies (should be installed automatically)
- poetry
- tmux

## Installation

cmusic is available on PyPI, so you can install it using pip.

```sh
pip install cmusic
```

(please make sure that your python scripts directory is in your PATH)

or you can install it from the source code.

```sh
git clone https://github.com/Kokonico/cMusic
cd cmusic
pip3.12 install .
```

<!-- not implemented yet. -->
<!--
or if you're on macOS, you can use Homebrew to install it.

```sh
brew tap Kokonico/tap
brew install cmusic
```
-->

## Usage

Cmusic currently only supports mp3 files. To use the player, you need to index the songs you want to play first.

```sh
# index a song
cmusic index <Song File>
```

example:

```sh
cmusic index "path/to/song.mp3"
```

it will walk you through the process of indexing the song.

to select options to change, use arrow keys to navigate and space to select.

to play a song, you can use the following command, the name of the song should be the same as the one you set when indexing the song.

```sh
cmusic play <Song> [--loop] [--shuffle]

```

_pssst, you can also pass multiple Songs to play them in a row._

```sh
cmusic play <Song1> <Song2> <Song3> ...
```

The player will display the current Song playing, the progress of the Song and the controls.
```
NOW PLAYING: Altars of Apostasy by Heaven Pierce Her (Ultrakill: Imperfect Hatred (Original Game Soundtrack))
─────────█────────────────────
<< || >> 01:44 / 05:37 ────○ 🔊 100% 🔁
```


if you want, you can activate background mode by adding the `--background` flag to the command.
```sh
cmusic play <Song> --background
```
it will play the Song in the background, and you can continue using the terminal.

note: if you want to return to the player, you can use `cmusic c`


### Music Controls

to control the music when it's not in the background, you can use the following keys:
- `space` to pause/play the Song.
- `s` to skip the current song
- `shift + (+)` to increase the volume.
- `shift + (-)` to decrease the volume.
- `e` to enter background mode.

### commands

- `cmusic index <Song File>` to index a Song
- `cmusic list` to list all the songs in the library.
- `cmusic play <Song>` to play a Song.
- `cmusic version` to display the version of the player.
- `cmusic search <query>` to search for Songs in the library.
- `cmusic del <Song>` to delete a song.
<!-- - `cmusic queue <Song>` to add a Song to the queue. it'll play after the one currently playing. -->

#### background mode commands

- `cmusic p` to pause/play the current Song
- `cmusic v <volume>` to change the volume of the player.
- `cmusic c` to return to the player.
- `cmusic q` to quit the player.

#### playlist commands

- `cmusic playlist create <name> <song>(s)` to create a playlist.
- `cmusic playlist add <name> <song>(s)` to add a Song to a playlist.
- `cmusic playlist remove <name> <song>(s)` to remove a Song from a playlist.
- `cmusic playlist delete <name>` to delete a playlist.
- `cmusic playlist list` to list all the playlists.
- `cmusic playlist list <name>` to list all the Songs in a playlist.
- `cmusic play <playlist name> --playlist` to play a playlist.

## Development setup

To set up the development environment, you need to have Poetry and python 3.12+ installed on your system.

```sh
git clone https://github.com/Kokonico/cMusic
cd cmusic
poetry install
```

to install the player to use it in the terminal, you can use the following command.

```sh
poetry run pip install .
```

## License

This project is licensed under the Zlib License. See the [LICENSE](LICENSE) file for details.
 
