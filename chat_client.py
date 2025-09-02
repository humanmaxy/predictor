#!/usr/bin/env python3
"""
带图形界面的聊天客户端
支持服务器配置、协议选择、用户认证
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import websockets
import json
import threading
from datetime import datetime
import ssl
import uuid

class ChatClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("聊天客户端")
        self.root.geometry("800x600")
        
        # 连接相关变量
        self.websocket = None
        self.connected = False
        self.user_id = str(uuid.uuid4())[:8]  # 生成短UUID作为默认ID
        self.username = ""
        self.server_host = "localhost"
        self.server_port = 8765
        self.use_ssl = False
        
        # 私聊相关变量
        self.private_chat_windows = {}  # user_id -> 私聊窗口
        self.online_users = {}  # user_id -> username 映射
        
        # 创建界面
        self.create_widgets()
        
        # 启动异步事件循环
        self.loop = None
        self.setup_async_loop()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 服务器配置区域
        config_frame = ttk.LabelFrame(main_frame, text="服务器配置", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # 服务器地址
        ttk.Label(config_frame, text="服务器地址:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.host_var = tk.StringVar(value=self.server_host)
        host_entry = ttk.Entry(config_frame, textvariable=self.host_var, width=20)
        host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 端口
        ttk.Label(config_frame, text="端口:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar(value=str(self.server_port))
        port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=3, sticky=tk.W)
        
        # 协议选择
        ttk.Label(config_frame, text="协议:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.protocol_var = tk.StringVar(value="HTTP")
        protocol_combo = ttk.Combobox(config_frame, textvariable=self.protocol_var, 
                                    values=["HTTP", "HTTPS"], state="readonly", width=10)
        protocol_combo.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # 快速连接预设
        preset_frame = ttk.Frame(config_frame)
        preset_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(preset_frame, text="连接模式:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        local_btn = ttk.Button(preset_frame, text="本地", 
                              command=lambda: self.set_server_config("localhost", "8765"))
        local_btn.grid(row=0, column=1, padx=(0, 5))
        
        lan_btn = ttk.Button(preset_frame, text="局域网", 
                            command=lambda: self.set_server_config("172.27.66.166", "8765"))
        lan_btn.grid(row=0, column=2, padx=(0, 5))
        
        custom_btn = ttk.Button(preset_frame, text="自定义", 
                               command=self.show_custom_config)
        custom_btn.grid(row=0, column=3, padx=(0, 5))
        
        cos_btn = ttk.Button(preset_frame, text="COS云聊天", 
                            command=self.start_cos_chat)
        cos_btn.grid(row=0, column=4, padx=(0, 5))
        cos_btn.config(style="Accent.TButton")
        
        # 用户信息区域
        user_frame = ttk.LabelFrame(main_frame, text="用户信息", padding="5")
        user_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        user_frame.columnconfigure(1, weight=1)
        
        # 用户名
        ttk.Label(user_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(user_frame, textvariable=self.username_var, width=20)
        username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 用户ID
        ttk.Label(user_frame, text="用户ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.user_id_var = tk.StringVar(value=self.user_id)
        user_id_entry = ttk.Entry(user_frame, textvariable=self.user_id_var, width=15)
        user_id_entry.grid(row=0, column=3, sticky=tk.W)
        
        # 连接按钮
        self.connect_btn = ttk.Button(user_frame, text="连接", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        # 聊天区域
        chat_frame = ttk.LabelFrame(main_frame, text="聊天室", padding="5")
        chat_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 消息显示区域
        self.message_display = scrolledtext.ScrolledText(chat_frame, height=15, state=tk.DISABLED)
        self.message_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 在线用户列表
        users_frame = ttk.LabelFrame(chat_frame, text="在线用户", padding="5")
        users_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(10, 0))
        
        # 添加使用提示
        tip_label = ttk.Label(users_frame, text="双击用户名开始私聊", font=("Arial", 8))
        tip_label.pack(pady=(0, 5))
        
        self.users_listbox = tk.Listbox(users_frame, width=20, height=15)
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 绑定双击事件开启私聊
        self.users_listbox.bind('<Double-1>', self.start_private_chat)
        
        # 消息输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var)
        self.message_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_btn = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_btn.grid(row=0, column=1)
        
        # 初始状态设置
        self.set_chat_state(False)
        
        # 状态栏
        self.status_var = tk.StringVar(value="未连接")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def setup_async_loop(self):
        """设置异步事件循环"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.async_thread = threading.Thread(target=run_loop, daemon=True)
        self.async_thread.start()
    
    def set_chat_state(self, enabled: bool):
        """设置聊天界面状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.message_entry.config(state=state)
        self.send_btn.config(state=state)
    
    def set_server_config(self, host: str, port: str):
        """设置服务器配置"""
        self.host_var.set(host)
        self.port_var.set(port)
        self.add_system_message(f"服务器配置已设置为: {host}:{port}")
    
    def show_custom_config(self):
        """显示自定义配置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("自定义服务器配置")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 自定义地址输入
        ttk.Label(frame, text="服务器地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        custom_host_var = tk.StringVar(value=self.host_var.get())
        host_entry = ttk.Entry(frame, textvariable=custom_host_var, width=30)
        host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="端口:").grid(row=1, column=0, sticky=tk.W, pady=5)
        custom_port_var = tk.StringVar(value=self.port_var.get())
        port_entry = ttk.Entry(frame, textvariable=custom_port_var, width=30)
        port_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 常用地址列表
        ttk.Label(frame, text="常用地址:").grid(row=2, column=0, sticky=tk.W, pady=(20, 5))
        
        addresses_frame = ttk.Frame(frame)
        addresses_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        common_addresses = [
            ("本地服务器", "localhost", "8765"),
            ("局域网服务器", "172.27.66.166", "8765"),
            ("测试服务器", "192.168.1.100", "8765"),
        ]
        
        for i, (name, host, port) in enumerate(common_addresses):
            btn = ttk.Button(addresses_frame, text=name,
                           command=lambda h=host, p=port: [custom_host_var.set(h), custom_port_var.set(p)])
            btn.grid(row=i//2, column=i%2, padx=5, pady=2, sticky=tk.W)
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        def apply_config():
            self.set_server_config(custom_host_var.get(), custom_port_var.get())
            dialog.destroy()
        
        ttk.Button(button_frame, text="应用", command=apply_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
        
        frame.columnconfigure(1, weight=1)
        host_entry.focus()
    
    def toggle_connection(self):
        """切换连接状态"""
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
    
    def connect_to_server(self):
        """连接到服务器"""
        # 验证输入
        username = self.username_var.get().strip()
        user_id = self.user_id_var.get().strip()
        host = self.host_var.get().strip()
        
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return
        
        if not user_id:
            messagebox.showerror("错误", "请输入用户ID")
            return
        
        if not host:
            messagebox.showerror("错误", "请输入服务器地址")
            return
        
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return
        
        self.username = username
        self.user_id = user_id
        self.server_host = host
        self.server_port = port
        self.use_ssl = self.protocol_var.get() == "HTTPS"
        
        # 异步连接
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._connect(), self.loop)
    
    async def _connect(self):
        """异步连接到服务器"""
        try:
            protocol = "wss" if self.use_ssl else "ws"
            uri = f"{protocol}://{self.server_host}:{self.server_port}"
            
            # SSL配置
            ssl_context = None
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE  # 开发环境，不验证证书
            
            self.websocket = await websockets.connect(uri, ssl=ssl_context)
            
            # 发送加入消息
            join_message = {
                "type": "join",
                "user_id": self.user_id,
                "username": self.username
            }
            await self.websocket.send(json.dumps(join_message))
            
            # 更新UI状态
            self.root.after(0, self._on_connected)
            
            # 开始监听消息
            await self._listen_for_messages()
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._on_connection_error(msg))
    
    def _on_connected(self):
        """连接成功回调"""
        self.connected = True
        self.connect_btn.config(text="断开连接")
        self.set_chat_state(True)
        self.status_var.set(f"已连接到 {self.server_host}:{self.server_port}")
        self.add_system_message("已连接到服务器")
    
    def _on_connection_error(self, error_msg: str):
        """连接错误回调"""
        self.status_var.set("连接失败")
        messagebox.showerror("连接错误", f"无法连接到服务器: {error_msg}")
    
    async def _listen_for_messages(self):
        """监听服务器消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.root.after(0, lambda d=data: self._handle_message(d))
        except websockets.exceptions.ConnectionClosed:
            self.root.after(0, self._on_disconnected)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._on_connection_error(msg))
    
    def _handle_message(self, data: dict):
        """处理服务器消息"""
        message_type = data.get("type")
        
        if message_type == "join_success":
            self.add_system_message("成功加入聊天室")
        
        elif message_type == "error":
            messagebox.showerror("服务器错误", data.get("message", "未知错误"))
        
        elif message_type == "chat":
            username = data.get("username", "")
            user_id = data.get("user_id", "")
            message = data.get("message", "")
            timestamp = data.get("timestamp", "")
            
            # 格式化时间
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = datetime.now().strftime("%H:%M:%S")
            
            self.add_chat_message(f"[{time_str}] {username}: {message}")
        
        elif message_type == "user_joined":
            username = data.get("username", "")
            user_id = data.get("user_id", "")
            self.add_system_message(f"{username} 加入了聊天室")
            self.update_user_list(data.get("online_users", []))
            # 更新用户信息映射
            if user_id:
                self.online_users[user_id] = username
        
        elif message_type == "user_left":
            user_id = data.get("user_id", "")
            if user_id in self.online_users:
                username = self.online_users[user_id]
                self.add_system_message(f"{username} 离开了聊天室")
                del self.online_users[user_id]
            else:
                self.add_system_message(f"用户 {user_id} 离开了聊天室")
            self.update_user_list(data.get("online_users", []))
        
        elif message_type == "private_chat":
            sender_id = data.get("user_id", "")
            sender_name = data.get("username", "")
            target_id = data.get("target_user_id", "")
            message = data.get("message", "")
            timestamp = data.get("timestamp", "")
            
            # 格式化时间
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = datetime.now().strftime("%H:%M:%S")
            
            # 确定聊天对象
            if sender_id == self.user_id:
                # 自己发送的消息，聊天对象是target_id
                chat_partner_id = target_id
                chat_partner_name = self.online_users.get(target_id, target_id)
                message_text = f"[{time_str}] 我: {message}"
            else:
                # 收到的私聊消息，聊天对象是sender_id  
                chat_partner_id = sender_id
                chat_partner_name = sender_name
                message_text = f"[{time_str}] {sender_name}: {message}"
            
            # 在私聊窗口显示消息
            self.show_private_message(chat_partner_id, chat_partner_name, message_text)
        
        elif message_type == "user_info":
            # 用户信息响应，暂时不处理
            pass
    
    def add_system_message(self, message: str):
        """添加系统消息"""
        self.message_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_display.insert(tk.END, f"[{timestamp}] [系统] {message}\n")
        self.message_display.config(state=tk.DISABLED)
        self.message_display.see(tk.END)
    
    def add_chat_message(self, message: str):
        """添加聊天消息"""
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, f"{message}\n")
        self.message_display.config(state=tk.DISABLED)
        self.message_display.see(tk.END)
    
    def update_user_list(self, users: list):
        """更新在线用户列表"""
        self.users_listbox.delete(0, tk.END)
        for user_id in users:
            if user_id != self.user_id:  # 不显示自己
                username = self.online_users.get(user_id, user_id)
                display_text = f"{username} ({user_id})" if username != user_id else user_id
                self.users_listbox.insert(tk.END, display_text)
    
    def send_message(self, event=None):
        """发送消息"""
        message = self.message_var.get().strip()
        if not message or not self.connected:
            return
        
        # 异步发送消息
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)
        
        self.message_var.set("")  # 清空输入框
    
    async def _send_message(self, message: str):
        """异步发送消息"""
        try:
            if self.websocket:
                chat_message = {
                    "type": "chat",
                    "user_id": self.user_id,
                    "username": self.username,
                    "message": message
                }
                await self.websocket.send(json.dumps(chat_message))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("发送错误", f"发送消息失败: {msg}"))
    
    def disconnect_from_server(self):
        """断开服务器连接"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
    
    async def _disconnect(self):
        """异步断开连接"""
        try:
            if self.websocket:
                await self.websocket.close()
        except:
            pass
        finally:
            self.root.after(0, self._on_disconnected)
    
    def _on_disconnected(self):
        """断开连接回调"""
        self.connected = False
        self.websocket = None
        self.connect_btn.config(text="连接")
        self.set_chat_state(False)
        self.status_var.set("未连接")
        self.add_system_message("已断开连接")
        self.users_listbox.delete(0, tk.END)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.connected:
            self.disconnect_from_server()
        
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.root.destroy()
    
    def run(self):
        """运行客户端"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 添加快捷键
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        
        # 设置焦点
        self.username_var.trace('w', lambda *args: None)
        
        self.root.mainloop()
    
    def start_private_chat(self, event=None):
        """开始私聊（双击用户列表触发）"""
        selection = self.users_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.users_listbox.get(selection[0])
        # 解析用户ID（格式：username (user_id) 或 user_id）
        if '(' in selected_text and ')' in selected_text:
            user_id = selected_text.split('(')[-1].split(')')[0]
        else:
            user_id = selected_text
        
        username = self.online_users.get(user_id, user_id)
        self.open_private_chat_window(user_id, username)
    
    def open_private_chat_window(self, target_user_id: str, target_username: str):
        """打开私聊窗口"""
        if target_user_id in self.private_chat_windows:
            # 如果窗口已存在，则显示到前台
            self.private_chat_windows[target_user_id].lift()
            self.private_chat_windows[target_user_id].focus()
            return
        
        # 创建新的私聊窗口
        private_window = tk.Toplevel(self.root)
        private_window.title(f"私聊 - {target_username}")
        private_window.geometry("500x400")
        
        # 创建私聊界面
        frame = ttk.Frame(private_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # 消息显示区域
        message_display = scrolledtext.ScrolledText(frame, height=15, state=tk.DISABLED)
        message_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 消息输入区域
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        message_var = tk.StringVar()
        message_entry = ttk.Entry(input_frame, textvariable=message_var)
        message_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        def send_private_message(event=None):
            message = message_var.get().strip()
            if message and self.connected:
                self.send_private_message_to_server(target_user_id, message)
                message_var.set("")
        
        message_entry.bind('<Return>', send_private_message)
        
        send_btn = ttk.Button(input_frame, text="发送", command=send_private_message)
        send_btn.grid(row=0, column=1)
        
        # 存储窗口引用和消息显示组件
        self.private_chat_windows[target_user_id] = private_window
        private_window.message_display = message_display
        private_window.target_user_id = target_user_id
        private_window.target_username = target_username
        
        # 窗口关闭事件
        def on_close():
            if target_user_id in self.private_chat_windows:
                del self.private_chat_windows[target_user_id]
            private_window.destroy()
        
        private_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # 添加欢迎消息
        self.add_private_message(target_user_id, f"开始与 {target_username} 的私聊")
        
        message_entry.focus()
    
    def send_private_message_to_server(self, target_user_id: str, message: str):
        """发送私聊消息到服务器"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_private_message(target_user_id, message), 
                self.loop
            )
    
    async def _send_private_message(self, target_user_id: str, message: str):
        """异步发送私聊消息"""
        try:
            if self.websocket:
                private_message = {
                    "type": "private_chat",
                    "user_id": self.user_id,
                    "username": self.username,
                    "target_user_id": target_user_id,
                    "message": message
                }
                await self.websocket.send(json.dumps(private_message))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("发送错误", f"发送私聊消息失败: {msg}"))
    
    def show_private_message(self, chat_partner_id: str, chat_partner_name: str, message_text: str):
        """在私聊窗口显示消息"""
        # 如果私聊窗口不存在，创建它
        if chat_partner_id not in self.private_chat_windows:
            self.open_private_chat_window(chat_partner_id, chat_partner_name)
        
        # 在私聊窗口显示消息
        window = self.private_chat_windows[chat_partner_id]
        if hasattr(window, 'message_display'):
            window.message_display.config(state=tk.NORMAL)
            window.message_display.insert(tk.END, f"{message_text}\n")
            window.message_display.config(state=tk.DISABLED)
            window.message_display.see(tk.END)
            
            # 如果窗口不在前台，闪烁提醒
            if not window.focus_displayof():
                window.bell()  # 系统提示音
                original_title = window.title()
                window.title(f"[新消息] {original_title}")
                # 3秒后恢复标题
                window.after(3000, lambda: window.title(original_title))
    
    def add_private_message(self, target_user_id: str, message: str):
        """添加私聊系统消息"""
        if target_user_id in self.private_chat_windows:
            window = self.private_chat_windows[target_user_id]
            if hasattr(window, 'message_display'):
                window.message_display.config(state=tk.NORMAL)
                timestamp = datetime.now().strftime("%H:%M:%S")
                window.message_display.insert(tk.END, f"[{timestamp}] [系统] {message}\n")
                window.message_display.config(state=tk.DISABLED)
                window.message_display.see(tk.END)
    
    def start_cos_chat(self):
        """启动COS云聊天"""
        try:
            import subprocess
            import sys
            
            # 启动COS聊天客户端
            subprocess.Popen([sys.executable, "cos_chat_client.py"])
            self.add_system_message("正在启动COS云聊天客户端...")
            
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动COS聊天客户端: {str(e)}")

def main():
    """主函数"""
    try:
        client = ChatClient()
        client.run()
    except KeyboardInterrupt:
        print("客户端已停止")

if __name__ == "__main__":
    main()