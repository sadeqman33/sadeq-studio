#!/bin/zsh
set -e
cd "${0:A:h}"
python3 -m venv .venv-cutout
.venv-cutout/bin/python -m pip install -r requirements-cutout.txt
.venv-cutout/bin/python cutout.py
