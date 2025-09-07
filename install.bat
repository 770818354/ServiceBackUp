@echo off
chcp 65001 >nul
echo ========================================
echo    自动备份脚本 - 安装工具
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo Python已安装

echo.
echo [2/3] 安装依赖包...
pip install paramiko scp schedule
if errorlevel 1 (
    echo 依赖安装失败
    pause
    exit /b 1
)
echo 依赖安装成功

echo.
echo [3/3] 检查配置...
python check_config.py
if errorlevel 1 (
    echo 配置检查失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo             安装完成！
echo ========================================
echo.
echo    使用方法:
echo    python backup_script.py          # 执行备份
echo    python schedule_backup.py        # 启动定时备份
echo    python check_config.py           # 检查配置
echo.
pause