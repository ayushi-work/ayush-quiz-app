#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install -q -r backend/requirements.txt
python3 -m backend.seed
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
