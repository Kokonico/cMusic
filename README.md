# cMusic
> A simple CLI music player written in Python.

PS: it's recommended to use the GitHub monaspace font(s) with ligatures enabled to use the player, but it's not required.

Also, there's a bug in pygame's mixer that causes the music to do strange things when paused for an extended period of time, so I recommend not pausing the music for too long (12 hours or more). I can't really do anything about it, so you'll have to deal with it.

## NOTICE
Although this player can play any audio file, *I do not condone piracy.* Please only use this player to play music that you own or have the rights to play. By using this player, you agree to take full responsibility for any legal consequences that may arise from your use of this player.

## Installation

cmusic is available on PyPI, so you can install it using pip.

```sh
pip install cmusic
```

or you can install it from the source code.

```sh
git clone
cd cmusic
pip install .
```

<!-- also not implemented yet. -->
<!--
or if you're on macOS, you can use Homebrew to install it.

```sh
brew tap Kokonico/tap
brew install cmusic
```
-->

## Usage

```sh
# play a Song (must be in the current directory, you can ignore file extensions)
cmusic play <Song> [--loop] [--shuffle]

```

pssst, you can also pass multiple Songs to play them in a row._

```sh
cmusic play <Song1> <Song2> <Song3> ...
```

The player will display the current Song playing, the progress of the Song and the controls.
```
NOW PLAYING: Altars of Apostasy by Heaven Pierce Her (Ultrakill: Imperfect Hatred (Original Game Soundtrack))
─────────⬤️────────────────────
<< || >> 01:44 / 05:37 ────○ 🔊 100% 🔁
```

<!--
if you want, you can activate background mode by adding the `--background` flag to the command.
```sh
cmusic play <Song> --background
```
it will play the Song in the background, and you can continue using the terminal.

note: if you want to return to the player, you can use `cmusic` without any arguments.
-->

### Music Controls

to control the music when it's not in the background, you can use the following keys:
- `space` to pause/play the Song.
- `q` to quit the player.
- `shift + (+)` to increase the volume.
- `shift + (-)` to decrease the volume.

### commands

- `cmusic list` to list all the songs in the library.
- `cmusic play <Song>` to play a Song.
- `cmusic version` to display the version of the player.
- `cmusic search <query>` to search for Songs in the library.

<!-- comment this out for now until I implement it. -->
<!--
#### background mode commands

- `cmusic toggle` to pause/play the current Song
- `cmusic next` to play the next Song.
- `cmusic prev` to play the previous Song.
- `cmusic restart` to restart the current Song.
- `cmusic seek <time>` to seek the Song to a specific time.
- `cmusic volume <volume>` to change the volume of the player.
-->

## License

This project is licensed under the Zlib License. See the [LICENSE](LICENSE) file for details.
 
