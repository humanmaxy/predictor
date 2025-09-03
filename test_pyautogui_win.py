#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows兼容的PyAutoGUI测试脚本
避免Unicode编码问题
"""

import sys
import traceback
import os

# 设置Windows控制台编码
if sys.platform.startswith('win'):
    try:
        # 尝试设置控制台为UTF-8
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

def safe_print(text):
    """安全的打印函数，避免编码错误"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果有编码问题，使用ASCII安全版本
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

def test_pyautogui_import():
    """测试PyAutoGUI导入"""
    safe_print("[检查] 测试PyAutoGUI导入...")
    
    try:
        import pyautogui
        safe_print("[成功] PyAutoGUI导入成功")
        safe_print(f"   版本: {pyautogui.__version__}")
        
        # 测试基本功能
        try:
            screen_size = pyautogui.size()
            safe_print(f"[成功] 屏幕尺寸获取成功: {screen_size[0]}x{screen_size[1]}")
        except Exception as e:
            safe_print(f"[失败] 屏幕尺寸获取失败: {e}")
        
        try:
            mouse_pos = pyautogui.position()
            safe_print(f"[成功] 鼠标位置获取成功: ({mouse_pos.x}, {mouse_pos.y})")
        except Exception as e:
            safe_print(f"[失败] 鼠标位置获取失败: {e}")
        
        # 禁用故障保护
        pyautogui.FAILSAFE = False
        safe_print("[成功] 故障保护已禁用")
        
        return True
        
    except ImportError as e:
        safe_print(f"[失败] PyAutoGUI导入失败: {e}")
        safe_print("请确认已安装PyAutoGUI:")
        safe_print("  pip install pyautogui")
        return False
    except Exception as e:
        safe_print(f"[失败] PyAutoGUI测试失败: {e}")
        traceback.print_exc()
        return False

def test_pil_import():
    """测试PIL导入"""
    safe_print("\n[检查] 测试PIL导入...")
    
    try:
        from PIL import Image, ImageGrab
        safe_print("[成功] PIL导入成功")
        
        # 测试屏幕截图
        try:
            screenshot = ImageGrab.grab()
            safe_print(f"[成功] 屏幕截图成功: {screenshot.size[0]}x{screenshot.size[1]}")
        except Exception as e:
            safe_print(f"[失败] 屏幕截图失败: {e}")
        
        return True
        
    except ImportError as e:
        safe_print(f"[失败] PIL导入失败: {e}")
        safe_print("请确认已安装Pillow:")
        safe_print("  pip install pillow")
        return False
    except Exception as e:
        safe_print(f"[失败] PIL测试失败: {e}")
        return False

def check_system_info():
    """检查系统信息"""
    safe_print("[系统] 系统信息:")
    safe_print(f"  操作系统: {sys.platform}")
    safe_print(f"  Python版本: {sys.version.split()[0]}")
    safe_print(f"  Python路径: {sys.executable}")
    
    # 检查编码
    import locale
    safe_print(f"  默认编码: {locale.getpreferredencoding()}")
    safe_print(f"  控制台编码: {sys.stdout.encoding}")
    safe_print("")

def main():
    """主测试函数"""
    safe_print("PyAutoGUI 依赖测试 (Windows兼容版)")
    safe_print("=" * 50)
    
    # 显示系统信息
    check_system_info()
    
    # 测试导入
    pyautogui_ok = test_pyautogui_import()
    pil_ok = test_pil_import()
    
    safe_print("\n[结果] 测试结果:")
    if pyautogui_ok and pil_ok:
        safe_print("[成功] 所有依赖都正常，远程控制功能可用")
        safe_print("")
        safe_print("现在可以启动远程控制功能:")
        safe_print("  python network_share_chat.py")
        safe_print("  python start_remote_assistance.py")
    else:
        safe_print("[警告] 部分依赖有问题，某些功能可能受限")
        safe_print("")
        safe_print("修复建议:")
        if not pyautogui_ok:
            safe_print("  pip install pyautogui")
        if not pil_ok:
            safe_print("  pip install pillow")
        safe_print("  python fix_pyautogui.py  # 运行完整修复")

if __name__ == "__main__":
    main()