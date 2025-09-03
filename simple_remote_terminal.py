#!/usr/bin/env python3
"""
简洁的远程命令行控制界面
通过输入框直接执行远程命令
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
from datetime import datetime
from pathlib import Path
from native_control_utils import NativeRemoteControlManager

class SimpleRemoteTerminal:
    """简洁的远程终端控制器"""
    
    def __init__(self, parent, remote_manager: NativeRemoteControlManager, user_id: str):
        self.parent = parent
        self.remote_manager = remote_manager
        self.user_id = user_id
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("远程命令行控制")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # 状态
        self.is_listening = False
        self.command_history = []
        self.history_index = -1
        
        self._create_widgets()
        self._setup_events()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题和状态
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🖥️ 远程命令行控制", 
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header_frame, text="未连接", 
                                    foreground="red", font=("Arial", 10))
        self.status_label.pack(side=tk.RIGHT)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connect_btn = ttk.Button(control_frame, text="开始监听命令", 
                                    command=self.toggle_listening)
        self.connect_btn.pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="清空输出", 
                  command=self.clear_output).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(control_frame, text="保存日志", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(10, 0))
        
        # 输出区域
        output_frame = ttk.LabelFrame(main_frame, text="命令输出", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            height=20,
            font=("Consolas", 10),
            bg="black",
            fg="green",
            insertbackground="white"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 命令输入区域
        input_frame = ttk.LabelFrame(main_frame, text="发送命令", padding=5)
        input_frame.pack(fill=tk.X)
        
        # 命令输入框
        cmd_frame = ttk.Frame(input_frame)
        cmd_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(cmd_frame, text="命令:").pack(side=tk.LEFT)
        
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(cmd_frame, textvariable=self.command_var, 
                                     font=("Consolas", 10))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.send_btn = ttk.Button(cmd_frame, text="发送", command=self.send_command)
        self.send_btn.pack(side=tk.RIGHT)
        
        # 快捷命令按钮
        shortcuts_frame = ttk.Frame(input_frame)
        shortcuts_frame.pack(fill=tk.X)
        
        shortcuts = [
            ("pwd", "显示当前目录"),
            ("ls", "列出文件 (Linux/Mac)"),
            ("dir", "列出文件 (Windows)"),
            ("whoami", "显示当前用户"),
            ("date", "显示日期时间"),
            ("clear", "清屏")
        ]
        
        for i, (cmd, desc) in enumerate(shortcuts):
            if i % 3 == 0:
                row_frame = ttk.Frame(shortcuts_frame)
                row_frame.pack(fill=tk.X, pady=2)
            
            btn = ttk.Button(row_frame, text=f"{cmd}", 
                           command=lambda c=cmd: self.send_quick_command(c),
                           width=12)
            btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 初始输出
        self.add_output("=== 远程命令行控制台 ===")
        self.add_output("使用说明:")
        self.add_output("1. 点击'开始监听命令'启用远程控制")
        self.add_output("2. 在命令框中输入要执行的命令")
        self.add_output("3. 按回车或点击'发送'执行命令")
        self.add_output("4. 使用上下箭头键浏览命令历史")
        self.add_output("")
    
    def _setup_events(self):
        """设置事件绑定"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 回车发送命令
        self.command_entry.bind('<Return>', lambda e: self.send_command())
        
        # 命令历史导航
        self.command_entry.bind('<Up>', self.previous_command)
        self.command_entry.bind('<Down>', self.next_command)
        
        # 焦点设置
        self.command_entry.focus_set()
    
    def toggle_listening(self):
        """切换监听状态"""
        if not self.is_listening:
            if self.remote_manager.start_remote_control_listening(self.user_id):
                self.is_listening = True
                self.connect_btn.config(text="停止监听")
                self.status_label.config(text="正在监听", foreground="green")
                self.add_output("✅ 开始监听远程命令")
            else:
                messagebox.showerror("错误", "无法启动远程控制监听")
        else:
            self.remote_manager.stop_remote_control_listening()
            self.is_listening = False
            self.connect_btn.config(text="开始监听命令")
            self.status_label.config(text="未连接", foreground="red")
            self.add_output("⏹️ 停止监听远程命令")
    
    def send_command(self):
        """发送命令"""
        command = self.command_var.get().strip()
        if not command:
            return
        
        if not self.is_listening:
            messagebox.showwarning("未连接", "请先开始监听命令")
            return
        
        # 添加到历史
        if command not in self.command_history:
            self.command_history.append(command)
            if len(self.command_history) > 50:  # 限制历史记录数量
                self.command_history.pop(0)
        self.history_index = -1
        
        # 显示发送的命令
        self.add_output(f"$ {command}", "command")
        
        # 发送命令
        command_data = {
            'type': 'execute_command',
            'command': command,
            'timestamp': datetime.now().isoformat()
        }
        
        success = self.remote_manager.send_control_command(command_data)
        if success:
            self.add_output("命令已发送...", "info")
        else:
            self.add_output("❌ 命令发送失败", "error")
        
        # 清空输入框
        self.command_var.set("")
    
    def send_quick_command(self, command):
        """发送快捷命令"""
        self.command_var.set(command)
        self.send_command()
    
    def previous_command(self, event):
        """上一个命令"""
        if self.command_history:
            if self.history_index == -1:
                self.history_index = len(self.command_history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
            
            self.command_var.set(self.command_history[self.history_index])
            self.command_entry.icursor(tk.END)
        return "break"
    
    def next_command(self, event):
        """下一个命令"""
        if self.command_history and self.history_index != -1:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_var.set(self.command_history[self.history_index])
            else:
                self.history_index = -1
                self.command_var.set("")
            self.command_entry.icursor(tk.END)
        return "break"
    
    def add_output(self, text, tag=None):
        """添加输出文本"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.output_text.config(state=tk.NORMAL)
        
        if tag == "command":
            self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.output_text.insert(tk.END, f"{text}\n", "command")
        elif tag == "error":
            self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.output_text.insert(tk.END, f"{text}\n", "error")
        elif tag == "info":
            self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.output_text.insert(tk.END, f"{text}\n", "info")
        else:
            self.output_text.insert(tk.END, f"[{timestamp}] {text}\n")
        
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(tk.END)
        
        # 配置标签样式
        self.output_text.tag_config("timestamp", foreground="cyan")
        self.output_text.tag_config("command", foreground="yellow")
        self.output_text.tag_config("error", foreground="red")
        self.output_text.tag_config("info", foreground="blue")
    
    def clear_output(self):
        """清空输出"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.add_output("输出已清空")
    
    def save_log(self):
        """保存日志"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存命令日志"
            )
            
            if filename:
                content = self.output_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.add_output(f"日志已保存到: {filename}", "info")
                
        except Exception as e:
            messagebox.showerror("保存失败", f"保存日志失败: {e}")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_listening:
            self.remote_manager.stop_remote_control_listening()
        self.window.destroy()

class SimpleRemoteControlPanel:
    """简化的远程控制面板 - 仅命令行控制"""
    
    def __init__(self, parent_frame, remote_manager: NativeRemoteControlManager, user_id: str):
        self.parent_frame = parent_frame
        self.remote_manager = remote_manager
        self.user_id = user_id
        
        # 终端窗口
        self.terminal_window = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建远程控制面板"""
        # 远程控制框架 - 使用grid布局
        self.remote_frame = ttk.LabelFrame(self.parent_frame, text="远程命令行控制", padding=5)
        
        # 获取当前网格行数并放置在下一行
        try:
            grid_slaves = self.parent_frame.grid_slaves()
            if grid_slaves:
                rows = []
                for child in grid_slaves:
                    grid_info = child.grid_info()
                    if 'row' in grid_info and grid_info['row'] is not None:
                        rows.append(grid_info['row'])
                max_row = max(rows) if rows else 4
            else:
                max_row = 4
            self.remote_frame.grid(row=max_row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        except Exception as e:
            print(f"Grid布局检测失败，使用固定位置: {e}")
            self.remote_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(self.remote_frame)
        button_frame.pack(fill=tk.X)
        
        # 命令行控制按钮
        self.terminal_btn = ttk.Button(
            button_frame, text="🖥️ 打开远程终端", 
            command=self.open_terminal_window
        )
        self.terminal_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态显示
        controller_enabled = self.remote_manager.controller.enabled
        if controller_enabled:
            status_text = f"命令行控制就绪 ({self.remote_manager.controller.system})"
            status_color = "green"
        else:
            status_text = f"命令行控制不可用 ({self.remote_manager.controller.system})"
            status_color = "red"
        
        self.status_var = tk.StringVar(value=status_text)
        self.status_label = ttk.Label(button_frame, textvariable=self.status_var, 
                                    font=("Arial", 8), foreground=status_color)
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 快速控制选项
        options_frame = ttk.Frame(self.remote_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 允许被控制
        self.allow_control_var = tk.BooleanVar()
        self.allow_control_cb = ttk.Checkbutton(
            options_frame, text="允许远程执行命令",
            variable=self.allow_control_var,
            command=self.toggle_allow_control
        )
        self.allow_control_cb.pack(side=tk.LEFT)
        
        # 说明文本
        help_text = "通过远程终端可以执行系统命令、查看文件、管理进程等"
        ttk.Label(options_frame, text=help_text, font=("Arial", 8), 
                 foreground="gray").pack(side=tk.LEFT, padx=(20, 0))
        
        # 如果控制器不可用，禁用选项
        if not controller_enabled:
            self.allow_control_cb.config(state='disabled')
            self.terminal_btn.config(state='disabled')
    
    def open_terminal_window(self):
        """打开远程终端窗口"""
        if self.terminal_window is None or not self.terminal_window.window.winfo_exists():
            self.terminal_window = SimpleRemoteTerminal(
                self.parent_frame.winfo_toplevel(), 
                self.remote_manager, 
                self.user_id
            )
        else:
            self.terminal_window.window.lift()
            self.terminal_window.window.focus_set()
    
    def toggle_allow_control(self):
        """切换允许控制状态"""
        if not self.remote_manager.controller.enabled:
            messagebox.showwarning("功能不可用", "当前系统不支持命令行远程控制")
            self.allow_control_var.set(False)
            return
        
        if self.allow_control_var.get():
            if self.remote_manager.start_remote_control_listening(self.user_id):
                self.status_var.set("正在监听远程命令...")
            else:
                self.allow_control_var.set(False)
                messagebox.showerror("错误", "无法启动远程控制监听")
        else:
            self.remote_manager.stop_remote_control_listening()
            controller_enabled = self.remote_manager.controller.enabled
            if controller_enabled:
                self.status_var.set(f"命令行控制就绪 ({self.remote_manager.controller.system})")

def test_simple_terminal():
    """测试简单终端"""
    import tempfile
    
    root = tk.Tk()
    root.title("简单远程终端测试")
    root.geometry("600x400")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        remote_manager = NativeRemoteControlManager(temp_dir)
        
        # 创建远程控制面板
        panel = SimpleRemoteControlPanel(root, remote_manager, "test_user")
        
        root.mainloop()

if __name__ == "__main__":
    test_simple_terminal()