#!/bin/sh
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$TASK_ROOT"
PYTHON=${PYTHON:-python3}
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install .
printf '\nSetup complete. Run ./start.sh to open Audiolizer.\n'
command -v fluidsynth >/dev/null 2>&1 || printf 'WAV previews require FluidSynth: brew install fluid-synth (macOS).\n'
