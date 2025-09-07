@echo off
chcp 65001 >nul
title 快速备份

echo ========================================
echo           快速备份
echo ========================================
echo.
echo 正在执行备份...
echo.

python backup_script.py

echo.
echo 备份完成！
echo 按任意键退出...
pause >nul
