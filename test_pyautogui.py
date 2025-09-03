#!/usr/bin/env python3
"""
测试PyAutoGUI导入和功能
"""

import sys
import traceback

def test_pyautogui_import():
    """测试PyAutoGUI导入"""
    print("[检查] 测试PyAutoGUI导入...")
    
    try:
        import pyautogui
        print("[成功] PyAutoGUI导入成功")
        print(f"   版本: {pyautogui.__version__}")
        
        # 测试基本功能
        try:
            screen_size = pyautogui.size()
            print(f"[成功] 屏幕尺寸获取成功: {screen_size[0]}x{screen_size[1]}")
        except Exception as e:
            print(f"[失败] 屏幕尺寸获取失败: {e}")
        
        try:
            mouse_pos = pyautogui.position()
            print(f"[成功] 鼠标位置获取成功: ({mouse_pos.x}, {mouse_pos.y})")
        except Exception as e:
            print(f"[失败] 鼠标位置获取失败: {e}")
        
        # 禁用故障保护
        pyautogui.FAILSAFE = False
        print("[成功] 故障保护已禁用")
        
        return True
        
    except ImportError as e:
        print(f"[失败] PyAutoGUI导入失败: {e}")
        print("请确认已安装PyAutoGUI:")
        print("  pip install pyautogui")
        return False
    except Exception as e:
        print(f"[失败] PyAutoGUI测试失败: {e}")
        traceback.print_exc()
        return False

def test_pil_import():
    """测试PIL导入"""
    print("\n[检查] 测试PIL导入...")
    
    try:
        from PIL import Image, ImageGrab
        print("[成功] PIL导入成功")
        
        # 测试屏幕截图
        try:
            screenshot = ImageGrab.grab()
            print(f"[成功] 屏幕截图成功: {screenshot.size[0]}x{screenshot.size[1]}")
        except Exception as e:
            print(f"[失败] 屏幕截图失败: {e}")
        
        return True
        
    except ImportError as e:
        print(f"[失败] PIL导入失败: {e}")
        print("请确认已安装Pillow:")
        print("  pip install pillow")
        return False
    except Exception as e:
        print(f"[失败] PIL测试失败: {e}")
        return False

def main():
    """主测试函数"""
    # 设置输出编码，避免Windows下的编码问题
    import sys
    import io
    
    # 尝试设置UTF-8输出
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass
    
    print("测试 远程控制依赖测试")
    print("=" * 50)
    
    # 显示Python版本
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print()
    
    # 测试导入
    pyautogui_ok = test_pyautogui_import()
    pil_ok = test_pil_import()
    
    print("\n[结果] 测试结果:")
    if pyautogui_ok and pil_ok:
        print("[成功] 所有依赖都正常，远程控制功能可用")
    else:
        print("[警告] 部分依赖有问题，某些功能可能受限")
        
    print("\n[启动] 如果所有测试都通过，可以启动远程控制功能:")
    print("  python network_share_chat.py")

if __name__ == "__main__":
    main()