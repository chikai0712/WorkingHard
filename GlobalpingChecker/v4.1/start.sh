#!/bin/bash
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --reload
