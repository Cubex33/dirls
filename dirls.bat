@echo off

for /f "delims=" %%i in ('python "%~dp0dirls.py"') do set "TARGET=%%i"

if defined TARGET (
    if exist "%TARGET%\*" (
        cd /d "%TARGET%"
    ) else (
        cd "" "%TARGET%"
    )
)