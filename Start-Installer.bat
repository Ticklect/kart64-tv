@echo off
cd /d "%~dp0"
py studio.py
if errorlevel 1 pause
