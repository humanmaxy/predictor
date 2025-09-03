#!/usr/bin/env python3
"""
原生远程控制启动器
无需PyAutoGUI依赖，使用系统原生方法
"""

import tkinter as tk
from tkinter import ttk, messagebox
import platform
import sys
import os
from pathlib import Path

class NativeRemoteControlLauncher:
    """原生远程控制启动器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("原生远程控制启动器")
        self.root.geometry("700x600")
        
        self.system = platform.system().lower()
        self.system_support = self._check_system_support()
        
        self._create_widgets()
    
    def _check_system_support(self):
        """检查系统支持情况"""
        support_info = {
            'system': self.system,
            'screen_capture': True,  # PIL ImageGrab 支持所有系统
            'mouse_control': False,
            'keyboard_control': False,
            'requirements': []
        }
        
        if self.system == 'windows':
            support_info['mouse_control'] = True
            support_info['keyboard_control'] = True
            support_info['requirements'] = ['Windows内置API (ctypes)']
        elif self.system == 'darwin':  # macOS
            try:
                import subprocess
                result = subprocess.run(['which', 'osascript'], capture_output=True)
                if result.returncode == 0:
                    support_info['mouse_control'] = True
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
                    support_info['mouse_control'] = True
                    support_info['keyboard_control'] = True
                    requirements.append('xdotool (已安装)')
                else:
                    requirements.append('需要安装: sudo apt-get install xdotool')
                
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
        title_label = ttk.Label(main_frame, text="🖥️ 原生远程控制启动器", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="无需PyAutoGUI依赖，使用系统原生方法", 
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
            ("鼠标控制", self.system_support['mouse_control'], "系统原生API"),
            ("键盘控制", self.system_support['keyboard_control'], "系统原生API")
        ]
        
        for feature_name, supported, method in features:
            frame = ttk.Frame(support_frame)
            frame.pack(fill=tk.X, pady=2)
            
            status = "✅" if supported else "❌"
            color = "green" if supported else "red"
            
            ttk.Label(frame, text=f"{status} {feature_name}:", 
                     foreground=color).pack(side=tk.LEFT)
            ttk.Label(frame, text=method, font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 系统要求
        if self.system_support['requirements']:
            ttk.Label(support_frame, text="系统要求:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
            for req in self.system_support['requirements']:
                ttk.Label(support_frame, text=f"  • {req}", font=("Arial", 9)).pack(anchor=tk.W)
        
        # 功能对比
        compare_frame = ttk.LabelFrame(main_frame, text="功能对比", padding=10)
        compare_frame.pack(fill=tk.X, pady=(0, 15))
        
        comparison_text = """
原生控制 vs PyAutoGUI:

✅ 原生控制优势:
  • 无需安装额外依赖包
  • 更轻量级，启动更快
  • 直接使用系统API，更稳定
  • 避免PyAutoGUI的安装和兼容性问题

⚠️ 原生控制限制:
  • 不同系统实现方式不同
  • Linux需要安装xdotool
  • macOS可能需要权限设置

🔄 PyAutoGUI优势:
  • 跨平台统一接口
  • 功能更丰富
  • 社区支持更好
        """
        
        compare_label = ttk.Label(compare_frame, text=comparison_text, 
                                font=("Arial", 9), justify=tk.LEFT)
        compare_label.pack(anchor=tk.W)
        
        # 启动按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 原生控制启动
        native_btn = ttk.Button(button_frame, text="🚀 启动原生远程控制", 
                              command=self.launch_native_control, width=25)
        native_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 测试按钮
        test_btn = ttk.Button(button_frame, text="🧪 测试原生控制", 
                            command=self.test_native_control, width=20)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 安装依赖按钮（Linux）
        if self.system == 'linux' and not self.system_support['mouse_control']:
            install_btn = ttk.Button(button_frame, text="📦 安装Linux依赖", 
                                   command=self.install_linux_deps, width=20)
            install_btn.pack(side=tk.LEFT)
        
        # 使用说明
        help_frame = ttk.LabelFrame(main_frame, text="使用说明", padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = """
使用步骤:

1. 检查系统支持状态 (上方显示)

2. Windows用户:
   • 直接点击"启动原生远程控制"即可使用所有功能

3. macOS用户:
   • 首次使用可能需要在"系统偏好设置 > 安全性与隐私 > 辅助功能"中允许终端或Python
   • 点击"启动原生远程控制"

4. Linux用户:
   • 如果显示需要安装xdotool，点击"安装Linux依赖"
   • 确保在X11环境中运行
   • 点击"启动原生远程控制"

5. 功能说明:
   • 屏幕共享: 实时捕获和传输屏幕内容
   • 远程控制: 通过鼠标键盘控制远程电脑
   • 基于共享目录: 无需额外网络配置

注意事项:
• 仅在信任的网络环境中使用
• 及时关闭不需要的控制权限
• Linux用户需要xdotool工具
• macOS用户可能需要授权辅助功能权限
        """
        
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, 
                              font=("Arial", 9))
        help_label.pack(anchor=tk.W)
    
    def launch_native_control(self):
        """启动原生远程控制"""
        try:
            # 检查是否支持
            if not self.system_support['screen_capture']:
                messagebox.showerror("不支持", "当前系统不支持屏幕捕获功能")
                return
            
            # 启动主程序
            from network_share_chat import NetworkShareChatClient
            
            def run_client():
                client = NetworkShareChatClient()
                client.run()
            
            import threading
            threading.Thread(target=run_client, daemon=True).start()
            
            messagebox.showinfo("启动成功", 
                              "原生远程控制聊天客户端已启动！\n\n" + 
                              "功能说明:\n" +
                              "• 无需PyAutoGUI依赖\n" +
                              "• 使用系统原生控制方法\n" +
                              "• 在远程控制面板中启用功能")
            
        except Exception as e:
            messagebox.showerror("启动失败", f"启动原生远程控制失败: {e}")
    
    def test_native_control(self):
        """测试原生控制功能"""
        try:
            from native_control_utils import test_native_control
            
            def run_test():
                test_native_control()
            
            import threading
            threading.Thread(target=run_test, daemon=True).start()
            
            messagebox.showinfo("测试启动", "原生控制功能测试已启动，请查看控制台输出")
            
        except Exception as e:
            messagebox.showerror("测试失败", f"测试启动失败: {e}")
    
    def install_linux_deps(self):
        """安装Linux依赖"""
        if self.system != 'linux':
            messagebox.showwarning("不适用", "此功能仅适用于Linux系统")
            return
        
        try:
            import subprocess
            import tkinter.simpledialog as simpledialog
            
            # 询问是否安装
            result = messagebox.askyesno("安装依赖", 
                                       "将执行以下命令安装xdotool:\n\n" +
                                       "sudo apt-get update\n" +
                                       "sudo apt-get install xdotool\n\n" +
                                       "是否继续？")
            
            if result:
                # 在终端中执行安装命令
                commands = [
                    "sudo apt-get update",
                    "sudo apt-get install -y xdotool"
                ]
                
                messagebox.showinfo("执行安装", 
                                  "即将在终端中执行安装命令，请输入sudo密码。\n\n" +
                                  "安装完成后请重新启动此程序。")
                
                # 打开终端执行命令
                cmd = " && ".join(commands)
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 
                                f'{cmd}; echo "安装完成，按任意键关闭"; read'])
                
        except Exception as e:
            messagebox.showerror("安装失败", f"无法执行安装: {e}")
    
    def run(self):
        """运行启动器"""
        self.root.mainloop()

def main():
    """主函数"""
    print("🖥️ 原生远程控制启动器")
    print("无需PyAutoGUI依赖，使用系统原生方法")
    
    launcher = NativeRemoteControlLauncher()
    launcher.run()

if __name__ == "__main__":
    main()