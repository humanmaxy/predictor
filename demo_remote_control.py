#!/usr/bin/env python3
"""
远程控制功能演示脚本
展示文件下载增强和远程控制功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tempfile
import os
from pathlib import Path
import threading
import time

# 导入我们的模块
from network_share_chat import NetworkShareChatClient
from remote_control_utils import RemoteControlManager, test_remote_control
from remote_control_gui import test_remote_control_gui

class RemoteControlDemo:
    """远程控制功能演示"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("网络共享聊天 - 远程控制功能演示")
        self.root.geometry("800x600")
        
        # 临时目录（模拟网络共享）
        self.temp_dir = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建演示界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="网络共享聊天 - 远程控制功能演示", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 功能说明
        info_frame = ttk.LabelFrame(main_frame, text="新增功能", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        features = [
            "✅ 文件下载功能增强：支持右键菜单选择下载位置",
            "✅ 屏幕共享：实时捕获和显示远程屏幕",
            "✅ 远程控制：支持鼠标点击、移动、滚轮和键盘输入",
            "✅ 基于共享目录：无需额外网络配置",
            "✅ 权限控制：可选择是否允许他人控制",
        ]
        
        for feature in features:
            label = ttk.Label(info_frame, text=feature, font=("Arial", 10))
            label.pack(anchor=tk.W, pady=2)
        
        # 演示按钮
        demo_frame = ttk.LabelFrame(main_frame, text="功能演示", padding=10)
        demo_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 按钮网格
        button_frame = ttk.Frame(demo_frame)
        button_frame.pack(fill=tk.X)
        
        # 第一行按钮
        row1_frame = ttk.Frame(button_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(row1_frame, text="🚀 启动聊天客户端", 
                  command=self.launch_chat_client, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(row1_frame, text="🧪 测试远程控制核心", 
                  command=self.test_remote_core, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(row1_frame, text="📺 测试屏幕共享GUI", 
                  command=self.test_screen_gui, width=20).pack(side=tk.LEFT)
        
        # 第二行按钮
        row2_frame = ttk.Frame(button_frame)
        row2_frame.pack(fill=tk.X)
        
        ttk.Button(row2_frame, text="📁 创建测试环境", 
                  command=self.setup_test_env, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(row2_frame, text="🔧 安装依赖", 
                  command=self.install_dependencies, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(row2_frame, text="❌ 清理环境", 
                  command=self.cleanup_test_env, width=20).pack(side=tk.LEFT)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始状态信息
        self.log("欢迎使用网络共享聊天远程控制功能演示!")
        self.log("请先点击 '安装依赖' 确保所有必需包已安装。")
        self.log("然后点击 '创建测试环境' 设置模拟的网络共享目录。")
        self.log("最后点击 '启动聊天客户端' 体验新功能。")
    
    def log(self, message):
        """添加日志信息"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def launch_chat_client(self):
        """启动聊天客户端"""
        try:
            self.log("启动网络共享聊天客户端...")
            
            # 在新线程中启动客户端
            def run_client():
                try:
                    client = NetworkShareChatClient()
                    client.run()
                except Exception as e:
                    self.log(f"客户端运行错误: {e}")
            
            thread = threading.Thread(target=run_client, daemon=True)
            thread.start()
            
            self.log("✅ 聊天客户端已启动")
            self.log("新功能说明:")
            self.log("- 文件下载：右键点击下载链接可选择保存位置")
            self.log("- 远程控制：在远程控制面板中启用屏幕共享和控制权限")
            
        except Exception as e:
            self.log(f"❌ 启动客户端失败: {e}")
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def test_remote_core(self):
        """测试远程控制核心功能"""
        try:
            self.log("测试远程控制核心功能...")
            
            def run_test():
                try:
                    test_remote_control()
                    self.log("✅ 远程控制核心功能测试完成")
                except Exception as e:
                    self.log(f"❌ 测试失败: {e}")
            
            thread = threading.Thread(target=run_test, daemon=True)
            thread.start()
            
        except Exception as e:
            self.log(f"❌ 测试启动失败: {e}")
    
    def test_screen_gui(self):
        """测试屏幕共享GUI"""
        try:
            self.log("启动屏幕共享GUI测试...")
            
            def run_gui_test():
                try:
                    test_remote_control_gui()
                    self.log("✅ 屏幕共享GUI测试完成")
                except Exception as e:
                    self.log(f"❌ GUI测试失败: {e}")
            
            thread = threading.Thread(target=run_gui_test, daemon=True)
            thread.start()
            
        except Exception as e:
            self.log(f"❌ GUI测试启动失败: {e}")
    
    def setup_test_env(self):
        """设置测试环境"""
        try:
            self.log("创建测试环境...")
            
            # 创建临时目录
            if self.temp_dir is None:
                self.temp_dir = tempfile.mkdtemp(prefix="chat_remote_test_")
            
            # 创建一些测试文件
            test_files = [
                ("test_document.txt", "这是一个测试文档文件。"),
                ("readme.md", "# 测试文件\n这是一个markdown文件。"),
                ("config.json", '{"test": true, "version": "1.0"}')
            ]
            
            for filename, content in test_files:
                file_path = Path(self.temp_dir) / filename
                file_path.write_text(content, encoding='utf-8')
            
            self.log(f"✅ 测试环境创建成功: {self.temp_dir}")
            self.log("测试文件已创建，可以在聊天客户端中使用此目录。")
            self.log("建议的共享路径设置:")
            self.log(f"  {self.temp_dir}")
            
        except Exception as e:
            self.log(f"❌ 创建测试环境失败: {e}")
            messagebox.showerror("错误", f"创建失败: {e}")
    
    def install_dependencies(self):
        """安装依赖"""
        try:
            self.log("启动依赖安装程序...")
            
            def run_install():
                try:
                    import subprocess
                    import sys
                    
                    # 运行安装脚本
                    result = subprocess.run([
                        sys.executable, "install_remote_control_deps.py"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.log("✅ 依赖安装完成")
                        self.log("输出:")
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.log(f"  {line}")
                    else:
                        self.log("❌ 依赖安装失败")
                        self.log("错误:")
                        for line in result.stderr.split('\n'):
                            if line.strip():
                                self.log(f"  {line}")
                    
                except Exception as e:
                    self.log(f"❌ 安装过程出错: {e}")
            
            thread = threading.Thread(target=run_install, daemon=True)
            thread.start()
            
        except Exception as e:
            self.log(f"❌ 启动安装失败: {e}")
    
    def cleanup_test_env(self):
        """清理测试环境"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log(f"✅ 测试环境已清理: {self.temp_dir}")
                self.temp_dir = None
            else:
                self.log("⚠️  没有需要清理的测试环境")
                
        except Exception as e:
            self.log(f"❌ 清理失败: {e}")
    
    def on_closing(self):
        """窗口关闭事件"""
        self.cleanup_test_env()
        self.root.destroy()
    
    def run(self):
        """运行演示"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """主函数"""
    try:
        demo = RemoteControlDemo()
        demo.run()
    except Exception as e:
        print(f"演示程序启动失败: {e}")
        messagebox.showerror("错误", f"启动失败: {e}")

if __name__ == "__main__":
    main()