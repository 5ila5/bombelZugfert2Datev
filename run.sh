#! /bin/bash

# check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# activate virtual environment
.venv/bin/pip install -r requirements.txt
.venv/bin/python3 archive_builder.py