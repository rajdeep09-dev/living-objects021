#!/usr/bin/env sh
set -eu
python scripts/run_v5_benchmarks.py --all --generations "${1:-100000}" --resume
