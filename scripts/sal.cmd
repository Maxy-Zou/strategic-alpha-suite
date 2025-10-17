@echo off
set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..
set PYTHONPATH=%REPO_ROOT%\strategic_alpha\src;%PYTHONPATH%
python -m strategic_alpha.cli %*
