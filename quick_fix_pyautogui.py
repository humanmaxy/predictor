#!/usr/bin/env python3
"""
PyAutoGUI快速修复脚本
"""

import sys
import subprocess

def quick_fix():
    """快速修复PyAutoGUI"""
    print("🔧 PyAutoGUI快速修复")
    print("=" * 40)
    
    steps = [
        ("升级pip", [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]),
        ("卸载PyAutoGUI", [sys.executable, "-m", "pip", "uninstall", "pyautogui", "-y"]),
        ("安装PyAutoGUI", [sys.executable, "-m", "pip", "install", "pyautogui"]),
    ]
    
    for step_name, cmd in steps:
        print(f"\n🔄 {step_name}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"✅ {step_name}成功")
            else:
                print(f"❌ {step_name}失败: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ {step_name}异常: {e}")
    
    # 测试导入
    print(f"\n🧪 测试导入...")
    try:
        import pyautogui
        print(f"✅ PyAutoGUI导入成功，版本: {pyautogui.__version__}")
        print("✅ 修复完成！")
        return True
    except Exception as e:
        print(f"❌ 导入仍然失败: {e}")
        print("请运行完整修复: python fix_pyautogui.py")
        return False

if __name__ == "__main__":
    quick_fix()