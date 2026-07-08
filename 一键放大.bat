@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在用默认设置(漫画模型/4倍/PNG)批量放大 input 文件夹...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0upscale.ps1"
echo.
pause
