@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  正在打包 AI 生图放大器 (文件夹版)
echo ============================================
echo.

REM 清理旧产物
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "AI生图放大器.spec" del /q "AI生图放大器.spec"

python -m PyInstaller --noconfirm --windowed --name "AI生图放大器" ^
    --icon "assets\icon.ico" ^
    --add-data "bin;bin" ^
    --add-data "assets;assets" ^
    --collect-all sv_ttk ^
    gui.py

echo.
if exist "dist\AI生图放大器\AI生图放大器.exe" (
    echo ============================================
    echo  打包成功！
    echo  成品目录: dist\AI生图放大器\
    echo  双击运行: dist\AI生图放大器\AI生图放大器.exe
    echo  分发时把整个 AI生图放大器 文件夹打包压缩即可。
    echo ============================================
) else (
    echo [失败] 未生成 exe，请检查上方报错信息。
)
echo.
pause
