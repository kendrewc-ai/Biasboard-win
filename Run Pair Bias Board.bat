@echo off
cd /d "%~dp0"
set PY=python
where pythonw >nul 2>nul
if not errorlevel 1 set PY=pythonw
"%PY%" main.py
if errorlevel 1 pause
