#!/usr/bin/env python3
"""
测试远程控制完整流程
"""

import tempfile
import time
import json
from pathlib import Path
from native_control_utils import NativeRemoteControlManager

def test_control_flow():
    """测试控制流程"""
    print("🧪 测试远程控制完整流程")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建管理器
        manager = NativeRemoteControlManager(temp_dir)
        
        # 检查控制器状态
        if not manager.controller.enabled:
            print("❌ 控制器未启用，无法测试")
            return
        
        print("✅ 控制器已启用")
        
        # 启动监听
        user_id = "test_user"
        if not manager.start_remote_control_listening(user_id):
            print("❌ 无法启动监听")
            return
        
        print("✅ 监听已启动")
        time.sleep(1)  # 等待监听线程启动
        
        # 发送测试命令
        test_commands = [
            {
                'type': 'mouse_move',
                'x': 500,
                'y': 300,
                'screen_size': (1920, 1080)
            },
            {
                'type': 'mouse_click',
                'x': 500,
                'y': 300,
                'button': 'left',
                'screen_size': (1920, 1080)
            }
        ]
        
        print("\n发送测试命令...")
        for i, command in enumerate(test_commands):
            print(f"\n命令 {i+1}: {command['type']}")
            success = manager.send_control_command(command)
            print(f"发送结果: {'✅ 成功' if success else '❌ 失败'}")
            
            # 等待命令处理
            time.sleep(1)
        
        # 等待命令处理完成
        print("\n等待命令处理完成...")
        time.sleep(3)
        
        # 停止监听
        manager.stop_remote_control_listening()
        print("\n✅ 监听已停止")
        
        # 检查控制目录
        control_dir = Path(temp_dir) / "remote_control" / "controls"
        remaining_files = list(control_dir.glob("cmd_*.json"))
        print(f"剩余命令文件: {len(remaining_files)}")
        
        if remaining_files:
            print("❌ 仍有未处理的命令文件:")
            for f in remaining_files:
                print(f"  - {f.name}")
        else:
            print("✅ 所有命令文件已处理")

def test_manual_control():
    """手动测试控制"""
    print("\n🎮 手动测试控制")
    print("=" * 30)
    
    from native_control_utils import NativeController
    
    controller = NativeController()
    
    if not controller.enabled:
        print("❌ 控制器未启用")
        return
    
    print("✅ 控制器已启用")
    
    # 获取屏幕尺寸
    screen_size = controller.get_screen_size()
    print(f"屏幕尺寸: {screen_size[0]}x{screen_size[1]}")
    
    # 测试鼠标移动
    print("\n测试鼠标移动到屏幕中心...")
    center_x, center_y = screen_size[0] // 2, screen_size[1] // 2
    
    result = controller.move_mouse(center_x, center_y)
    print(f"移动结果: {'✅ 成功' if result else '❌ 失败'}")
    
    time.sleep(1)
    
    # 测试点击
    print("测试鼠标点击...")
    result = controller.click_mouse(center_x, center_y, 'left')
    print(f"点击结果: {'✅ 成功' if result else '❌ 失败'}")

def main():
    """主函数"""
    print("🔧 远程控制流程测试")
    print("这个测试将验证远程控制的完整流程")
    print()
    
    # 手动控制测试
    test_manual_control()
    
    # 完整流程测试
    test_control_flow()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("如果看到错误，请检查:")
    print("1. 系统权限设置")
    print("2. 控制器是否正确初始化")
    print("3. 监听线程是否正常运行")
    print("4. 命令文件是否正确创建和处理")

if __name__ == "__main__":
    main()