@echo off
chcp 65001 >nul
rem build_exe.bat  v1.3.2
cd /d "%~dp0"
echo === [1/4] Проверка Python ===
python --version || (echo Python не найден & pause & exit /b 1)
echo === [2/4] Библиотеки ===
python -m pip install -r requirements.txt || (echo Ошибка pip & pause & exit /b 1)
echo === [3/4] PyInstaller ===
python -m PyInstaller --noconfirm --clean win_fix.spec || (echo Ошибка сборки & pause & exit /b 1)
echo === [4/4] Самопроверка ===
dist\win_fix.exe --selftest || (echo Самопроверка не прошла & pause & exit /b 1)
echo Готово: dist\win_fix.exe
pause
