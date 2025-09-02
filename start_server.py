#!/usr/bin/env python3
"""
聊天服务器启动脚本
提供简单的配置界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import os
import sys
import platform

class ServerLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("聊天服务器启动器")
        self.root.geometry("500x400")
        
        self.server_process = None
        self.create_widgets()
        self.check_environment()
    
    def get_python_executable(self):
        """获取正确的Python可执行文件路径（跨平台支持）"""
        # 首先尝试虚拟环境中的Python
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if platform.system() == "Windows":
            # Windows系统路径 - 尝试多个可能的文件名
            possible_paths = [
                os.path.join(script_dir, "venv", "Scripts", "python.exe"),
                os.path.join(script_dir, "venv", "Scripts", "python3.exe"),
            ]
        else:
            # Linux/Mac系统路径
            possible_paths = [
                os.path.join(script_dir, "venv", "bin", "python3"),
                os.path.join(script_dir, "venv", "bin", "python"),
            ]
        
        # 检查虚拟环境中的Python
        for venv_python in possible_paths:
            if os.path.exists(venv_python):
                return venv_python
        
        # 回退选项：尝试当前Python解释器
        current_python = sys.executable
        if current_python and os.path.exists(current_python):
            return current_python
        
        # 最后回退：使用系统Python命令
        if platform.system() == "Windows":
            # Windows上尝试多个命令
            for cmd in ["python", "python3", "py"]:
                try:
                    # 测试命令是否可用
                    result = subprocess.run([cmd, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return cmd
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            return "python"  # 默认回退
        else:
            return "python3"
    
    def check_environment(self):
        """检查运行环境并显示信息"""
        python_cmd = self.get_python_executable()
        
        # 显示环境信息
        self.log_message(f"操作系统: {platform.system()} {platform.release()}")
        self.log_message(f"Python路径: {python_cmd}")
        
        # 检查Python是否可用
        try:
            if os.path.exists(python_cmd):
                result = subprocess.run([python_cmd, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip()
                    self.log_message(f"Python版本: {version}")
                else:
                    self.log_message(f"警告: Python命令执行失败")
            else:
                self.log_message(f"警告: Python可执行文件不存在: {python_cmd}")
        except Exception as e:
            self.log_message(f"警告: 无法检查Python版本: {e}")
        
        # 检查依赖包
        try:
            if os.path.exists(python_cmd):
                result = subprocess.run([python_cmd, "-c", "import websockets; print('websockets版本:', websockets.__version__)"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_message(result.stdout.strip())
                else:
                    self.log_message("警告: websockets包未安装或无法导入")
                    self.log_message("请运行 setup_windows.bat 来安装依赖")
        except Exception as e:
            self.log_message(f"警告: 无法检查依赖包: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="聊天服务器配置", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 主机地址
        ttk.Label(main_frame, text="主机地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar(value="localhost")
        host_entry = ttk.Entry(main_frame, textvariable=self.host_var)
        host_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 端口
        ttk.Label(main_frame, text="端口:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value="8765")
        port_entry = ttk.Entry(main_frame, textvariable=self.port_var)
        port_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # SSL选项
        self.ssl_var = tk.BooleanVar()
        ssl_check = ttk.Checkbutton(main_frame, text="启用HTTPS/SSL", variable=self.ssl_var,
                                   command=self.toggle_ssl_options)
        ssl_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # SSL证书文件
        self.cert_frame = ttk.Frame(main_frame)
        self.cert_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.cert_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.cert_frame, text="证书文件:").grid(row=0, column=0, sticky=tk.W)
        self.cert_var = tk.StringVar()
        cert_entry = ttk.Entry(self.cert_frame, textvariable=self.cert_var)
        cert_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        cert_btn = ttk.Button(self.cert_frame, text="浏览", command=self.browse_cert_file)
        cert_btn.grid(row=0, column=2)
        
        # SSL私钥文件
        ttk.Label(self.cert_frame, text="私钥文件:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.key_var = tk.StringVar()
        key_entry = ttk.Entry(self.cert_frame, textvariable=self.key_var)
        key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=(5, 0))
        key_btn = ttk.Button(self.cert_frame, text="浏览", command=self.browse_key_file)
        key_btn.grid(row=1, column=2, pady=(5, 0))
        
        # 初始隐藏SSL选项
        self.cert_frame.grid_remove()
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="启动服务器", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.client_btn = ttk.Button(button_frame, text="启动客户端", command=self.start_client)
        self.client_btn.pack(side=tk.LEFT)
        
        # 状态显示
        self.status_var = tk.StringVar(value="服务器未启动")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 10))
        status_label.grid(row=6, column=0, columnspan=2, pady=10)
        
        # 日志显示
        log_frame = ttk.LabelFrame(main_frame, text="服务器日志", padding="5")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.log_display = tk.Text(log_frame, height=8, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_display.yview)
        self.log_display.configure(yscrollcommand=scrollbar.set)
        
        self.log_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def toggle_ssl_options(self):
        """切换SSL选项显示"""
        if self.ssl_var.get():
            self.cert_frame.grid()
        else:
            self.cert_frame.grid_remove()
    
    def browse_cert_file(self):
        """浏览证书文件"""
        filename = filedialog.askopenfilename(
            title="选择SSL证书文件",
            filetypes=[("证书文件", "*.crt *.pem"), ("所有文件", "*.*")]
        )
        if filename:
            self.cert_var.set(filename)
    
    def browse_key_file(self):
        """浏览私钥文件"""
        filename = filedialog.askopenfilename(
            title="选择SSL私钥文件",
            filetypes=[("私钥文件", "*.key *.pem"), ("所有文件", "*.*")]
        )
        if filename:
            self.key_var.set(filename)
    
    def log_message(self, message: str):
        """添加日志消息"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, f"{message}\n")
        self.log_display.config(state=tk.DISABLED)
        self.log_display.see(tk.END)
    
    def start_server(self):
        """启动服务器"""
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return
        
        host = self.host_var.get().strip()
        if not host:
            messagebox.showerror("错误", "请输入主机地址")
            return
        
        # 构建命令 - 使用跨平台的Python路径
        python_cmd = self.get_python_executable()
        server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_server.py")
        cmd = [python_cmd, server_script, "--host", host, "--port", str(port)]
        
        if self.ssl_var.get():
            cert_file = self.cert_var.get().strip()
            key_file = self.key_var.get().strip()
            
            if not cert_file or not key_file:
                messagebox.showerror("错误", "启用SSL时需要提供证书和私钥文件")
                return
            
            if not os.path.exists(cert_file):
                messagebox.showerror("错误", f"证书文件不存在: {cert_file}")
                return
            
            if not os.path.exists(key_file):
                messagebox.showerror("错误", f"私钥文件不存在: {key_file}")
                return
            
            cmd.extend(["--ssl", "--cert", cert_file, "--key", key_file])
        
        try:
            # 记录调试信息
            self.log_message(f"使用Python路径: {python_cmd}")
            self.log_message(f"服务器脚本路径: {server_script}")
            self.log_message(f"执行命令: {' '.join(cmd)}")
            
            # 检查文件是否存在
            if not os.path.exists(python_cmd):
                error_msg = f"Python可执行文件不存在: {python_cmd}"
                self.log_message(f"错误: {error_msg}")
                messagebox.showerror("启动错误", error_msg)
                return
                
            if not os.path.exists(server_script):
                error_msg = f"服务器脚本不存在: {server_script}"
                self.log_message(f"错误: {error_msg}")
                messagebox.showerror("启动错误", error_msg)
                return
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__))  # 设置工作目录
            )
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            protocol = "HTTPS" if self.ssl_var.get() else "HTTP"
            self.status_var.set(f"服务器运行中 ({protocol}://{host}:{port})")
            self.log_message(f"服务器已启动: {protocol}://{host}:{port}")
            
            # 启动日志读取线程
            threading.Thread(target=self.read_server_output, daemon=True).start()
            
        except FileNotFoundError as e:
            error_msg = f"找不到文件: {e}. 请检查Python安装和虚拟环境设置。"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("启动错误", error_msg)
        except Exception as e:
            error_msg = f"无法启动服务器: {e}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("启动错误", error_msg)
    
    def read_server_output(self):
        """读取服务器输出"""
        if self.server_process:
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    self.root.after(0, lambda l=line.strip(): self.log_message(l))
            
            # 服务器进程结束
            self.root.after(0, self.on_server_stopped)
    
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
        
        self.on_server_stopped()
    
    def on_server_stopped(self):
        """服务器停止回调"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("服务器未启动")
        self.log_message("服务器已停止")
    
    def start_client(self):
        """启动客户端"""
        try:
            # 使用跨平台的Python路径
            python_cmd = self.get_python_executable()
            client_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_client.py")
            
            # 记录调试信息
            self.log_message(f"启动客户端 - Python路径: {python_cmd}")
            self.log_message(f"客户端脚本路径: {client_script}")
            
            # 检查文件是否存在
            if not os.path.exists(python_cmd):
                error_msg = f"Python可执行文件不存在: {python_cmd}"
                self.log_message(f"错误: {error_msg}")
                messagebox.showerror("启动错误", error_msg)
                return
                
            if not os.path.exists(client_script):
                error_msg = f"客户端脚本不存在: {client_script}"
                self.log_message(f"错误: {error_msg}")
                messagebox.showerror("启动错误", error_msg)
                return
            
            subprocess.Popen([python_cmd, client_script], 
                           cwd=os.path.dirname(os.path.abspath(__file__)))
            self.log_message("客户端已启动")
        except FileNotFoundError as e:
            error_msg = f"找不到文件: {e}. 请检查Python安装。"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("启动错误", error_msg)
        except Exception as e:
            error_msg = f"无法启动客户端: {e}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("启动错误", error_msg)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.server_process:
            self.stop_server()
        self.root.destroy()
    
    def run(self):
        """运行启动器"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    launcher = ServerLauncher()
    launcher.run()

if __name__ == "__main__":
    main()