#!/usr/bin/env python3
"""
测试布局管理器修复
"""

import tkinter as tk
from tkinter import ttk
import tempfile

def test_layout_fix():
    """测试布局修复"""
    print("测试布局管理器修复...")
    
    root = tk.Tk()
    root.title("布局测试")
    root.geometry("600x400")
    
    # 创建主框架 - 使用grid布局
    main_frame = ttk.Frame(root)
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(2, weight=1)
    
    # 添加一些使用grid的组件
    ttk.Label(main_frame, text="测试标签1").grid(row=0, column=0, sticky=tk.W, pady=5)
    ttk.Label(main_frame, text="测试标签2").grid(row=1, column=0, sticky=tk.W, pady=5)
    
    # 测试原生远程控制面板
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            from native_control_utils import NativeRemoteControlManager
            from native_control_gui import NativeRemoteControlPanel
            
            remote_manager = NativeRemoteControlManager(temp_dir)
            panel = NativeRemoteControlPanel(main_frame, remote_manager, "test_user")
            
            print("✅ 原生远程控制面板创建成功，无布局冲突")
            
    except Exception as e:
        print(f"❌ 原生远程控制面板创建失败: {e}")
    
    # 测试原始远程控制面板
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            from remote_control_utils import RemoteControlManager
            from remote_control_gui import RemoteControlPanel
            
            remote_manager = RemoteControlManager(temp_dir)
            panel = RemoteControlPanel(main_frame, remote_manager, "test_user")
            
            print("✅ 原始远程控制面板创建成功，无布局冲突")
            
    except Exception as e:
        print(f"❌ 原始远程控制面板创建失败: {e}")
    
    # 显示窗口一会儿然后关闭
    def close_after_delay():
        root.after(2000, root.destroy)  # 2秒后关闭
    
    close_after_delay()
    root.mainloop()
    
    print("✅ 布局测试完成")

if __name__ == "__main__":
    test_layout_fix()