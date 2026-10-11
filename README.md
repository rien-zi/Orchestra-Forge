# Orchestra Forge

A minimal Python toolkit for composition JSON → MIDI → WAV, with **Audiolizer**, a local visual instrument playground. It is a deterministic music tool, not a trained AI model. Python runtime code uses only the standard library; FluidSynth and a separately obtained SoundFont provide audio.

## Setup on macOS

Requires Python 3.10+ and FluidSynth on PATH.

```sh
brew install python fluid-synth
./setup.sh
fluidsynth --version
```

`setup.sh` creates this checkout's `.venv` and installs the package. Setuptools is a build dependency; there are no Python runtime dependencies. To update after pulling changes, rerun setup. Use `PYTHON=/path/to/python3 ./setup.sh` to select a Python installation.

Obtain a licensed General MIDI `.sf2` SoundFont; [GeneralUser GS](https://www.schristiancollins.com/generaluser) is one option. Put it in the ignored `soundfonts/` folder or specify an absolute path. SoundFonts, generated audio and game compositions are not bundled in this public repository.

## Audiolizer

```sh
export ORCHESTRA_FORGE_SOUNDFONT="/absolute/path/to/your.sf2"
./start.sh
```

The browser opens `http://127.0.0.1:8765`. Keep the terminal running; Ctrl+C stops the server. Add `--port 8766` if needed, `--no-open` to skip opening a browser, or `--soundfont /path/to/library.sf2` to override the environment variable. Without either override, the default is `soundfonts/GeneralUser GS v1.471.sf2` relative to the current directory.

Select among 128 General MIDI program names, click a piano key, and adjust pitch, touch, duration and listening volume. Audition one note, a major chord or a short major-key phrase. **Copy settings** gives the exact instrument, MIDI pitch, velocity and duration to share. Middle C is C4 / MIDI 60; tuning uses A4 = 440 Hz.

Preview audio comes from actual FluidSynth rendering. Temporary MIDI/WAV files are deleted after rendering; a small in-memory cache disappears when the server stops. The server binds only to loopback, uses no external web assets, performs no uploads, and has no routes that edit compositions. It is a local development tool, not a hosted production service. Note release/reverb can extend beyond the requested duration. Preview gain and listening volume differ from a final music mix. No microphone input or pitch detection is included.

The installed command is `orchestra-forge-audiolizer`; `python -m orchestra_forge.audiolizer` works too.

## CLI example

```sh
.venv/bin/orchestra-forge demo --composition examples/demo.json --midi samples/demo.mid --output samples/demo.wav --soundfont /path/to/library.sf2
.venv/bin/orchestra-forge compose --composition examples/demo.json --output samples/demo.mid
.venv/bin/orchestra-forge render --midi samples/demo.mid --output samples/demo.wav --soundfont /path/to/library.sf2
```

The public example is a generic six-second strings-and-harp demonstration. `examples/` contains no project-specific music. Commands use explicit paths and work from any directory after installation.

## Composition format

See `examples/demo.json`:

- `title`: track title.
- `bpm`: quarter notes per minute.
- `beats`: duration in quarter-note beats, including written silence.
- Optional `time_signature`: `[numerator, denominator]`, default `[4, 4]`; `[6, 8]` is supported. The BPM/beat units stay quarter notes regardless of meter.
- `parts`: tracks with `name`, zero-based GM `program` (0–127), and unique zero-based `channel` (0–15, excluding percussion channel 9).
- Each note is `[start_beat, duration_beats, MIDI_pitch, velocity]`; pitch 0–127, velocity 1–127.

## What is where

| File or folder | Purpose |
| --- | --- |
| `orchestra_forge/composition.py` | Immutable score data and validated JSON loading |
| `orchestra_forge/midi.py` | MIDI type-1 writer, tempo, meter and UTF-8 labels |
| `orchestra_forge/cli.py` | Compose, render and demo commands |
| `orchestra_forge/audiolizer.py` | Local preview server and instrument catalogue |
| `orchestra_forge/web/` | Packaged Audiolizer HTML, CSS and JavaScript |
| `examples/` | Generic, public demonstration score |
| `tests/` | Standard-library checks |
| `setup.sh` / `start.sh` | Create/update this project's environment / launch Audiolizer |
| `pyproject.toml` | Package version, build dependency, entry points and web assets |

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Keep game music private

Store game compositions, audio, arrangement logic and approval records **outside this public checkout**, in a separately controlled private project. This reusable tool never requires publishing input music. Audio, MIDI, SoundFonts, virtual environments and a `private/` folder are ignored here as a secondary safeguard. `.gitignore` does not protect previously tracked files or arbitrary JSON; review staged files before publishing.

## Other systems

The Python package is portable. On Linux, install Python/venv and FluidSynth using your distribution's package manager, then use the same scripts. On Windows, install Python 3.10+, FluidSynth on PATH and your SoundFont, then run:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\orchestra-forge-audiolizer --soundfont C:\path\library.sf2
```

The shell launchers target macOS/Linux. These other-system instructions have not been exercised on those systems.

## Licensing and limitations

Source and generic example are MIT licensed (`LICENSE`). Rights to your input melodies and instrument samples are separate. [FluidSynth](https://www.fluidsynth.org/) is separately installed under LGPL; its license does not license a SoundFont. [GeneralUser GS v1.471's license](https://github.com/planet-s/generaluser-gs/blob/master/LICENSE.txt) permits commercial recordings but notes incomplete sample provenance. Review exact versions and retain their terms. Redistribution of libraries or a synthesizer differs from distributing rendered audio.

One fixed tempo and meter per composition; melodic GM instruments only. No adaptive arrangement, stems or loudness mastering. Raw WAVs include release/reverb tails, so game loops need deliberate tail handling and listening. Instrument realism depends on the chosen SoundFont.
