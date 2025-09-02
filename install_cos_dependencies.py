#!/usr/bin/env python3
"""
安装COS聊天功能所需的依赖
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装依赖包"""
    dependencies = [
        "cos-python-sdk-v5",  # 腾讯云COS SDK
        "urllib3",            # HTTP库
    ]
    
    print("🔧 安装COS聊天功能依赖...")
    
    for package in dependencies:
        print(f"📦 安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 安装失败: {e}")
            return False
    
    print("\n🎉 所有依赖安装完成！")
    print("\n📖 使用说明:")
    print("1. 运行主聊天客户端: python3 chat_client.py")
    print("2. 点击 'COS云聊天' 按钮启动云端聊天")
    print("3. 或直接运行: python3 cos_chat_client.py")
    
    return True

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import qcloud_cos
        print("✅ 腾讯云COS SDK 已安装")
        return True
    except ImportError:
        print("❌ 腾讯云COS SDK 未安装")
        return False

def main():
    print("COS聊天功能依赖检查器")
    print("=" * 40)
    
    if check_dependencies():
        print("🎯 所有依赖已就绪，可以使用COS聊天功能！")
    else:
        choice = input("\n是否安装缺失的依赖？(y/N): ")
        if choice.lower() == 'y':
            install_dependencies()
        else:
            print("⚠️  未安装依赖，COS聊天功能将无法使用")

if __name__ == "__main__":
    main()