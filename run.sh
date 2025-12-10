#!/bin/bash
# DownX Başlatma Scripti

cd "$(dirname "$0")"
source .venv/bin/activate
python gui.py
