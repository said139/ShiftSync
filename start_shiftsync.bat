@echo off
title ShiftSync Full-Stack Launcher
echo ============================================================
echo   Starting ShiftSync Backend (http://127.0.0.1:8000)
echo   and React Frontend (http://127.0.0.1:5173)
echo ============================================================

start "ShiftSync Django Backend" cmd /k "cd /d C:\Users\saidm\OneDrive\Desktop\SHIFTSYNC\backend && C:\Users\saidm\OneDrive\Desktop\SHIFTSYNC\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
start "ShiftSync React Frontend" cmd /k "cd /d C:\Users\saidm\OneDrive\Desktop\SHIFTSYNC\frontend && npm.cmd run dev"

timeout /t 3 >nul
start http://127.0.0.1:5173
echo ShiftSync is launching in your browser at http://127.0.0.1:5173
