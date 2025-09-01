#!/usr/bin/env python3
"""
聊天软件演示脚本
自动启动服务器和多个客户端进行演示
"""

import subprocess
import time
import threading
import os
import signal
import sys

class ChatDemo:
    def __init__(self):
        self.server_process = None
        self.client_processes = []
    
    def start_server(self):
        """启动服务器"""
        print("🚀 启动聊天服务器...")
        try:
            self.server_process = subprocess.Popen(
                ["python3", "chat_server.py", "--host", "0.0.0.0", "--port", "8765"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            time.sleep(2)  # 等待服务器启动
            print("✅ 服务器启动成功 (ws://localhost:8765)")
            return True
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            return False
    
    def start_clients(self, count=2):
        """启动多个客户端"""
        print(f"🖥️  启动 {count} 个客户端...")
        for i in range(count):
            try:
                process = subprocess.Popen(["python3", "chat_client.py"])
                self.client_processes.append(process)
                print(f"✅ 客户端 {i+1} 启动成功")
                time.sleep(1)  # 间隔启动
            except Exception as e:
                print(f"❌ 客户端 {i+1} 启动失败: {e}")
    
    def stop_all(self):
        """停止所有进程"""
        print("\n🛑 正在停止所有进程...")
        
        # 停止客户端
        for i, process in enumerate(self.client_processes):
            try:
                process.terminate()
                print(f"✅ 客户端 {i+1} 已停止")
            except:
                pass
        
        # 停止服务器
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ 服务器已停止")
            except:
                try:
                    self.server_process.kill()
                    print("✅ 服务器已强制停止")
                except:
                    pass
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print("\n接收到停止信号...")
        self.stop_all()
        sys.exit(0)
    
    def run_demo(self):
        """运行演示"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🎉 聊天软件演示")
        print("=" * 40)
        
        # 启动服务器
        if not self.start_server():
            return
        
        # 启动客户端
        self.start_clients(2)
        
        print("\n📋 演示说明:")
        print("1. 服务器已在 ws://localhost:8765 启动")
        print("2. 已启动2个客户端窗口")
        print("3. 在客户端中:")
        print("   - 输入不同的用户名和ID")
        print("   - 点击'连接'按钮")
        print("   - 开始聊天测试")
        print("4. 按 Ctrl+C 停止演示")
        
        try:
            # 保持运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()

def main():
    # 检查依赖
    try:
        import websockets
    except ImportError:
        print("❌ 缺少依赖包，请先安装:")
        print("pip install -r requirements.txt")
        return
    
    demo = ChatDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()