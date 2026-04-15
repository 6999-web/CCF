@echo off
echo Starting Backend on 101.33.210.169:5051...
start cmd /k "cd backend && uvicorn app.main:app --host 101.33.210.169 --port 5051 --reload"

echo Starting Frontend on 101.33.210.169:5052...
start cmd /k "cd frontend && npm run dev -- --host 101.33.210.169 --port 5052"

echo Services started!
