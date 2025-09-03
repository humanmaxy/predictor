#!/usr/bin/env python3
"""
基于网络共享目录的聊天客户端
聊天记录存储在 \\\\catl-tfile\\Temp1day每天凌晨两点清理数据01\\imdmmm
"""

import sys
import os
import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import shutil
import glob

# 导入文件传输工具
from file_transfer_utils import FileTransferManager
from improved_file_manager import FileManagerWindow, DownloadButton

class NetworkShareChatManager:
    """网络共享目录聊天管理器"""
    def __init__(self, share_path: str):
        self.share_path = Path(share_path)
        self.public_dir = self.share_path / "public"
        self.private_dir = self.share_path / "private"
        self.users_dir = self.share_path / "users"
        self.config_file = self.share_path / ".chat_config"
        
        # 消息缓存
        self.message_cache = set()  # 已处理的消息文件
        self.last_scan_time = datetime.now()
        
        # 文件传输管理器
        self.file_manager = FileTransferManager(share_path)
        
        # 初始化目录结构
        self._init_directories()
    
    def _init_directories(self):
        """初始化目录结构"""
        try:
            # 创建必要的目录
            self.share_path.mkdir(parents=True, exist_ok=True)
            self.public_dir.mkdir(exist_ok=True)
            self.private_dir.mkdir(exist_ok=True)
            self.users_dir.mkdir(exist_ok=True)
            
            # 创建配置文件
            if not self.config_file.exists():
                config = {
                    "chat_room_name": "局域网共享聊天室",
                    "created_time": datetime.now().isoformat(),
                    "sync_interval": 3,
                    "cleanup_time": "02:00"
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"初始化目录失败: {e}")
            return False
    
    def check_access(self):
        """检查目录访问权限"""
        try:
            # 测试读写权限
            test_file = self.share_path / f"test_{uuid.uuid4().hex[:8]}.tmp"
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            return True
        except Exception as e:
            print(f"目录访问测试失败: {e}")
            return False
    
    def send_public_message(self, user_id: str, username: str, message: str, file_info: dict = None):
        """发送群聊消息"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"msg_{timestamp}_{user_id}.json"
            
            message_data = {
                "type": "public",
                "user_id": user_id,
                "username": username,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            # 如果有文件信息，添加到消息中
            if file_info:
                message_data["file_info"] = file_info
                message_data["message_type"] = "file"
            else:
                message_data["message_type"] = "text"
            
            # 直接保存消息数据为JSON
            file_path = self.public_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"发送群聊消息失败: {e}")
            return False
    
    def send_private_message(self, sender_id: str, sender_name: str, target_id: str, message: str, file_info: dict = None):
        """发送私聊消息"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"msg_{timestamp}_{sender_id}.json"
            
            # 私聊目录：按用户ID字母序排列
            chat_pair = "_".join(sorted([sender_id, target_id]))
            private_chat_dir = self.private_dir / chat_pair
            private_chat_dir.mkdir(exist_ok=True)
            
            message_data = {
                "type": "private",
                "sender_id": sender_id,
                "sender_name": sender_name,
                "target_id": target_id,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            # 如果有文件信息，添加到消息中
            if file_info:
                message_data["file_info"] = file_info
                message_data["message_type"] = "file"
            else:
                message_data["message_type"] = "text"
            
            # 直接保存消息数据为JSON
            file_path = private_chat_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"发送私聊消息失败: {e}")
            return False
    
    def update_user_heartbeat(self, user_id: str, username: str):
        """更新用户心跳"""
        try:
            heartbeat_file = self.users_dir / f"{user_id}_heartbeat.json"
            heartbeat_data = {
                "user_id": user_id,
                "username": username,
                "last_active": datetime.now().isoformat(),
                "status": "online"
            }
            
            with open(heartbeat_file, 'w', encoding='utf-8') as f:
                json.dump(heartbeat_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"更新心跳失败: {e}")
            return False
    
    def get_new_messages(self, user_id: str):
        """获取新消息"""
        new_messages = []
        
        try:
            # 获取群聊消息
            public_messages = self._scan_directory(self.public_dir, "public")
            new_messages.extend(public_messages)
            
            # 获取私聊消息（扫描所有包含当前用户的私聊目录）
            for private_dir in self.private_dir.iterdir():
                if private_dir.is_dir() and user_id in private_dir.name:
                    private_messages = self._scan_directory(private_dir, "private")
                    new_messages.extend(private_messages)
            
            # 按时间戳排序
            new_messages.sort(key=lambda x: x.get('timestamp', ''))
            
        except Exception as e:
            print(f"获取新消息失败: {e}")
        
        return new_messages
    
    def _scan_directory(self, directory: Path, msg_type: str):
        """扫描目录获取消息"""
        messages = []
        
        try:
            if not directory.exists():
                return messages
            
            # 扫描JSON消息文件
            for file_path in directory.glob("msg_*.json"):
                filename = file_path.name
                
                # 跳过已处理的消息
                if filename in self.message_cache:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                    
                    # 直接解析JSON消息
                    message_data = json.loads(file_content)
                    
                    if message_data:  # 解密成功
                        message_data['_filename'] = filename
                        message_data['_file_path'] = str(file_path)
                        
                        messages.append(message_data)
                        self.message_cache.add(filename)
                    
                except Exception as e:
                    print(f"读取消息文件失败 {file_path}: {e}")
                    
        except Exception as e:
            print(f"扫描目录失败 {directory}: {e}")
        
        return messages
    
    def get_online_users(self):
        """获取在线用户（基于心跳文件）"""
        online_users = []
        current_time = datetime.now()
        
        try:
            for heartbeat_file in self.users_dir.glob("*_heartbeat.json"):
                try:
                    with open(heartbeat_file, 'r', encoding='utf-8') as f:
                        heartbeat_data = json.load(f)
                    
                    last_active = datetime.fromisoformat(heartbeat_data.get('last_active', ''))
                    # 5分钟内活跃视为在线
                    if (current_time - last_active).total_seconds() < 300:
                        online_users.append((
                            heartbeat_data.get('user_id', ''),
                            heartbeat_data.get('username', '')
                        ))
                        
                except Exception as e:
                    print(f"读取心跳文件失败 {heartbeat_file}: {e}")
                    
        except Exception as e:
            print(f"获取在线用户失败: {e}")
        
        return online_users
    
    def cleanup_old_messages(self, days_to_keep=1):
        """清理旧消息（模拟每日凌晨2点清理）"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            # 清理群聊消息
            for msg_file in self.public_dir.glob("msg_*.json"):
                if msg_file.stat().st_mtime < cutoff_time.timestamp():
                    msg_file.unlink()
                    deleted_count += 1
            
            # 清理私聊消息
            for private_dir in self.private_dir.iterdir():
                if private_dir.is_dir():
                    for msg_file in private_dir.glob("msg_*.json"):
                        if msg_file.stat().st_mtime < cutoff_time.timestamp():
                            msg_file.unlink()
                            deleted_count += 1
                    
                    # 删除空的私聊目录
                    if not any(private_dir.iterdir()):
                        private_dir.rmdir()
            
            # 清理过期心跳文件
            for heartbeat_file in self.users_dir.glob("*_heartbeat.json"):
                if heartbeat_file.stat().st_mtime < cutoff_time.timestamp():
                    heartbeat_file.unlink()
            
            print(f"清理完成，删除了 {deleted_count} 个消息文件")
            return deleted_count
            
        except Exception as e:
            print(f"清理消息失败: {e}")
            return 0
    
    def upload_file(self, file_path: str, user_id: str, username: str) -> dict:
        """上传文件"""
        return self.file_manager.upload_file(file_path, user_id, username)
    
    def download_file(self, file_info: dict, local_dir: str) -> bool:
        """下载文件"""
        return self.file_manager.download_file(file_info, local_dir)
    
    def get_file_storage_stats(self) -> dict:
        """获取文件存储统计"""
        return self.file_manager.get_storage_stats()

class NetworkShareChatClient:
    """基于网络共享目录的聊天客户端"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("局域网共享目录聊天")
        self.root.geometry("900x700")
        
        # 网络共享配置
        self.share_path = r"\\catl-tfile\Temp1day每天凌晨两点清理数据01\imdmmm"
        self.chat_manager = None
        self.connected = False
        
        # 用户信息
        self.user_id = str(uuid.uuid4())[:8]
        self.username = ""
        
        # 消息同步
        self.sync_thread = None
        self.sync_running = False
        self.sync_interval = 3  # 3秒同步间隔
        self.heartbeat_thread = None
        
        # 私聊窗口
        self.private_chat_windows = {}
        self.online_users = {}
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 网络共享配置区域
        config_frame = ttk.LabelFrame(main_frame, text="网络共享目录配置", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # 共享路径
        ttk.Label(config_frame, text="共享路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.share_path_var = tk.StringVar(value=self.share_path)
        share_path_entry = ttk.Entry(config_frame, textvariable=self.share_path_var, width=60)
        share_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 浏览按钮
        browse_btn = ttk.Button(config_frame, text="浏览...", command=self.browse_share_path)
        browse_btn.grid(row=0, column=2)
        
        # 测试连接按钮
        test_btn = ttk.Button(config_frame, text="测试访问", command=self.test_share_access)
        test_btn.grid(row=1, column=0, pady=(10, 0))
        
        # 访问状态
        self.access_status_var = tk.StringVar(value="未测试")
        status_label = ttk.Label(config_frame, textvariable=self.access_status_var)
        status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
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
        self.connect_btn = ttk.Button(user_frame, text="加入聊天室", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        # 聊天区域
        chat_frame = ttk.LabelFrame(main_frame, text="局域网共享聊天室", padding="5")
        chat_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 消息显示区域
        self.message_display = scrolledtext.ScrolledText(chat_frame, height=15, state=tk.DISABLED)
        self.message_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 在线用户列表
        users_frame = ttk.LabelFrame(chat_frame, text="活跃用户", padding="5")
        users_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(10, 0))
        
        # 添加使用提示
        tip_label = ttk.Label(users_frame, text="双击用户名开始私聊", font=("Arial", 8))
        tip_label.pack(pady=(0, 5))
        
        self.users_listbox = tk.Listbox(users_frame, width=20, height=15)
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
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
        
        # 文件传输按钮
        file_btn_frame = ttk.Frame(input_frame)
        file_btn_frame.grid(row=0, column=2, padx=(5, 0))
        
        self.file_btn = ttk.Button(file_btn_frame, text="📎 文件", command=self.send_file)
        self.file_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.image_btn = ttk.Button(file_btn_frame, text="🖼️ 图片", command=self.send_image)
        self.image_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.file_manager_btn = ttk.Button(file_btn_frame, text="📁 文件管理", command=self.open_file_manager)
        self.file_manager_btn.pack(side=tk.LEFT)
        
        # 初始状态设置
        self.set_chat_state(False)
        
        # 状态栏
        self.status_var = tk.StringVar(value="未连接")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 同步信息
        sync_frame = ttk.Frame(main_frame)
        sync_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.sync_status_var = tk.StringVar(value="同步状态: 未开始")
        sync_label = ttk.Label(sync_frame, textvariable=self.sync_status_var, font=("Arial", 8))
        sync_label.pack(side=tk.LEFT)
        
        self.last_sync_var = tk.StringVar(value="")
        last_sync_label = ttk.Label(sync_frame, textvariable=self.last_sync_var, font=("Arial", 8))
        last_sync_label.pack(side=tk.RIGHT)
        
        # 清理按钮
        cleanup_btn = ttk.Button(sync_frame, text="清理旧消息", command=self.cleanup_messages)
        cleanup_btn.pack(side=tk.RIGHT, padx=(0, 20))
    
    def browse_share_path(self):
        """浏览共享路径"""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择网络共享目录")
        if path:
            self.share_path_var.set(path)
    
    def test_share_access(self):
        """测试共享目录访问"""
        share_path = self.share_path_var.get().strip()
        if not share_path:
            self.access_status_var.set("❌ 路径为空")
            return
        
        try:
            test_manager = NetworkShareChatManager(share_path)
            if test_manager.check_access():
                self.access_status_var.set("✅ 访问正常")
                self.add_system_message("网络共享目录访问测试成功")
            else:
                self.access_status_var.set("❌ 访问失败")
                messagebox.showerror("访问错误", "无法访问网络共享目录，请检查路径和权限")
        except Exception as e:
            self.access_status_var.set("❌ 访问异常")
            messagebox.showerror("访问错误", f"访问测试失败: {str(e)}")
    
    def set_chat_state(self, enabled: bool):
        """设置聊天界面状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.message_entry.config(state=state)
        self.send_btn.config(state=state)
        self.file_btn.config(state=state)
        self.image_btn.config(state=state)
        self.file_manager_btn.config(state=state)
    
    def toggle_connection(self):
        """切换连接状态"""
        if not self.connected:
            self.connect_to_share()
        else:
            self.disconnect_from_share()
    
    def connect_to_share(self):
        """连接到共享目录"""
        # 验证输入
        username = self.username_var.get().strip()
        user_id = self.user_id_var.get().strip()
        share_path = self.share_path_var.get().strip()
        
        if not all([username, user_id, share_path]):
            messagebox.showerror("错误", "请填写所有必要信息")
            return
        
        try:
            # 创建聊天管理器
            self.chat_manager = NetworkShareChatManager(share_path)
            
            # 测试访问
            if not self.chat_manager.check_access():
                messagebox.showerror("连接错误", "无法访问网络共享目录")
                return
            
            # 更新用户信息
            self.username = username
            self.user_id = user_id
            self.share_path = share_path
            
            # 连接成功
            self.connected = True
            self.connect_btn.config(text="离开聊天室")
            self.set_chat_state(True)
            self.status_var.set(f"已连接到共享聊天室: {os.path.basename(share_path)}")
            self.add_system_message("已加入局域网共享聊天室")
            self.add_system_message("消息存储在网络共享目录，每天凌晨2点自动清理")
            
            # 开始消息同步和心跳
            self.start_message_sync()
            self.start_heartbeat()
            
        except Exception as e:
            messagebox.showerror("连接错误", f"连接失败: {str(e)}")
    
    def disconnect_from_share(self):
        """断开共享目录连接"""
        self.connected = False
        self.stop_message_sync()
        self.stop_heartbeat()
        self.connect_btn.config(text="加入聊天室")
        self.set_chat_state(False)
        self.status_var.set("未连接")
        self.sync_status_var.set("同步状态: 已停止")
        self.add_system_message("已离开共享聊天室")
        self.users_listbox.delete(0, tk.END)
    
    def start_message_sync(self):
        """开始消息同步"""
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._sync_messages, daemon=True)
        self.sync_thread.start()
        self.sync_status_var.set("同步状态: 运行中")
    
    def stop_message_sync(self):
        """停止消息同步"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=1)
    
    def start_heartbeat(self):
        """开始心跳"""
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def stop_heartbeat(self):
        """停止心跳"""
        # 心跳线程会自动停止（daemon=True）
        pass
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.connected:
            try:
                self.chat_manager.update_user_heartbeat(self.user_id, self.username)
            except Exception as e:
                print(f"心跳更新失败: {e}")
            
            time.sleep(30)  # 每30秒更新一次心跳
    
    def _sync_messages(self):
        """消息同步循环"""
        while self.sync_running and self.connected:
            try:
                # 获取新消息
                new_messages = self.chat_manager.get_new_messages(self.user_id)
                
                # 在主线程中处理消息
                for message in new_messages:
                    self.root.after(0, lambda msg=message: self._handle_message(msg))
                
                # 更新在线用户列表
                online_users = self.chat_manager.get_online_users()
                self.root.after(0, lambda users=online_users: self._update_online_users(users))
                
                # 更新同步状态
                sync_time = datetime.now().strftime("%H:%M:%S")
                self.root.after(0, lambda t=sync_time: self.last_sync_var.set(f"最后同步: {t}"))
                
            except Exception as e:
                print(f"消息同步错误: {e}")
                self.root.after(0, lambda err=str(e): self.add_system_message(f"同步错误: {err}"))
            
            # 等待下次同步
            time.sleep(self.sync_interval)
    
    def _handle_message(self, message_data: dict):
        """处理消息"""
        msg_type = message_data.get('type')
        timestamp = message_data.get('timestamp', '')
        
        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = datetime.now().strftime("%H:%M:%S")
        
        if msg_type == 'public':
            # 群聊消息
            username = message_data.get('username', '')
            user_id = message_data.get('user_id', '')
            message = message_data.get('message', '')
            message_type = message_data.get('message_type', 'text')
            
            if message_type == 'file':
                file_info = message_data.get('file_info', {})
                if user_id == self.user_id:
                    self.add_file_message(f"[{time_str}] 我", file_info, is_public=True)
                else:
                    self.add_file_message(f"[{time_str}] {username}", file_info, is_public=True)
            else:
                if user_id == self.user_id:
                    self.add_chat_message(f"[{time_str}] 我: {message}")
                else:
                    self.add_chat_message(f"[{time_str}] {username}: {message}")
        
        elif msg_type == 'private':
            # 私聊消息
            sender_id = message_data.get('sender_id', '')
            sender_name = message_data.get('sender_name', '')
            target_id = message_data.get('target_id', '')
            message = message_data.get('message', '')
            
            # 确定聊天对象
            if sender_id == self.user_id:
                # 自己发送的私聊消息
                chat_partner_id = target_id
                chat_partner_name = self.online_users.get(target_id, target_id)
                message_text = f"[{time_str}] 我: {message}"
            elif target_id == self.user_id:
                # 收到的私聊消息
                chat_partner_id = sender_id
                chat_partner_name = sender_name
                message_text = f"[{time_str}] {sender_name}: {message}"
            else:
                # 不相关的私聊消息，忽略
                return
            
            # 在私聊窗口显示消息
            self.show_private_message(chat_partner_id, chat_partner_name, message_text, message_data)
    
    def _update_online_users(self, users: list):
        """更新在线用户列表"""
        self.users_listbox.delete(0, tk.END)
        self.online_users.clear()
        
        for user_id, username in users:
            if user_id != self.user_id:  # 不显示自己
                self.online_users[user_id] = username
                display_text = f"{username} ({user_id})" if username != user_id else user_id
                self.users_listbox.insert(tk.END, display_text)
    
    def send_message(self, event=None):
        """发送群聊消息"""
        message = self.message_var.get().strip()
        if not message or not self.connected:
            return
        
        # 发送到共享目录
        success = self.chat_manager.send_public_message(self.user_id, self.username, message)
        if success:
            self.message_var.set("")  # 清空输入框
        else:
            messagebox.showerror("发送失败", "发送消息到共享目录失败")
    
    def start_private_chat(self, event=None):
        """开始私聊"""
        selection = self.users_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.users_listbox.get(selection[0])
        # 解析用户ID
        if '(' in selected_text and ')' in selected_text:
            user_id = selected_text.split('(')[-1].split(')')[0]
        else:
            user_id = selected_text
        
        username = self.online_users.get(user_id, user_id)
        self.open_private_chat_window(user_id, username)
    
    def open_private_chat_window(self, target_user_id: str, target_username: str):
        """打开私聊窗口"""
        if target_user_id in self.private_chat_windows:
            self.private_chat_windows[target_user_id].lift()
            self.private_chat_windows[target_user_id].focus()
            return
        
        # 创建新的私聊窗口
        private_window = tk.Toplevel(self.root)
        private_window.title(f"共享私聊 - {target_username}")
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
                success = self.chat_manager.send_private_message(
                    self.user_id, self.username, target_user_id, message
                )
                if success:
                    message_var.set("")
                else:
                    messagebox.showerror("发送失败", "发送私聊消息失败")
        
        message_entry.bind('<Return>', send_private_message)
        
        send_btn = ttk.Button(input_frame, text="发送", command=send_private_message)
        send_btn.grid(row=0, column=1)
        
        # 存储窗口引用
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
        self.add_private_message(target_user_id, f"开始与 {target_username} 的共享私聊")
        
        message_entry.focus()
    
    def show_private_message(self, chat_partner_id: str, chat_partner_name: str, message_text: str):
        """在私聊窗口显示消息"""
        if chat_partner_id not in self.private_chat_windows:
            self.open_private_chat_window(chat_partner_id, chat_partner_name)
        
        window = self.private_chat_windows[chat_partner_id]
        if hasattr(window, 'message_display'):
            window.message_display.config(state=tk.NORMAL)
            window.message_display.insert(tk.END, f"{message_text}\n")
            window.message_display.config(state=tk.DISABLED)
            window.message_display.see(tk.END)
            
            # 如果窗口不在前台，闪烁提醒
            if not window.focus_displayof():
                window.bell()
                original_title = window.title()
                window.title(f"[新消息] {original_title}")
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
    
    def cleanup_messages(self):
        """清理旧消息"""
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到聊天室")
            return
        
        result = messagebox.askyesno("确认清理", "确定要清理1天前的旧消息吗？")
        if result:
            try:
                deleted_count = self.chat_manager.cleanup_old_messages(days_to_keep=1)
                self.add_system_message(f"清理完成，删除了 {deleted_count} 条旧消息")
            except Exception as e:
                messagebox.showerror("清理错误", f"清理失败: {str(e)}")
    
    def send_file(self):
        """发送文件"""
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到聊天室")
            return
        
        file_path = filedialog.askopenfilename(
            title="选择要发送的文件",
            filetypes=[
                ("所有支持的文件", "*.txt;*.doc;*.docx;*.pdf;*.xls;*.xlsx;*.ppt;*.pptx;*.zip;*.rar;*.7z;*.tar;*.gz;*.mp3;*.mp4;*.avi;*.mov"),
                ("文档文件", "*.txt;*.doc;*.docx;*.pdf"),
                ("表格文件", "*.xls;*.xlsx"),
                ("演示文件", "*.ppt;*.pptx"),
                ("压缩文件", "*.zip;*.rar;*.7z;*.tar;*.gz"),
                ("媒体文件", "*.mp3;*.mp4;*.avi;*.mov"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self._upload_and_send_file(file_path, "file")
    
    def send_image(self):
        """发送图片"""
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到聊天室")
            return
        
        image_path = filedialog.askopenfilename(
            title="选择要发送的图片",
            filetypes=[
                ("图片文件", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp"),
                ("JPEG图片", "*.jpg;*.jpeg"),
                ("PNG图片", "*.png"),
                ("GIF图片", "*.gif"),
                ("BMP图片", "*.bmp"),
                ("WebP图片", "*.webp"),
                ("所有文件", "*.*")
            ]
        )
        
        if image_path:
            self._upload_and_send_file(image_path, "image")
    
    def _upload_and_send_file(self, file_path: str, file_type: str):
        """上传并发送文件"""
        try:
            # 显示上传进度
            self.add_system_message(f"正在上传{file_type}...")
            self.root.update()
            
            # 上传文件
            file_info = self.chat_manager.upload_file(file_path, self.user_id, self.username)
            
            if file_info:
                # 发送包含文件信息的消息
                file_name = file_info['original_name']
                message = f"发送了{file_type}: {file_name}"
                
                success = self.chat_manager.send_public_message(
                    self.user_id, self.username, message, file_info
                )
                
                if success:
                    self.add_system_message(f"{file_type}发送成功: {file_name}")
                else:
                    self.add_system_message(f"{file_type}发送失败")
            else:
                self.add_system_message(f"{file_type}上传失败")
                
        except Exception as e:
            messagebox.showerror("发送错误", f"发送{file_type}失败: {str(e)}")
    
    def add_file_message(self, sender: str, file_info: dict, is_public: bool = True):
        """添加文件消息"""
        try:
            file_name = file_info.get('original_name', '未知文件')
            file_size = file_info.get('file_size', 0)
            file_type = file_info.get('file_type', 'file')
            
            # 格式化文件大小
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            # 创建文件消息
            if file_type == 'image':
                icon = "🖼️"
            else:
                icon = "📎"
            
            message_text = f"{sender} {icon} {file_name} ({size_str})"
            
            if is_public:
                self.add_chat_message(message_text)
                # 添加下载提示和文件管理器链接
                self.add_chat_message(f"    📥 使用文件管理器下载，或点击上方 '📁 文件管理' 按钮")
            
        except Exception as e:
            print(f"添加文件消息失败: {e}")
    
    def show_private_message(self, chat_partner_id: str, chat_partner_name: str, message_text: str, message_data: dict = None):
        """在私聊窗口显示消息"""
        # 如果私聊窗口不存在，创建它
        if chat_partner_id not in self.private_chat_windows:
            self.open_private_chat_window(chat_partner_id, chat_partner_name)
        
        # 在私聊窗口显示消息
        window = self.private_chat_windows[chat_partner_id]
        if hasattr(window, 'message_display'):
            window.message_display.config(state=tk.NORMAL)
            
            # 检查是否是文件消息
            if message_data and message_data.get('message_type') == 'file':
                file_info = message_data.get('file_info', {})
                file_name = file_info.get('original_name', '未知文件')
                file_size = file_info.get('file_size', 0)
                file_type = file_info.get('file_type', 'file')
                
                # 格式化文件大小
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                icon = "🖼️" if file_type == 'image' else "📎"
                window.message_display.insert(tk.END, f"{message_text.split(':')[0]}: {icon} {file_name} ({size_str})\n")
                window.message_display.insert(tk.END, f"    💡 双击可下载文件\n")
            else:
                window.message_display.insert(tk.END, f"{message_text}\n")
            
            window.message_display.config(state=tk.DISABLED)
            window.message_display.see(tk.END)
            
            # 如果窗口不在前台，闪烁提醒
            if not window.focus_displayof():
                window.bell()
                original_title = window.title()
                window.title(f"[新消息] {original_title}")
                window.after(3000, lambda: window.title(original_title))
    
    def open_file_manager(self):
        """打开文件管理器"""
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到聊天室")
            return
        
        try:
            # 创建文件管理窗口
            FileManagerWindow(self.root, self.chat_manager, self.user_id, self.username)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件管理器: {str(e)}")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.connected:
            self.disconnect_from_share()
        self.root.destroy()
    
    def run(self):
        """运行客户端"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.mainloop()

def main():
    """主函数"""
    try:
        client = NetworkShareChatClient()
        client.run()
    except KeyboardInterrupt:
        print("网络共享聊天客户端已停止")

if __name__ == "__main__":
    main()