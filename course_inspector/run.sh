#!/usr/bin/env bash
# Start a virtual display if none exists, then launch the app.
set -e

if [ -z "$DISPLAY" ]; then
    Xvfb :99 -screen 0 1280x800x24 &>/tmp/xvfb.log &
    export DISPLAY=:99
    sleep 0.5
fi

cd "$(dirname "$0")"
python3.12 main.py
