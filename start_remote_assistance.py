#!/usr/bin/env python3
"""
远程协助启动器
提供多种方式启动远程协助功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import threading
import tempfile
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    missing_deps = []
    
    try:
        import pyautogui
        print(f"✅ PyAutoGUI已安装，版本: {pyautogui.__version__}")
    except ImportError:
        missing_deps.append("pyautogui")
        print("❌ PyAutoGUI未安装")
    
    try:
        from PIL import Image, ImageGrab
        print("✅ PIL/Pillow已安装")
    except ImportError:
        missing_deps.append("pillow")
        print("❌ PIL/Pillow未安装")
    
    return missing_deps

class RemoteAssistanceLauncher:
    """远程协助启动器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("远程协助启动器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 检查依赖
        self.missing_deps = check_dependencies()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🖥️ 远程协助启动器", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 依赖状态
        deps_frame = ttk.LabelFrame(main_frame, text="依赖检查", padding=10)
        deps_frame.pack(fill=tk.X, pady=(0, 15))
        
        if self.missing_deps:
            # 有缺失的依赖
            warning_label = ttk.Label(deps_frame, text="⚠️ 缺少以下依赖:", 
                                    foreground="red", font=("Arial", 10, "bold"))
            warning_label.pack(anchor=tk.W)
            
            for dep in self.missing_deps:
                dep_label = ttk.Label(deps_frame, text=f"  • {dep}", 
                                    foreground="red")
                dep_label.pack(anchor=tk.W)
            
            # 按钮框架
            btn_frame = ttk.Frame(deps_frame)
            btn_frame.pack(pady=(10, 0))
            
            install_btn = ttk.Button(btn_frame, text="🔧 安装缺失依赖", 
                                   command=self.install_dependencies)
            install_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            fix_btn = ttk.Button(btn_frame, text="🔧 修复PyAutoGUI", 
                               command=self.fix_pyautogui)
            fix_btn.pack(side=tk.LEFT)
        else:
            # 所有依赖都正常
            ok_label = ttk.Label(deps_frame, text="✅ 所有依赖都已安装，可以使用完整功能", 
                               foreground="green", font=("Arial", 10, "bold"))
            ok_label.pack()
            
            # 即使依赖正常也提供修复选项
            fix_btn = ttk.Button(deps_frame, text="🔧 诊断PyAutoGUI", 
                               command=self.fix_pyautogui)
            fix_btn.pack(pady=(5, 0))
        
        # 启动选项
        options_frame = ttk.LabelFrame(main_frame, text="启动选项", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 选项1：完整聊天客户端
        option1_frame = ttk.Frame(options_frame)
        option1_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(option1_frame, text="🚀 启动完整聊天客户端", 
                  command=self.launch_full_client, width=25).pack(side=tk.LEFT)
        ttk.Label(option1_frame, text="包含聊天、文件传输和远程协助功能", 
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 选项2：仅远程协助
        option2_frame = ttk.Frame(options_frame)
        option2_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(option2_frame, text="📺 仅启动远程协助", 
                  command=self.launch_remote_only, width=25).pack(side=tk.LEFT)
        ttk.Label(option2_frame, text="仅屏幕共享和远程控制功能", 
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 选项3：功能演示
        option3_frame = ttk.Frame(options_frame)
        option3_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(option3_frame, text="🧪 功能演示", 
                  command=self.launch_demo, width=25).pack(side=tk.LEFT)
        ttk.Label(option3_frame, text="演示和测试所有功能", 
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 选项4：测试依赖
        option4_frame = ttk.Frame(options_frame)
        option4_frame.pack(fill=tk.X)
        
        ttk.Button(option4_frame, text="🔍 测试依赖", 
                  command=self.test_dependencies, width=25).pack(side=tk.LEFT)
        ttk.Label(option4_frame, text="检查PyAutoGUI和PIL功能", 
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 快速设置
        setup_frame = ttk.LabelFrame(main_frame, text="快速设置", padding=10)
        setup_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 共享目录设置
        dir_frame = ttk.Frame(setup_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="共享目录:").pack(side=tk.LEFT)
        self.share_path_var = tk.StringVar()
        self.share_path_entry = ttk.Entry(dir_frame, textvariable=self.share_path_var, width=40)
        self.share_path_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="浏览", command=self.browse_share_path).pack(side=tk.RIGHT)
        
        # 用户信息
        user_frame = ttk.Frame(setup_frame)
        user_frame.pack(fill=tk.X)
        
        ttk.Label(user_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_var = tk.StringVar(value="远程用户")
        ttk.Entry(user_frame, textvariable=self.username_var, width=15).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(user_frame, text="用户ID:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.user_id_var = tk.StringVar(value="remote001")
        ttk.Entry(user_frame, textvariable=self.user_id_var, width=15).grid(row=0, column=3, sticky=tk.W)
        
        # 使用说明
        help_frame = ttk.LabelFrame(main_frame, text="使用说明", padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = """
远程协助功能使用说明:

1. 🔧 首次使用请先安装依赖 (PyAutoGUI + Pillow)

2. 📁 设置共享目录:
   • 可以是本地文件夹 (单机测试)
   • 可以是网络共享目录 (局域网使用)
   • 例如: \\\\server\\share 或 /mnt/share

3. 🚀 启动方式:
   • 完整客户端: 包含聊天+文件传输+远程协助
   • 仅远程协助: 只有屏幕共享和控制功能
   • 功能演示: 测试所有功能

4. 📺 远程协助操作:
   • 屏幕共享: 实时显示对方屏幕
   • 远程控制: 通过鼠标键盘控制对方电脑
   • 权限控制: 可选择是否允许被控制

5. 🔒 安全提醒:
   • 仅在信任的网络环境中使用
   • 及时关闭不需要的控制权限
        """
        
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, 
                              font=("Arial", 9))
        help_label.pack(anchor=tk.W)
    
    def browse_share_path(self):
        """浏览共享目录"""
        path = filedialog.askdirectory(title="选择共享目录")
        if path:
            self.share_path_var.set(path)
    
    def install_dependencies(self):
        """安装依赖"""
        def run_install():
            try:
                import subprocess
                import sys
                
                messagebox.showinfo("安装依赖", "正在安装依赖包，请稍候...")
                
                # 安装PyAutoGUI
                if "pyautogui" in self.missing_deps:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
                
                # 安装Pillow
                if "pillow" in self.missing_deps:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
                
                messagebox.showinfo("安装完成", "依赖安装完成！请重新启动程序。")
                
            except Exception as e:
                messagebox.showerror("安装失败", f"依赖安装失败: {e}")
        
        threading.Thread(target=run_install, daemon=True).start()
    
    def fix_pyautogui(self):
        """修复PyAutoGUI问题"""
        try:
            import subprocess
            import sys
            
            messagebox.showinfo("修复PyAutoGUI", "正在诊断和修复PyAutoGUI问题，请稍候...")
            
            def run_fix():
                try:
                    # 运行修复脚本
                    result = subprocess.run([sys.executable, "fix_pyautogui.py"], 
                                          capture_output=True, text=True, cwd=os.path.dirname(__file__))
                    
                    if "修复成功" in result.stdout or "SUCCESS" in result.stdout:
                        messagebox.showinfo("修复完成", "PyAutoGUI修复成功！请重新启动程序测试。")
                    else:
                        # 显示详细结果
                        result_window = tk.Toplevel(self.root)
                        result_window.title("修复结果")
                        result_window.geometry("700x500")
                        
                        text_widget = tk.Text(result_window, wrap=tk.WORD)
                        scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=text_widget.yview)
                        text_widget.configure(yscrollcommand=scrollbar.set)
                        
                        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                        
                        text_widget.insert(tk.END, "修复输出:\n")
                        text_widget.insert(tk.END, result.stdout)
                        if result.stderr:
                            text_widget.insert(tk.END, "\n错误信息:\n")
                            text_widget.insert(tk.END, result.stderr)
                    
                except Exception as e:
                    messagebox.showerror("修复失败", f"修复过程出错: {e}")
            
            threading.Thread(target=run_fix, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("修复失败", f"无法启动修复: {e}")
    
    def launch_full_client(self):
        """启动完整聊天客户端"""
        try:
            # 设置环境变量传递参数
            if self.share_path_var.get():
                os.environ['CHAT_SHARE_PATH'] = self.share_path_var.get()
            if self.username_var.get():
                os.environ['CHAT_USERNAME'] = self.username_var.get()
            if self.user_id_var.get():
                os.environ['CHAT_USER_ID'] = self.user_id_var.get()
            
            # 启动客户端
            from network_share_chat import NetworkShareChatClient
            
            def run_client():
                client = NetworkShareChatClient()
                # 如果有预设参数，自动填入
                if self.share_path_var.get():
                    client.share_path_var.set(self.share_path_var.get())
                if self.username_var.get():
                    client.username_var.set(self.username_var.get())
                if self.user_id_var.get():
                    client.user_id_var.set(self.user_id_var.get())
                client.run()
            
            threading.Thread(target=run_client, daemon=True).start()
            messagebox.showinfo("启动成功", "聊天客户端已启动！\n可以在远程控制面板中启用屏幕共享和远程控制功能。")
            
        except Exception as e:
            messagebox.showerror("启动失败", f"启动客户端失败: {e}")
    
    def launch_remote_only(self):
        """仅启动远程协助"""
        try:
            from remote_control_gui import test_remote_control_gui
            
            def run_remote():
                test_remote_control_gui()
            
            threading.Thread(target=run_remote, daemon=True).start()
            messagebox.showinfo("启动成功", "远程协助界面已启动！")
            
        except Exception as e:
            messagebox.showerror("启动失败", f"启动远程协助失败: {e}")
    
    def launch_demo(self):
        """启动功能演示"""
        try:
            from demo_remote_control import RemoteControlDemo
            
            def run_demo():
                demo = RemoteControlDemo()
                demo.run()
            
            threading.Thread(target=run_demo, daemon=True).start()
            messagebox.showinfo("启动成功", "功能演示已启动！")
            
        except Exception as e:
            messagebox.showerror("启动失败", f"启动演示失败: {e}")
    
    def test_dependencies(self):
        """测试依赖"""
        try:
            import subprocess
            import sys
            
            # 运行测试脚本
            result = subprocess.run([sys.executable, "test_pyautogui.py"], 
                                  capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            # 显示结果
            result_window = tk.Toplevel(self.root)
            result_window.title("依赖测试结果")
            result_window.geometry("600x400")
            
            text_widget = tk.Text(result_window, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.insert(tk.END, result.stdout)
            if result.stderr:
                text_widget.insert(tk.END, "\n错误信息:\n")
                text_widget.insert(tk.END, result.stderr)
            
        except Exception as e:
            messagebox.showerror("测试失败", f"依赖测试失败: {e}")
    
    def run(self):
        """运行启动器"""
        self.root.mainloop()

def main():
    """主函数"""
    print("🖥️ 远程协助启动器")
    print("检查依赖...")
    
    launcher = RemoteAssistanceLauncher()
    launcher.run()

if __name__ == "__main__":
    main()