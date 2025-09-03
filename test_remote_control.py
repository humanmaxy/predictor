#!/usr/bin/env python3
"""
测试远程控制功能
诊断鼠标键盘控制问题
"""

import sys
import time
import platform
from native_control_utils import NativeController

def test_native_controller():
    """测试原生控制器"""
    print("🧪 测试原生控制器功能")
    print("=" * 50)
    
    controller = NativeController()
    system = platform.system().lower()
    
    print(f"系统: {system}")
    print(f"控制器启用: {controller.enabled}")
    
    if not controller.enabled:
        print("❌ 控制器未启用，无法测试")
        return False
    
    # 测试屏幕尺寸
    try:
        screen_size = controller.get_screen_size()
        print(f"✅ 屏幕尺寸: {screen_size[0]}x{screen_size[1]}")
    except Exception as e:
        print(f"❌ 获取屏幕尺寸失败: {e}")
        return False
    
    # 提示用户
    print("\n⚠️  即将进行鼠标控制测试")
    print("请确保:")
    print("1. 鼠标可以自由移动")
    print("2. 没有重要程序在运行")
    print("3. 准备观察鼠标移动")
    
    try:
        input("按回车键开始测试...")
    except KeyboardInterrupt:
        print("\n用户取消测试")
        return False
    
    # 测试鼠标移动
    print("\n🖱️  测试鼠标移动...")
    try:
        # 获取当前鼠标位置作为参考
        center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
        
        # 测试移动到屏幕中心
        print("移动鼠标到屏幕中心...")
        result = controller.move_mouse(center_x, center_y)
        print(f"移动结果: {'成功' if result else '失败'}")
        time.sleep(1)
        
        # 测试移动到四个角落
        positions = [
            (100, 100, "左上角"),
            (screen_size[0] - 100, 100, "右上角"),
            (screen_size[0] - 100, screen_size[1] - 100, "右下角"),
            (100, screen_size[1] - 100, "左下角"),
            (center_x, center_y, "回到中心")
        ]
        
        for x, y, desc in positions:
            print(f"移动到{desc} ({x}, {y})...")
            result = controller.move_mouse(x, y)
            print(f"结果: {'✅ 成功' if result else '❌ 失败'}")
            time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ 鼠标移动测试失败: {e}")
        return False
    
    # 测试鼠标点击
    print("\n🖱️  测试鼠标点击...")
    print("⚠️  将在2秒后在当前位置点击，请准备...")
    time.sleep(2)
    
    try:
        result = controller.click_mouse(center_x, center_y, 'left')
        print(f"点击结果: {'✅ 成功' if result else '❌ 失败'}")
    except Exception as e:
        print(f"❌ 鼠标点击测试失败: {e}")
        return False
    
    # 测试键盘输入
    print("\n⌨️  测试键盘输入...")
    print("⚠️  请打开一个文本编辑器或记事本")
    try:
        input("打开文本编辑器后按回车继续...")
    except KeyboardInterrupt:
        print("\n用户取消测试")
        return False
    
    try:
        # 测试文本输入
        test_text = "Hello Remote Control!"
        print(f"输入测试文本: {test_text}")
        result = controller.type_text(test_text)
        print(f"文本输入结果: {'✅ 成功' if result else '❌ 失败'}")
        
        time.sleep(1)
        
        # 测试按键
        print("测试回车键...")
        result = controller.press_key('enter')
        print(f"按键结果: {'✅ 成功' if result else '❌ 失败'}")
        
    except Exception as e:
        print(f"❌ 键盘输入测试失败: {e}")
        return False
    
    print("\n✅ 原生控制器测试完成!")
    return True

def test_system_specific():
    """测试系统特定功能"""
    system = platform.system().lower()
    print(f"\n🔍 系统特定测试 ({system})")
    print("=" * 30)
    
    if system == 'windows':
        test_windows_specific()
    elif system == 'darwin':
        test_macos_specific()
    elif system == 'linux':
        test_linux_specific()

def test_windows_specific():
    """Windows特定测试"""
    print("测试Windows ctypes...")
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        # 测试获取鼠标位置
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        print(f"✅ 当前鼠标位置: ({point.x}, {point.y})")
        
        # 测试移动鼠标
        user32.SetCursorPos(point.x + 10, point.y + 10)
        print("✅ 鼠标移动测试成功")
        
        # 恢复位置
        user32.SetCursorPos(point.x, point.y)
        
    except Exception as e:
        print(f"❌ Windows ctypes测试失败: {e}")

def test_macos_specific():
    """macOS特定测试"""
    print("测试macOS osascript...")
    try:
        import subprocess
        
        # 测试osascript可用性
        result = subprocess.run(['which', 'osascript'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ osascript 可用")
            
            # 测试获取鼠标位置
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to return mouse location'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 当前鼠标位置: {result.stdout.strip()}")
            else:
                print(f"❌ 获取鼠标位置失败: {result.stderr}")
        else:
            print("❌ osascript 不可用")
            
    except Exception as e:
        print(f"❌ macOS osascript测试失败: {e}")

def test_linux_specific():
    """Linux特定测试"""
    print("测试Linux xdotool...")
    try:
        import subprocess
        
        # 测试xdotool可用性
        result = subprocess.run(['which', 'xdotool'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ xdotool 可用")
            
            # 测试获取鼠标位置
            result = subprocess.run(['xdotool', 'getmouselocation'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ 当前鼠标位置: {result.stdout.strip()}")
            else:
                print(f"❌ 获取鼠标位置失败: {result.stderr}")
                
            # 测试X11显示
            import os
            if 'DISPLAY' in os.environ:
                print(f"✅ X11显示可用: {os.environ['DISPLAY']}")
            else:
                print("❌ X11显示不可用")
                
        else:
            print("❌ xdotool 不可用")
            print("请安装: sudo apt-get install xdotool")
            
    except Exception as e:
        print(f"❌ Linux xdotool测试失败: {e}")

def main():
    """主测试函数"""
    print("🔧 远程控制功能诊断工具")
    print("=" * 60)
    
    # 基础信息
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print()
    
    # 系统特定测试
    test_system_specific()
    
    # 原生控制器测试
    success = test_native_controller()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！远程控制功能应该正常工作。")
        print("\n如果在实际使用中仍有问题，可能的原因:")
        print("1. 权限问题 (macOS需要辅助功能权限)")
        print("2. 安全软件阻止")
        print("3. 网络共享目录权限问题")
    else:
        print("❌ 测试失败！请检查系统配置和权限设置。")
    
    print("\n按回车键退出...")
    try:
        input()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()