from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .composition import load_composition
from .midi import write_midi


def _render(midi: Path, soundfont: Path | None, wav: Path) -> None:
    fluidsynth = shutil.which('fluidsynth')
    if not fluidsynth:
        raise ValueError('FluidSynth not found. Install it with: brew install fluid-synth')
    if not midi.is_file():
        raise ValueError(f'MIDI not found: {midi}')
    if soundfont is None or not soundfont.is_file():
        raise ValueError('Provide an existing SoundFont with --soundfont or ORCHESTRA_FORGE_SOUNDFONT')
    if wav.resolve() in (midi.resolve(), soundfont.resolve()):
        raise ValueError('Audio output must differ from the MIDI and SoundFont paths')
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([fluidsynth, '-ni', '-g', '0.8', '-r', '44100', '-T', 'wav', '-O', 's16',
                    '-F', str(wav), str(soundfont), str(midi)], check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='orchestra-forge', description='Compose orchestral MIDI from JSON and render WAV with FluidSynth.')
    sub = parser.add_subparsers(dest='command', required=True)
    compose = sub.add_parser('compose', help='write MIDI from a composition JSON file')
    compose.add_argument('--composition', type=Path, required=True)
    compose.add_argument('--output', type=Path, required=True)
    render = sub.add_parser('render', help='render an existing MIDI file')
    demo = sub.add_parser('demo', help='compose JSON to MIDI, then render WAV')
    demo.add_argument('--composition', type=Path, required=True)
    default_sf = os.environ.get('ORCHESTRA_FORGE_SOUNDFONT')
    for cmd in (render, demo):
        cmd.add_argument('--midi', type=Path, required=True)
        cmd.add_argument('--output', type=Path, required=True)
        cmd.add_argument('--soundfont', type=Path, default=Path(default_sf) if default_sf else None)
    args = parser.parse_args(argv)
    try:
        if args.command in ('compose', 'demo'):
            composition = load_composition(args.composition)
            midi = args.output if args.command == 'compose' else args.midi
            inputs = [args.composition.resolve()]
            if args.command == 'demo':
                inputs += [args.output.resolve()]
                if args.soundfont:
                    inputs += [args.soundfont.resolve()]
                if args.output.resolve() == args.composition.resolve():
                    raise ValueError('Audio output must differ from composition input')
            if midi.resolve() in inputs:
                raise ValueError('MIDI output must differ from input and audio paths')
            write_midi(midi, composition)
            print(f'Wrote {midi} ({composition.seconds:.2f} seconds; {len(composition.parts)} parts)')
        if args.command in ('render', 'demo'):
            _render(args.midi, args.soundfont, args.output)
            print(f'Rendered {args.output}')
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0
