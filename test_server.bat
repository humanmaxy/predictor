@echo off
REM 测试服务器是否能正常启动
echo 正在测试聊天服务器...

if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境测试服务器
    timeout /t 5 /nobreak >nul && taskkill /f /im python.exe >nul 2>&1
    start /b venv\Scripts\python.exe chat_server.py --host localhost --port 8765
    timeout /t 3 /nobreak >nul
    taskkill /f /im python.exe >nul 2>&1
    echo 服务器测试完成
) else (
    echo 虚拟环境不存在，请先运行 setup_windows.bat
)

pause