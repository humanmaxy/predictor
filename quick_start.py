#!/usr/bin/env python3
"""
快速启动聊天服务器
提供HTTP和HTTPS两种模式
"""

import subprocess
import sys
import os

def start_http_server(host="0.0.0.0", port="11900"):
    """启动HTTP模式服务器"""
    print("🚀 启动HTTP模式聊天服务器...")
    print(f"📡 服务器地址: http://{host}:{port}")
    print("✅ HTTP模式无需SSL证书，适合局域网使用")
    print("🔄 新功能：支持群聊和一对一私聊")
    print("💡 客户端使用：双击用户列表中的用户名开始私聊")
    print("-" * 50)
    
    cmd = [sys.executable, "chat_server.py", "--host", host, "--port", port]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")

def start_https_server(host="0.0.0.0", port="11900", cert="publicKey.pem", key="privateKey.pem"):
    """启动HTTPS模式服务器"""
    # 检查证书文件
    if not os.path.exists(cert) or not os.path.exists(key):
        print("❌ SSL证书文件不存在")
        print(f"   需要的文件: {cert}, {key}")
        print("\n解决方案:")
        print("1. 生成新证书: python3 generate_ssl_with_cryptography.py")
        print("2. 使用HTTP模式: python3 quick_start.py")
        return False
    
    print("🔒 启动HTTPS模式聊天服务器...")
    print(f"📡 服务器地址: https://{host}:{port}")
    print("🔐 HTTPS模式提供加密通信")
    print("🔄 新功能：支持群聊和一对一私聊")
    print("💡 客户端使用：双击用户列表中的用户名开始私聊")
    print("-" * 50)
    
    cmd = [sys.executable, "chat_server.py", "--host", host, "--port", port, 
           "--ssl", "--cert", cert, "--key", key]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    
    return True

def main():
    print("🎯 聊天服务器快速启动工具")
    print("=" * 40)
    
    print("\n选择启动模式:")
    print("1. HTTP模式 (推荐，无需证书)")
    print("2. HTTPS模式 (需要SSL证书)")
    print("3. 生成SSL证书")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        start_http_server()
    
    elif choice == "2":
        start_https_server()
    
    elif choice == "3":
        print("\n选择证书生成工具:")
        print("1. 使用cryptography库生成")
        print("2. 使用OpenSSL生成")
        
        cert_choice = input("请选择 (1-2): ").strip()
        if cert_choice == "1":
            os.system("python3 generate_ssl_with_cryptography.py")
        elif cert_choice == "2":
            os.system("python3 generate_ssl_cert.py")
    
    elif choice == "4":
        print("👋 退出")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()