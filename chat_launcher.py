#!/usr/bin/env python3
"""
聊天工具启动器
支持WebSocket实时聊天和COS云端聊天两种模式
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class ChatLauncher:
    """聊天工具启动器"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("聊天工具启动器")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 设置窗口居中
        self.center_window()
        
        # 创建界面
        self.create_widgets()
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"600x400+{x}+{y}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_frame = ttk.Frame(self.root, padding="20")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(title_frame, text="🎯 聊天工具启动器", 
                               font=("Arial", 18, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="选择您喜欢的聊天模式", 
                                  font=("Arial", 12))
        subtitle_label.pack(pady=(5, 0))
        
        # 分隔线
        separator = ttk.Separator(self.root, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=20, pady=10)
        
        # 选项区域
        options_frame = ttk.Frame(self.root, padding="20")
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # WebSocket模式
        websocket_frame = ttk.LabelFrame(options_frame, text="🌐 WebSocket实时聊天", padding="15")
        websocket_frame.pack(fill=tk.X, pady=(0, 15))
        
        ws_desc = ttk.Label(websocket_frame, 
                           text="• 基于WebSocket协议的实时聊天\n• 支持局域网和互联网连接\n• 群聊和私聊功能\n• 低延迟，实时性强",
                           font=("Arial", 10))
        ws_desc.pack(anchor=tk.W, pady=(0, 10))
        
        ws_btn_frame = ttk.Frame(websocket_frame)
        ws_btn_frame.pack(fill=tk.X)
        
        ttk.Button(ws_btn_frame, text="启动客户端", 
                  command=self.start_websocket_client).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ws_btn_frame, text="启动服务器", 
                  command=self.start_websocket_server).pack(side=tk.LEFT)
        
        # COS云端模式
        cos_frame = ttk.LabelFrame(options_frame, text="☁️ COS云端聊天", padding="15")
        cos_frame.pack(fill=tk.X, pady=(0, 15))
        
        cos_desc = ttk.Label(cos_frame,
                            text="• 基于腾讯云COS的云端聊天\n• 聊天记录永久存储在云端\n• 跨设备同步聊天记录\n• 无需服务器，直接使用云存储",
                            font=("Arial", 10))
        cos_desc.pack(anchor=tk.W, pady=(0, 10))
        
        cos_btn_frame = ttk.Frame(cos_frame)
        cos_btn_frame.pack(fill=tk.X)
        
        ttk.Button(cos_btn_frame, text="启动COS聊天", 
                  command=self.start_cos_client).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(cos_btn_frame, text="查看演示", 
                  command=self.show_cos_demo).pack(side=tk.LEFT)
        
        # 网络共享模式
        share_frame = ttk.LabelFrame(options_frame, text="📁 网络共享目录聊天", padding="15")
        share_frame.pack(fill=tk.X, pady=(0, 15))
        
        share_desc = ttk.Label(share_frame,
                              text="• 基于局域网共享目录的聊天\n• 消息存储在指定网络目录\n• 每天凌晨2点自动清理\n• 适合企业内网环境",
                              font=("Arial", 10))
        share_desc.pack(anchor=tk.W, pady=(0, 10))
        
        share_btn_frame = ttk.Frame(share_frame)
        share_btn_frame.pack(fill=tk.X)
        
        ttk.Button(share_btn_frame, text="启动共享聊天", 
                  command=self.start_network_share_client).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(share_btn_frame, text="清理工具", 
                  command=self.start_cleanup_tool).pack(side=tk.LEFT)
        
        # 工具区域
        tools_frame = ttk.LabelFrame(options_frame, text="🔧 工具和配置", padding="15")
        tools_frame.pack(fill=tk.X)
        
        tools_btn_frame = ttk.Frame(tools_frame)
        tools_btn_frame.pack(fill=tk.X)
        
        ttk.Button(tools_btn_frame, text="SSL证书生成", 
                  command=self.generate_ssl_cert).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_btn_frame, text="依赖检查", 
                  command=self.check_dependencies).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tools_btn_frame, text="快速启动", 
                  command=self.quick_start).pack(side=tk.LEFT)
        
        # 底部信息
        info_frame = ttk.Frame(self.root, padding="20")
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        info_label = ttk.Label(info_frame, 
                              text="💡 提示：WebSocket适合实时聊天，COS适合跨网络聊天，共享目录适合企业内网",
                              font=("Arial", 9), foreground="gray")
        info_label.pack()
    
    def start_websocket_client(self):
        """启动WebSocket客户端"""
        try:
            subprocess.Popen([sys.executable, "chat_client.py"])
            self.show_info("WebSocket客户端", "WebSocket聊天客户端已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动WebSocket客户端: {str(e)}")
    
    def start_websocket_server(self):
        """启动WebSocket服务器"""
        try:
            subprocess.Popen([sys.executable, "quick_start.py"])
            self.show_info("WebSocket服务器", "服务器启动工具已打开")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动服务器工具: {str(e)}")
    
    def start_cos_client(self):
        """启动COS聊天客户端"""
        try:
            subprocess.Popen([sys.executable, "cos_chat_client.py"])
            self.show_info("COS聊天", "COS云端聊天客户端已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动COS聊天客户端: {str(e)}")
    
    def show_cos_demo(self):
        """显示COS演示"""
        try:
            subprocess.Popen([sys.executable, "cos_chat_demo.py"])
            self.show_info("COS演示", "COS聊天演示已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动COS演示: {str(e)}")
    
    def generate_ssl_cert(self):
        """生成SSL证书"""
        try:
            subprocess.Popen([sys.executable, "generate_ssl_cert.py"])
            self.show_info("SSL工具", "SSL证书生成工具已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动SSL工具: {str(e)}")
    
    def check_dependencies(self):
        """检查依赖"""
        try:
            subprocess.Popen([sys.executable, "install_cos_dependencies.py"])
            self.show_info("依赖检查", "依赖检查工具已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动依赖检查: {str(e)}")
    
    def quick_start(self):
        """快速启动"""
        try:
            subprocess.Popen([sys.executable, "quick_start.py"])
            self.show_info("快速启动", "快速启动工具已打开")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动快速启动工具: {str(e)}")
    
    def start_network_share_client(self):
        """启动网络共享聊天客户端"""
        try:
            subprocess.Popen([sys.executable, "network_share_chat.py"])
            self.show_info("网络共享聊天", "网络共享目录聊天客户端已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动网络共享聊天客户端: {str(e)}")
    
    def start_cleanup_tool(self):
        """启动清理工具"""
        try:
            subprocess.Popen([sys.executable, "network_share_cleanup.py"])
            self.show_info("清理工具", "网络共享清理工具已启动")
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动清理工具: {str(e)}")
    
    def show_info(self, title: str, message: str):
        """显示信息"""
        messagebox.showinfo(title, message)
    
    def run(self):
        """运行启动器"""
        self.root.mainloop()

def main():
    """主函数"""
    try:
        launcher = ChatLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("启动器已停止")

if __name__ == "__main__":
    main()