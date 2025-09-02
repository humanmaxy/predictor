#!/usr/bin/env python3
"""
启动HTTP模式的聊天服务器（无需SSL证书）
"""

import subprocess
import sys
import os

def start_http_server():
    """启动HTTP模式的服务器"""
    print("启动HTTP模式聊天服务器...")
    print("注意：HTTP模式不需要SSL证书，适合局域网使用")
    
    # 启动服务器
    cmd = [sys.executable, "chat_server.py", "--host", "0.0.0.0", "--port", "11900"]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("服务器地址: http://0.0.0.0:11900")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    start_http_server()