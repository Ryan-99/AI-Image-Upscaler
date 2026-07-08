@echo off
cd /d "%~dp0"
REM 优先用 pythonw 启动(无黑窗)，找不到则退回 python
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0gui.py"
) else (
    start "" python "%~dp0gui.py"
)
