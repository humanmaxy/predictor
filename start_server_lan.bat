@echo off
REM Windows 局域网服务器启动脚本
echo 正在启动局域网聊天服务器...

REM 检查虚拟环境是否存在
if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境启动局域网服务器
    echo 服务器将监听所有网络接口 (0.0.0.0:8765)
    echo 局域网用户可通过您的IP地址连接
    echo.
    venv\Scripts\python.exe chat_server.py --host 0.0.0.0 --port 8765
) else (
    echo 虚拟环境不存在，请先运行 setup_windows.bat
    echo 或使用系统Python启动
    python chat_server.py --host 0.0.0.0 --port 8765
)

pause