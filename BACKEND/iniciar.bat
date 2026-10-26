@echo off
rem Arranca o backend Qolari Mobility (Rider 8090, Driver 8091, Fleet 3000 e consola 8300)
cd /d "%~dp0"
.venv\Scripts\python server.py
pause
