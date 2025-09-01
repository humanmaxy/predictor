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
        
        self.users_listbox = tk.Listbox(users_frame, width=20, height=15)
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        
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
            self.root.after(0, lambda: self._on_connection_error(str(e)))
    
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
            self.root.after(0, lambda: self._on_connection_error(str(e)))
    
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
            self.add_system_message(f"{username} 加入了聊天室")
            self.update_user_list(data.get("online_users", []))
        
        elif message_type == "user_left":
            user_id = data.get("user_id", "")
            self.add_system_message(f"用户 {user_id} 离开了聊天室")
            self.update_user_list(data.get("online_users", []))
    
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
        for user in users:
            self.users_listbox.insert(tk.END, user)
    
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
            self.root.after(0, lambda: messagebox.showerror("发送错误", f"发送消息失败: {e}"))
    
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

def main():
    """主函数"""
    try:
        client = ChatClient()
        client.run()
    except KeyboardInterrupt:
        print("客户端已停止")

if __name__ == "__main__":
    main()