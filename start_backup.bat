@echo off
chcp 65001 >nul
title 自动备份脚本

:menu
cls
echo ========================================
echo           自动备份脚本
echo ========================================
echo.
echo 请选择操作:
echo.
echo [1] 执行备份
echo [2] 启动定时备份
echo [3] 检查配置
echo [4] 测试连接
echo [5] 查看日志
echo [6] 退出
echo.
set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto backup
if "%choice%"=="2" goto schedule
if "%choice%"=="3" goto check
if "%choice%"=="4" goto test
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto exit
echo 无效选项，请重新选择
pause
goto menu

:backup
cls
echo ========================================
echo           执行备份
echo ========================================
echo.
echo 正在执行备份...
python backup_script.py
echo.
echo 备份完成！
pause
goto menu

:schedule
cls
echo ========================================
echo           启动定时备份
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
pause
goto menu

:check
cls
echo ========================================
echo           检查配置
echo ========================================
echo.
python check_config.py
echo.
pause
goto menu

:test
cls
echo ========================================
echo           测试连接
echo ========================================
echo.
python backup_script.py --test
echo.
pause
goto menu

:logs
cls
echo ========================================
echo           查看日志
echo ========================================
echo.
if exist "logs\backup_%date:~0,4%%date:~5,2%%date:~8,2%.log" (
    echo 今天的备份日志:
    type "logs\backup_%date:~0,4%%date:~5,2%%date:~8,2%.log"
) else (
    echo 今天的备份日志不存在
    echo.
    echo 可用的日志文件:
    dir logs\*.log /b 2>nul
)
echo.
pause
goto menu

:exit
echo 再见！
exit
