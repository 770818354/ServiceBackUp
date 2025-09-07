@echo off
chcp 65001 >nul
title 定时备份

echo ========================================
echo           定时备份
echo ========================================
echo.
echo 定时备份将在以下时间执行:
echo - 09:00
echo - 12:00  
echo - 17:00
echo - 00:00
echo.
echo 按 Ctrl+C 停止定时备份
echo.

python schedule_backup.py

echo.
echo 定时备份已停止
pause
