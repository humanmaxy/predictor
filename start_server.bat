@echo off
REM Windows 启动脚本
echo 正在启动聊天服务器启动器...

REM 检查虚拟环境是否存在
if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境中的Python
    venv\Scripts\python.exe start_server.py
) else (
    echo 虚拟环境不存在，使用系统Python
    python start_server.py
)

pause