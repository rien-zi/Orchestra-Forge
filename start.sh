#!/bin/sh
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$TASK_ROOT"
if [ ! -x .venv/bin/orchestra-forge-audiolizer ]; then
  printf 'Run ./setup.sh first.\n' >&2
  exit 1
fi
exec .venv/bin/orchestra-forge-audiolizer "$@"
