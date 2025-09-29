#!/bin/bash
# VÄKI - Quick launcher script

cd "$(dirname "$0")"
source venv/bin/activate
python main.py "$@"
