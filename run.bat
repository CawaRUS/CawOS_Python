@echo off


if not exist main.py (
    echo [ERROR] File main.py not found. System will not start.
    pause
    exit /b 1
)


python main.py
pause