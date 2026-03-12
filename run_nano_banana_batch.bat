@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 nano_banana_batch.py
  goto end
)

where python >nul 2>nul
if %errorlevel%==0 (
  python nano_banana_batch.py
  goto end
)

echo 未检测到 Python。
echo 请先安装 Python 3，然后执行 requirements-python.txt 里的依赖安装。

:end
echo.
pause
endlocal