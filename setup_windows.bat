@echo off
REM Windows 环境设置脚本
echo 正在设置聊天服务器环境...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python已安装，版本信息：
python --version

REM 创建虚拟环境
echo.
echo 正在创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo 错误: 无法创建虚拟环境
    pause
    exit /b 1
)

REM 激活虚拟环境并安装依赖
echo.
echo 正在安装依赖包...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 环境设置完成！
echo 现在可以运行 start_server.bat 来启动服务器
pause