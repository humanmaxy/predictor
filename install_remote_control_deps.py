#!/usr/bin/env python3
"""
安装远程控制功能所需的依赖包
"""

import sys
import subprocess
import importlib.util

def check_package(package_name):
    """检查包是否已安装"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """安装包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 检查并安装远程控制功能依赖...")
    
    # 必需的包列表
    required_packages = [
        ("PIL", "pillow"),  # (import_name, pip_name)
        ("pyautogui", "pyautogui"),
    ]
    
    # 可选的包（用于更好的性能）
    optional_packages = [
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
    ]
    
    install_count = 0
    failed_count = 0
    
    # 检查并安装必需包
    print("\n📦 检查必需依赖...")
    for import_name, pip_name in required_packages:
        if not check_package(import_name):
            print(f"❌ {import_name} 未安装")
            if install_package(pip_name):
                install_count += 1
            else:
                failed_count += 1
        else:
            print(f"✅ {import_name} 已安装")
    
    # 检查并安装可选包
    print("\n📦 检查可选依赖（用于增强功能）...")
    for import_name, pip_name in optional_packages:
        if not check_package(import_name):
            print(f"⚠️  {import_name} 未安装（可选）")
            choice = input(f"是否安装 {pip_name}? (y/n): ").lower()
            if choice == 'y':
                if install_package(pip_name):
                    install_count += 1
                else:
                    failed_count += 1
        else:
            print(f"✅ {import_name} 已安装")
    
    # 安装总结
    print(f"\n📊 安装总结:")
    print(f"✅ 成功安装: {install_count} 个包")
    if failed_count > 0:
        print(f"❌ 安装失败: {failed_count} 个包")
    
    # 测试导入
    print("\n🧪 测试功能模块...")
    
    try:
        from PIL import Image, ImageGrab
        print("✅ PIL/Pillow 导入成功")
        
        # 测试屏幕截图
        screenshot = ImageGrab.grab()
        print(f"✅ 屏幕截图功能正常 ({screenshot.size[0]}x{screenshot.size[1]})")
        
    except ImportError as e:
        print(f"❌ PIL/Pillow 导入失败: {e}")
    
    try:
        import pyautogui
        print("✅ pyautogui 导入成功")
        
        # 获取屏幕尺寸
        screen_size = pyautogui.size()
        print(f"✅ 鼠标键盘控制功能正常 (屏幕: {screen_size[0]}x{screen_size[1]})")
        
        # 禁用故障保护
        pyautogui.FAILSAFE = False
        print("✅ pyautogui 故障保护已禁用")
        
    except ImportError as e:
        print(f"❌ pyautogui 导入失败: {e}")
        print("⚠️  远程控制功能将受限")
    
    # 功能说明
    print(f"\n📋 功能说明:")
    print("1. 屏幕共享: 实时捕获并共享屏幕内容")
    print("2. 远程控制: 通过鼠标键盘控制远程电脑")
    print("3. 文件传输: 支持指定目录下载文件")
    print("4. 基于共享目录: 无需额外网络配置")
    
    print(f"\n🚀 安装完成! 现在可以使用完整的远程控制功能了。")
    
    if failed_count > 0:
        print(f"\n⚠️  注意: 有 {failed_count} 个包安装失败，某些功能可能受限。")
        print("你可以稍后手动安装这些包:")
        for import_name, pip_name in required_packages + optional_packages:
            if not check_package(import_name):
                print(f"  pip install {pip_name}")

if __name__ == "__main__":
    main()