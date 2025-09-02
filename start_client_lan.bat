@echo off
REM Windows 局域网客户端启动脚本
echo 正在启动聊天客户端 (局域网模式)...

REM 检查虚拟环境是否存在
if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境启动客户端
    venv\Scripts\python.exe chat_client.py
) else (
    echo 虚拟环境不存在，使用系统Python
    python chat_client.py
)

echo.
echo 提示：点击"局域网"按钮快速连接到 172.27.66.166:8765
pause