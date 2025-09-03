#!/usr/bin/env python3
"""
简化远程控制启动器
仅支持命令行远程控制，无鼠标操作
"""

import tkinter as tk
from tkinter import ttk, messagebox
import platform
import sys
import os
import tempfile
from pathlib import Path

class SimpleRemoteControlLauncher:
    """简化远程控制启动器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("简化远程控制启动器")
        self.root.geometry("600x500")
        
        self.system = platform.system().lower()
        self.system_support = self._check_system_support()
        
        self._create_widgets()
    
    def _check_system_support(self):
        """检查系统支持情况"""
        support_info = {
            'system': self.system,
            'screen_capture': True,  # PIL ImageGrab 支持所有系统
            'keyboard_control': False,
            'command_execution': True,  # 所有系统都支持命令执行
            'requirements': []
        }
        
        if self.system == 'windows':
            support_info['keyboard_control'] = True
            support_info['requirements'] = ['Windows内置API (ctypes)']
        elif self.system == 'darwin':  # macOS
            try:
                import subprocess
                result = subprocess.run(['which', 'osascript'], capture_output=True)
                if result.returncode == 0:
                    support_info['keyboard_control'] = True
                    support_info['requirements'] = ['osascript (系统内置)']
                else:
                    support_info['requirements'] = ['需要启用osascript']
            except:
                support_info['requirements'] = ['无法检测osascript']
        elif self.system == 'linux':
            requirements = []
            try:
                import subprocess
                # 检查xdotool
                result = subprocess.run(['which', 'xdotool'], capture_output=True)
                if result.returncode == 0:
                    support_info['keyboard_control'] = True
                    requirements.append('xdotool (已安装)')
                else:
                    requirements.append('键盘控制需要: sudo apt-get install xdotool')
                
                # 检查X11
                if 'DISPLAY' in os.environ:
                    requirements.append('X11显示可用')
                else:
                    requirements.append('需要X11显示环境')
                    
            except:
                requirements.append('无法检测Linux工具')
            
            support_info['requirements'] = requirements
        
        return support_info
    
    def _create_widgets(self):
        """创建界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🖥️ 简化远程控制", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="仅命令行控制，无鼠标操作", 
                                 font=("Arial", 12), foreground="blue")
        subtitle_label.pack(pady=(0, 20))
        
        # 系统支持状态
        support_frame = ttk.LabelFrame(main_frame, text="系统支持状态", padding=10)
        support_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 系统信息
        system_info = f"操作系统: {platform.system()} {platform.release()}"
        ttk.Label(support_frame, text=system_info, font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # 功能支持
        features = [
            ("屏幕捕获", self.system_support['screen_capture'], "使用PIL ImageGrab"),
            ("命令执行", self.system_support['command_execution'], "系统subprocess"),
            ("键盘输入", self.system_support['keyboard_control'], "系统原生API (可选)")
        ]
        
        for feature_name, supported, method in features:
            frame = ttk.Frame(support_frame)
            frame.pack(fill=tk.X, pady=2)
            
            status = "✅" if supported else "⚠️"
            color = "green" if supported else "orange"
            
            ttk.Label(frame, text=f"{status} {feature_name}:", 
                     foreground=color).pack(side=tk.LEFT)
            ttk.Label(frame, text=method, font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 系统要求
        if self.system_support['requirements']:
            ttk.Label(support_frame, text="系统要求:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
            for req in self.system_support['requirements']:
                ttk.Label(support_frame, text=f"  • {req}", font=("Arial", 9)).pack(anchor=tk.W)
        
        # 功能说明
        features_frame = ttk.LabelFrame(main_frame, text="功能特点", padding=10)
        features_frame.pack(fill=tk.X, pady=(0, 15))
        
        features_text = """
✅ 简化设计：
  • 移除了鼠标操作功能
  • 专注于命令行远程控制
  • 更轻量级，更稳定

🖥️ 命令行控制：
  • 直接执行系统命令
  • 支持命令历史记录
  • 实时显示命令输出
  • 快捷命令按钮

⌨️ 键盘输入（可选）：
  • 远程文本输入
  • 特殊按键支持
  • 适合文本编辑场景

📺 屏幕共享：
  • 实时查看远程屏幕
  • 了解命令执行效果
        """
        
        features_label = ttk.Label(features_frame, text=features_text, 
                                 font=("Arial", 9), justify=tk.LEFT)
        features_label.pack(anchor=tk.W)
        
        # 启动按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 启动按钮
        launch_btn = ttk.Button(button_frame, text="🚀 启动简化远程控制", 
                              command=self.launch_simple_control, width=25)
        launch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 测试按钮
        test_btn = ttk.Button(button_frame, text="🧪 测试命令执行", 
                            command=self.test_command_execution, width=20)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 直接打开终端按钮
        terminal_btn = ttk.Button(button_frame, text="🖥️ 直接打开终端", 
                                command=self.open_terminal_directly, width=20)
        terminal_btn.pack(side=tk.LEFT)
        
        # 使用说明
        help_frame = ttk.LabelFrame(main_frame, text="使用说明", padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = """
使用步骤:

1. 启动程序:
   • 点击"启动简化远程控制"启动完整聊天客户端
   • 或点击"直接打开终端"仅使用命令行功能

2. 命令行控制:
   • 在远程终端窗口中输入命令
   • 支持所有系统命令 (ls, dir, pwd, whoami等)
   • 使用上下箭头键浏览命令历史
   • 点击快捷按钮执行常用命令

3. 屏幕共享:
   • 可选择启用屏幕共享查看远程桌面
   • 了解命令执行的图形界面效果

4. 安全提醒:
   • 命令行控制权限很高，请谨慎使用
   • 仅在信任的网络环境中使用
   • 及时关闭不需要的控制权限

示例命令:
  • pwd - 显示当前目录
  • ls / dir - 列出文件
  • whoami - 显示当前用户
  • ps / tasklist - 显示进程
  • netstat -an - 显示网络连接
        """
        
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, 
                              font=("Arial", 9))
        help_label.pack(anchor=tk.W)
    
    def launch_simple_control(self):
        """启动简化远程控制"""
        try:
            # 启动主程序
            from network_share_chat import NetworkShareChatClient
            
            def run_client():
                client = NetworkShareChatClient()
                client.run()
            
            import threading
            threading.Thread(target=run_client, daemon=True).start()
            
            messagebox.showinfo("启动成功", 
                              "简化远程控制聊天客户端已启动！\n\n" + 
                              "新功能:\n" +
                              "• 专注命令行远程控制\n" +
                              "• 移除鼠标操作功能\n" +
                              "• 更简洁的用户界面\n" +
                              "• 点击'打开远程终端'使用命令行控制")
            
        except Exception as e:
            messagebox.showerror("启动失败", f"启动简化远程控制失败: {e}")
    
    def test_command_execution(self):
        """测试命令执行"""
        try:
            from native_control_utils import NativeController
            
            controller = NativeController()
            
            if not controller.enabled:
                messagebox.showwarning("测试失败", "控制器未启用，无法测试命令执行")
                return
            
            # 测试简单命令
            test_commands = []
            if self.system == 'windows':
                test_commands = ['echo Hello World', 'dir', 'whoami']
            else:
                test_commands = ['echo Hello World', 'pwd', 'whoami']
            
            results = []
            for cmd in test_commands:
                result = controller.execute_command(cmd)
                results.append(f"命令: {cmd}")
                if result['success']:
                    results.append(f"✅ 成功: {result['stdout'].strip()}")
                else:
                    results.append(f"❌ 失败: {result.get('error', result.get('stderr', '未知错误'))}")
                results.append("")
            
            # 显示结果
            result_window = tk.Toplevel(self.root)
            result_window.title("命令执行测试结果")
            result_window.geometry("600x400")
            
            text_widget = tk.Text(result_window, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.insert(tk.END, "\n".join(results))
            
        except Exception as e:
            messagebox.showerror("测试失败", f"命令执行测试失败: {e}")
    
    def open_terminal_directly(self):
        """直接打开终端"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                from native_control_utils import NativeRemoteControlManager
                from simple_remote_terminal import SimpleRemoteTerminal
                
                remote_manager = NativeRemoteControlManager(temp_dir)
                terminal = SimpleRemoteTerminal(self.root, remote_manager, "direct_user")
                
                messagebox.showinfo("终端已打开", 
                                  "远程终端已打开！\n\n" +
                                  "使用说明:\n" +
                                  "1. 点击'开始监听命令'启用\n" +
                                  "2. 在命令框中输入要执行的命令\n" +
                                  "3. 按回车或点击'发送'执行")
            
        except Exception as e:
            messagebox.showerror("打开失败", f"打开终端失败: {e}")
    
    def run(self):
        """运行启动器"""
        self.root.mainloop()

def main():
    """主函数"""
    print("🖥️ 简化远程控制启动器")
    print("专注命令行控制，移除鼠标操作")
    
    launcher = SimpleRemoteControlLauncher()
    launcher.run()

if __name__ == "__main__":
    main()