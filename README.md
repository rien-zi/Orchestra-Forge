# Orchestra Forge

A minimal Python CLI for orchestral composition data → MIDI → WAV. This is a deterministic music tool, not a trained AI model. Python uses only the standard library. FluidSynth and a separately obtained SoundFont provide instrument audio.

## macOS setup

Requires Python 3.10 or newer.

```sh
brew install python fluid-synth
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
fluidsynth --version
orchestra-forge --help
```

Installation uses setuptools as a build dependency; there are no Python runtime dependencies. For source development use `python -m pip install -e .`, or run `python -m orchestra_forge` from the repository root. On Intel Macs, Homebrew may warn about platform support or build from source; diagnose any actual installation error separately.

Obtain a General MIDI `.sf2` SoundFont from a source whose licensing fits your release. [GeneralUser GS by S. Christian Collins](https://www.schristiancollins.com/generaluser) is one option. SoundFonts and generated audio are not bundled or committed.

```sh
export ORCHESTRA_FORGE_SOUNDFONT="/absolute/path/to/your.sf2"
orchestra-forge demo --composition examples/demo.json --midi samples/demo.mid --output samples/demo.wav
```

The public example is a six-second strings-and-harp demonstration. Commands use explicit paths and work from any directory after installation. `--soundfont` overrides the environment variable.

## Keep game music private

Keep project-specific compositions and exports in a sibling directory **outside this repository**. For example:

```text
Orchestra-Forge/          # public tool and generic example
Orchestra-Forge-Private/  # private composition JSON, MIDI, WAV, notes
```

```sh
orchestra-forge demo \
  --composition ../Orchestra-Forge-Private/compositions/my_cue.json \
  --midi ../Orchestra-Forge-Private/audio/my_cue.mid \
  --output ../Orchestra-Forge-Private/audio/my_cue.wav
```

The CLI reads local files; it does not upload them. The public repository should contain only reusable code, documentation, tests, and the generic example. MIDI, audio, SoundFonts, and a `private/` directory are also ignored as a secondary safeguard. `.gitignore` does not protect previously tracked files or arbitrary JSON files: keep private compositions outside the checkout and review staged files before every push. Back up the private folder separately; this project does not provide encrypted storage or private remote backups.

## Composition format

See `examples/demo.json`. Fields:

- `title`: track title.
- `bpm`: tempo in quarter notes per minute.
- `beats`: total duration in quarter-note beats, including any silence.
- `parts`: instrument tracks with `name`, zero-based General MIDI `program` (0–127), and unique zero-based `channel` (0–15, excluding percussion channel 9).
- Each note is `[start_beat, duration_beats, MIDI_pitch, velocity]`; pitch is 0–127 and velocity is 1–127.

```sh
orchestra-forge compose --composition examples/demo.json --output samples/demo.mid
orchestra-forge render --midi samples/demo.mid --output samples/demo.wav
python -m unittest discover -s tests -v
```

## Modules

- `composition.py`: immutable note/part/composition data and validated JSON input.
- `midi.py`: Standard MIDI File type 1 writer, tempo and 4/4 metadata, UTF-8 track labels.
- `cli.py`: composition and offline FluidSynth rendering at 44.1 kHz, stereo 16-bit WAV.

## Licensing and commercial use

The source and generic example are MIT licensed; see `LICENSE`. Private compositions remain separate from the public source license. Using the tool does not require publishing your compositions. Rights to input melodies and instrument samples must be assessed separately.

[FluidSynth](https://www.fluidsynth.org/) is a separately installed LGPL synthesizer. Its license does not license your chosen SoundFont. Review the SoundFont's exact version and terms, and keep its license locally. [GeneralUser GS v1.471's license](https://github.com/planet-s/generaluser-gs/blob/master/LICENSE.txt) permits commercial music creation and profit from recordings, but the author notes incomplete provenance for some inherited samples. That permission is not a guarantee of sample provenance. Shipping a SoundFont or embedding the synthesizer has separate redistribution requirements from shipping rendered audio.

## Current limitations

- No trained generative model, automatic arrangement, stems, GUI, or loudness mastering.
- One fixed tempo and 4/4 metadata per composition; melodic General MIDI instruments only.
- FluidSynth exports release/reverb tails beyond the written phrase. A 30-second composition can produce a longer WAV. Seamless game loops need listening and deliberate tail wrapping/crossfading; this tool does not yet do that.
- SoundFont quality determines realism; orchestral phrasing and dynamics require manual refinement.
- JSON edits are explicit note data. Reusable composition algorithms can be added as modules without publishing private melodies.
