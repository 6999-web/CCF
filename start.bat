@echo off
echo Starting Backend on 0.0.0.0:5051...
start cmd /k "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 5051 --reload"

echo Starting Frontend on 0.0.0.0:5052...
start cmd /k "cd frontend && npm run dev -- --host 0.0.0.0 --port 5052"

echo Services started!
