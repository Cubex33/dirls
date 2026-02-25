
@echo off
REM Запуск менеджера
for /f "delims=" %%i in ('python C:\Users\Cubex33\Desktop\Work\SysCommand\dirls.py') do set NEWDIR=%%i
REM Переход в директорию, которую вернул скрипт
cd /d %NEWDIR%