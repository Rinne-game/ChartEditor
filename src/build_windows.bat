@echo off
REM ===============================
REM Windows用ビルド
REM ===============================

cd src

pyinstaller --onefile --noconsole main.py ^
--name "ChartEditor" ^
--distpath ../build/windows ^
--workpath ../build/windows/temp ^
--specpath ../build/windows

echo Windowsビルド完了
pause
