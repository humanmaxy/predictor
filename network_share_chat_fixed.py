#!/usr/bin/env python3
"""
修复版本的网络共享目录聊天客户端
集成了所有功能，修复了下载问题
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
import base64
import hashlib
import mimetypes

class ChatEncryption:
    """聊天加密工具（内置版本）"""
    
    SECRET_KEY = "ChatRoom2024SecretKey!@#NetworkShare"
    
    @classmethod
    def _get_key_hash(cls):
        """获取密钥的哈希值用于验证"""
        return hashlib.md5(cls.SECRET_KEY.encode()).hexdigest()[:16]
    
    @classmethod
    def encrypt_message(cls, message_data):
        """加密消息数据"""
        try:
            message_data['_encrypted'] = True
            message_data['_key_hash'] = cls._get_key_hash()
            
            json_str = json.dumps(message_data, ensure_ascii=False)
            encoded_bytes = base64.b64encode(json_str.encode('utf-8'))
            double_encoded = base64.b64encode(encoded_bytes)
            
            return double_encoded.decode('utf-8')
        except Exception as e:
            print(f"加密失败: {e}")
            return ""
    
    @classmethod
    def decrypt_message(cls, encrypted_data):
        """解密消息数据"""
        try:
            first_decode = base64.b64decode(encrypted_data.encode('utf-8'))
            second_decode = base64.b64decode(first_decode)
            json_str = second_decode.decode('utf-8')
            message_data = json.loads(json_str)
            
            if message_data.get('_key_hash') != cls._get_key_hash():
                raise ValueError("密钥验证失败")
            
            message_data.pop('_encrypted', None)
            message_data.pop('_key_hash', None)
            
            return message_data
        except Exception as e:
            print(f"解密失败: {e}")
            return {}
    
    @classmethod
    def is_encrypted_data(cls, data):
        """检查数据是否已加密"""
        try:
            decrypted = cls.decrypt_message(data)
            return bool(decrypted)
        except:
            return False

class SimpleFileManager:
    """简化的文件管理器"""
    
    def __init__(self, share_path):
        self.share_path = Path(share_path)
        self.files_dir = self.share_path / "files"
        self.images_dir = self.share_path / "images"
        self.thumbnails_dir = self.share_path / "thumbnails"
        
        # 创建目录
        for directory in [self.files_dir, self.images_dir, self.thumbnails_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 支持的文件类型
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.supported_file_types = {
            '.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov'
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def upload_file(self, file_path, user_id, username):
        """上传文件"""
        try:
            local_path = Path(file_path)
            
            if not local_path.exists():
                return None
            
            file_size = local_path.stat().st_size
            if file_size > self.max_file_size:
                print(f"文件过大: {file_size / 1024 / 1024:.1f}MB")
                return None
            
            # 检查文件类型
            file_ext = local_path.suffix.lower()
            if file_ext in self.supported_image_types:
                file_type = "image"
                target_dir = self.images_dir
            elif file_ext in self.supported_file_types:
                file_type = "file"
                target_dir = self.files_dir
            else:
                print(f"不支持的文件类型: {file_ext}")
                return None
            
            # 计算文件哈希
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()
            
            # 生成新文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{user_id}_{file_hash[:8]}{file_ext}"
            target_path = target_dir / new_filename
            
            # 复制文件
            shutil.copy2(file_path, target_path)
            
            # 如果是图片，生成缩略图
            if file_type == "image":
                thumbnail_path = self.thumbnails_dir / f"thumb_{new_filename}"
                shutil.copy2(target_path, thumbnail_path)
            
            return {
                "filename": new_filename,
                "original_name": local_path.name,
                "file_type": file_type,
                "file_size": file_size,
                "file_hash": file_hash,
                "mime_type": mimetypes.guess_type(file_path)[0] or "application/octet-stream",
                "upload_time": datetime.now().isoformat(),
                "uploader_id": user_id,
                "uploader_name": username,
                "relative_path": str(target_path.relative_to(self.share_path))
            }
            
        except Exception as e:
            print(f"文件上传失败: {e}")
            return None

class NetworkShareChatManager:
    """网络共享目录聊天管理器（简化版）"""
    
    def __init__(self, share_path):
        self.share_path = Path(share_path)
        self.public_dir = self.share_path / "public"
        self.private_dir = self.share_path / "private"
        self.users_dir = self.share_path / "users"
        
        # 文件管理器
        self.file_manager = SimpleFileManager(share_path)
        
        # 消息缓存
        self.message_cache = set()
        
        # 初始化目录
        self._init_directories()
    
    def _init_directories(self):
        """初始化目录结构"""
        try:
            for directory in [self.public_dir, self.private_dir, self.users_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"初始化目录失败: {e}")
            return False
    
    def check_access(self):
        """检查目录访问权限"""
        try:
            test_file = self.share_path / f"test_{uuid.uuid4().hex[:8]}.tmp"
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            return True
        except Exception as e:
            print(f"目录访问测试失败: {e}")
            return False
    
    def send_public_message(self, user_id, username, message, file_info=None):
        """发送群聊消息"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"msg_{timestamp}_{user_id}.json"
            
            message_data = {
                "type": "public",
                "user_id": user_id,
                "username": username,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "message_type": "file" if file_info else "text"
            }
            
            if file_info:
                message_data["file_info"] = file_info
            
            # 加密消息
            encrypted_data = ChatEncryption.encrypt_message(message_data)
            
            file_path = self.public_dir / filename
            file_path.write_text(encrypted_data, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"发送群聊消息失败: {e}")
            return False
    
    def send_private_message(self, sender_id, sender_name, target_id, message, file_info=None):
        """发送私聊消息"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"msg_{timestamp}_{sender_id}.json"
            
            chat_pair = "_".join(sorted([sender_id, target_id]))
            private_chat_dir = self.private_dir / chat_pair
            private_chat_dir.mkdir(exist_ok=True)
            
            message_data = {
                "type": "private",
                "sender_id": sender_id,
                "sender_name": sender_name,
                "target_id": target_id,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "message_type": "file" if file_info else "text"
            }
            
            if file_info:
                message_data["file_info"] = file_info
            
            # 加密消息
            encrypted_data = ChatEncryption.encrypt_message(message_data)
            
            file_path = private_chat_dir / filename
            file_path.write_text(encrypted_data, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"发送私聊消息失败: {e}")
            return False
    
    def get_new_messages(self, user_id):
        """获取新消息"""
        new_messages = []
        
        try:
            # 获取群聊消息
            public_messages = self._scan_directory(self.public_dir)
            new_messages.extend(public_messages)
            
            # 获取私聊消息
            for private_dir in self.private_dir.iterdir():
                if private_dir.is_dir() and user_id in private_dir.name:
                    private_messages = self._scan_directory(private_dir)
                    new_messages.extend(private_messages)
            
            # 按时间戳排序
            new_messages.sort(key=lambda x: x.get('timestamp', ''))
            
        except Exception as e:
            print(f"获取新消息失败: {e}")
        
        return new_messages
    
    def _scan_directory(self, directory):
        """扫描目录获取消息"""
        messages = []
        
        try:
            if not directory.exists():
                return messages
            
            for file_path in directory.glob("msg_*.json"):
                filename = file_path.name
                
                if filename in self.message_cache:
                    continue
                
                try:
                    file_content = file_path.read_text(encoding='utf-8').strip()
                    
                    # 尝试解密
                    if ChatEncryption.is_encrypted_data(file_content):
                        message_data = ChatEncryption.decrypt_message(file_content)
                    else:
                        message_data = json.loads(file_content)
                    
                    if message_data:
                        message_data['_filename'] = filename
                        messages.append(message_data)
                        self.message_cache.add(filename)
                        
                except Exception as e:
                    print(f"读取消息文件失败 {file_path}: {e}")
                    
        except Exception as e:
            print(f"扫描目录失败 {directory}: {e}")
        
        return messages
    
    def update_user_heartbeat(self, user_id, username):
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
    
    def get_online_users(self):
        """获取在线用户"""
        online_users = []
        current_time = datetime.now()
        
        try:
            for heartbeat_file in self.users_dir.glob("*_heartbeat.json"):
                try:
                    with open(heartbeat_file, 'r', encoding='utf-8') as f:
                        heartbeat_data = json.load(f)
                    
                    last_active = datetime.fromisoformat(heartbeat_data.get('last_active', ''))
                    if (current_time - last_active).total_seconds() < 300:  # 5分钟内
                        online_users.append((
                            heartbeat_data.get('user_id', ''),
                            heartbeat_data.get('username', '')
                        ))
                        
                except Exception as e:
                    print(f"读取心跳文件失败 {heartbeat_file}: {e}")
                    
        except Exception as e:
            print(f"获取在线用户失败: {e}")
        
        return online_users
    
    def upload_file(self, file_path, user_id, username):
        """上传文件"""
        return self.file_manager.upload_file(file_path, user_id, username)

class NetworkShareChatClient:
    """网络共享目录聊天客户端（修复版）"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("局域网共享目录聊天（修复版）")
        self.root.geometry("900x700")
        
        # 基本配置
        self.share_path = r"\\catl-tfile\Temp1day每天凌晨两点清理数据01\imdmmm"
        self.chat_manager = None
        self.connected = False
        
        # 用户信息
        self.user_id = str(uuid.uuid4())[:8]
        self.username = ""
        
        # 下载设置
        self.download_dir = str(Path.home() / "Downloads" / "ChatFiles")
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        # 同步设置
        self.sync_thread = None
        self.sync_running = False
        self.heartbeat_thread = None
        
        # 私聊窗口
        self.private_chat_windows = {}
        self.online_users = {}
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建GUI组件"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="网络共享目录配置", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # 共享路径
        ttk.Label(config_frame, text="共享路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.share_path_var = tk.StringVar(value=self.share_path)
        share_path_entry = ttk.Entry(config_frame, textvariable=self.share_path_var, width=60)
        share_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 测试访问按钮
        test_btn = ttk.Button(config_frame, text="测试访问", command=self.test_share_access)
        test_btn.grid(row=0, column=2)
        
        # 访问状态
        self.access_status_var = tk.StringVar(value="未测试")
        status_label = ttk.Label(config_frame, textvariable=self.access_status_var)
        status_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # 用户信息区域
        user_frame = ttk.LabelFrame(main_frame, text="用户信息", padding="5")
        user_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        user_frame.columnconfigure(1, weight=1)
        
        # 用户名和ID
        ttk.Label(user_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(user_frame, textvariable=self.username_var, width=20)
        username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
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
        
        # 用户列表
        users_frame = ttk.LabelFrame(chat_frame, text="活跃用户", padding="5")
        users_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(10, 0))
        
        tip_label = ttk.Label(users_frame, text="双击用户名开始私聊", font=("Arial", 8))
        tip_label.pack(pady=(0, 5))
        
        self.users_listbox = tk.Listbox(users_frame, width=20, height=15)
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        self.users_listbox.bind('<Double-1>', self.start_private_chat)
        
        # 输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var)
        self.message_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_btn = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_btn.grid(row=0, column=1)
        
        # 文件按钮
        self.file_btn = ttk.Button(input_frame, text="📎 文件", command=self.send_file)
        self.file_btn.grid(row=0, column=2, padx=(5, 0))
        
        self.image_btn = ttk.Button(input_frame, text="🖼️ 图片", command=self.send_image)
        self.image_btn.grid(row=0, column=3, padx=(5, 0))
        
        # 初始状态
        self.set_chat_state(False)
        
        # 状态栏
        self.status_var = tk.StringVar(value="未连接")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 下载目录设置
        download_frame = ttk.Frame(main_frame)
        download_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(download_frame, text=f"下载目录: {self.download_dir}", font=("Arial", 8)).pack(side=tk.LEFT)
        ttk.Button(download_frame, text="📁 更改", command=self.set_download_directory).pack(side=tk.RIGHT)
    
    def set_chat_state(self, enabled):
        """设置聊天状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.message_entry.config(state=state)
        self.send_btn.config(state=state)
        self.file_btn.config(state=state)
        self.image_btn.config(state=state)
    
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
            else:
                self.access_status_var.set("❌ 访问失败")
        except Exception as e:
            self.access_status_var.set("❌ 访问异常")
            messagebox.showerror("访问错误", f"测试失败: {str(e)}")
    
    def toggle_connection(self):
        """切换连接状态"""
        if not self.connected:
            self.connect_to_share()
        else:
            self.disconnect_from_share()
    
    def connect_to_share(self):
        """连接到共享目录"""
        username = self.username_var.get().strip()
        user_id = self.user_id_var.get().strip()
        share_path = self.share_path_var.get().strip()
        
        if not all([username, user_id, share_path]):
            messagebox.showerror("错误", "请填写所有信息")
            return
        
        try:
            self.chat_manager = NetworkShareChatManager(share_path)
            
            if not self.chat_manager.check_access():
                messagebox.showerror("连接错误", "无法访问网络共享目录")
                return
            
            self.username = username
            self.user_id = user_id
            self.share_path = share_path
            
            self.connected = True
            self.connect_btn.config(text="离开聊天室")
            self.set_chat_state(True)
            self.status_var.set("已连接到共享聊天室")
            
            self.add_system_message("已加入局域网共享聊天室")
            self.add_system_message("消息已加密存储，支持文件传输")
            self.add_system_message(f"文件下载目录: {self.download_dir}")
            
            # 开始同步
            self.start_sync()
            
        except Exception as e:
            messagebox.showerror("连接错误", f"连接失败: {str(e)}")
    
    def disconnect_from_share(self):
        """断开连接"""
        self.connected = False
        self.stop_sync()
        self.connect_btn.config(text="加入聊天室")
        self.set_chat_state(False)
        self.status_var.set("未连接")
        self.add_system_message("已离开共享聊天室")
        self.users_listbox.delete(0, tk.END)
    
    def start_sync(self):
        """开始同步"""
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def stop_sync(self):
        """停止同步"""
        self.sync_running = False
    
    def _sync_loop(self):
        """同步循环"""
        while self.sync_running and self.connected:
            try:
                # 获取新消息
                new_messages = self.chat_manager.get_new_messages(self.user_id)
                for message in new_messages:
                    self.root.after(0, lambda msg=message: self._handle_message(msg))
                
                # 更新在线用户
                online_users = self.chat_manager.get_online_users()
                self.root.after(0, lambda users=online_users: self._update_online_users(users))
                
            except Exception as e:
                print(f"同步错误: {e}")
            
            time.sleep(3)  # 3秒间隔
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.connected:
            try:
                self.chat_manager.update_user_heartbeat(self.user_id, self.username)
            except Exception as e:
                print(f"心跳更新失败: {e}")
            
            time.sleep(30)  # 30秒间隔
    
    def _handle_message(self, message_data):
        """处理消息"""
        msg_type = message_data.get('type')
        timestamp = message_data.get('timestamp', '')
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = datetime.now().strftime("%H:%M:%S")
        
        if msg_type == 'public':
            username = message_data.get('username', '')
            user_id = message_data.get('user_id', '')
            message = message_data.get('message', '')
            message_type = message_data.get('message_type', 'text')
            
            if message_type == 'file':
                file_info = message_data.get('file_info', {})
                if user_id == self.user_id:
                    self.add_file_message(f"[{time_str}] 我", file_info)
                else:
                    self.add_file_message(f"[{time_str}] {username}", file_info)
            else:
                if user_id == self.user_id:
                    self.add_chat_message(f"[{time_str}] 我: {message}")
                else:
                    self.add_chat_message(f"[{time_str}] {username}: {message}")
        
        elif msg_type == 'private':
            sender_id = message_data.get('sender_id', '')
            sender_name = message_data.get('sender_name', '')
            target_id = message_data.get('target_id', '')
            message = message_data.get('message', '')
            
            if sender_id == self.user_id:
                chat_partner_id = target_id
                chat_partner_name = self.online_users.get(target_id, target_id)
                message_text = f"[{time_str}] 我: {message}"
            elif target_id == self.user_id:
                chat_partner_id = sender_id
                chat_partner_name = sender_name
                message_text = f"[{time_str}] {sender_name}: {message}"
            else:
                return
            
            self.show_private_message(chat_partner_id, chat_partner_name, message_text, message_data)
    
    def _update_online_users(self, users):
        """更新在线用户列表"""
        self.users_listbox.delete(0, tk.END)
        self.online_users.clear()
        
        for user_id, username in users:
            if user_id != self.user_id:
                self.online_users[user_id] = username
                display_text = f"{username} ({user_id})" if username != user_id else user_id
                self.users_listbox.insert(tk.END, display_text)
    
    def send_message(self, event=None):
        """发送消息"""
        message = self.message_var.get().strip()
        if not message or not self.connected:
            return
        
        success = self.chat_manager.send_public_message(self.user_id, self.username, message)
        if success:
            self.message_var.set("")
        else:
            messagebox.showerror("发送失败", "发送消息失败")
    
    def send_file(self):
        """发送文件"""
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到聊天室")
            return
        
        file_path = filedialog.askopenfilename(
            title="选择要发送的文件",
            filetypes=[
                ("文档文件", "*.txt;*.doc;*.docx;*.pdf"),
                ("压缩文件", "*.zip;*.rar;*.7z"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self._upload_and_send_file(file_path, "文件")
    
    def send_image(self):
        """发送图片"""
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到聊天室")
            return
        
        image_path = filedialog.askopenfilename(
            title="选择要发送的图片",
            filetypes=[
                ("图片文件", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp"),
                ("所有文件", "*.*")
            ]
        )
        
        if image_path:
            self._upload_and_send_file(image_path, "图片")
    
    def _upload_and_send_file(self, file_path, file_type):
        """上传并发送文件"""
        try:
            self.add_system_message(f"正在上传{file_type}...")
            self.root.update()
            
            file_info = self.chat_manager.upload_file(file_path, self.user_id, self.username)
            
            if file_info:
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
    
    def add_file_message(self, sender, file_info):
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
            
            icon = "🖼️" if file_type == 'image' else "📎"
            message_text = f"{sender} {icon} {file_name} ({size_str})"
            
            self.add_chat_message(message_text)
            self._add_download_link(file_info)
            
        except Exception as e:
            print(f"添加文件消息失败: {e}")
    
    def _add_download_link(self, file_info):
        """添加下载链接"""
        try:
            file_name = file_info.get('original_name', '未知文件')
            
            self.message_display.config(state=tk.NORMAL)
            
            # 插入下载链接
            download_text = f"    📥 "
            self.message_display.insert(tk.END, download_text)
            
            start_index = self.message_display.index(tk.END + "-1c")
            link_text = f"[点击下载到 {os.path.basename(self.download_dir)}]"
            self.message_display.insert(tk.END, link_text)
            end_index = self.message_display.index(tk.END + "-1c")
            
            # 添加样式和事件
            tag_name = f"download_{id(file_info)}"
            self.message_display.tag_add(tag_name, start_index, end_index)
            self.message_display.tag_config(tag_name, foreground="blue", underline=True)
            
            def download_file(event=None):
                self._download_file_simple(file_info)
            
            self.message_display.tag_bind(tag_name, "<Button-1>", download_file)
            self.message_display.tag_bind(tag_name, "<Enter>", 
                                        lambda e: self.message_display.config(cursor="hand2"))
            self.message_display.tag_bind(tag_name, "<Leave>", 
                                        lambda e: self.message_display.config(cursor=""))
            
            self.message_display.insert(tk.END, "\n")
            self.message_display.config(state=tk.DISABLED)
            self.message_display.see(tk.END)
            
        except Exception as e:
            print(f"添加下载链接失败: {e}")
    
    def _download_file_simple(self, file_info):
        """简单下载文件"""
        try:
            # 构建源文件路径
            filename = file_info.get('filename', file_info.get('original_name', ''))
            file_type = file_info.get('file_type', 'file')
            
            if file_type == 'image':
                source_path = self.chat_manager.file_manager.images_dir / filename
            else:
                source_path = self.chat_manager.file_manager.files_dir / filename
            
            if not source_path.exists():
                messagebox.showerror("错误", f"文件不存在: {filename}")
                return
            
            # 构建目标路径
            original_name = file_info.get('original_name', filename)
            target_path = Path(self.download_dir) / original_name
            
            # 处理重名文件
            counter = 1
            original_target = target_path
            while target_path.exists():
                stem = original_target.stem
                suffix = original_target.suffix
                target_path = original_target.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # 下载文件
            def download_task():
                try:
                    shutil.copy2(source_path, target_path)
                    
                    if target_path.exists():
                        success_msg = f"文件下载成功!\n保存位置: {target_path}"
                        self.root.after(0, lambda: messagebox.showinfo("下载完成", success_msg))
                        self.root.after(0, lambda: self.add_system_message(f"下载完成: {target_path.name}"))
                    else:
                        raise Exception("下载文件不存在")
                        
                except Exception as e:
                    error_msg = f"下载失败: {str(e)}"
                    self.root.after(0, lambda: messagebox.showerror("下载失败", error_msg))
            
            # 启动下载
            thread = threading.Thread(target=download_task, daemon=True)
            thread.start()
            self.add_system_message(f"开始下载: {original_name}")
            
        except Exception as e:
            messagebox.showerror("下载错误", f"下载失败: {str(e)}")
    
    def set_download_directory(self):
        """设置下载目录"""
        new_dir = filedialog.askdirectory(
            title="选择文件下载目录",
            initialdir=self.download_dir
        )
        
        if new_dir:
            self.download_dir = new_dir
            Path(self.download_dir).mkdir(parents=True, exist_ok=True)
            self.add_system_message(f"下载目录已更新: {self.download_dir}")
            
            # 更新界面显示
            for widget in self.root.grid_slaves(row=4):
                widget.destroy()
            
            download_frame = ttk.Frame(self.root.grid_slaves(row=0)[0])
            download_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
            
            ttk.Label(download_frame, text=f"下载目录: {self.download_dir}", font=("Arial", 8)).pack(side=tk.LEFT)
            ttk.Button(download_frame, text="📁 更改", command=self.set_download_directory).pack(side=tk.RIGHT)
    
    def start_private_chat(self, event=None):
        """开始私聊"""
        selection = self.users_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.users_listbox.get(selection[0])
        if '(' in selected_text and ')' in selected_text:
            user_id = selected_text.split('(')[-1].split(')')[0]
        else:
            user_id = selected_text
        
        username = self.online_users.get(user_id, user_id)
        self.open_private_chat_window(user_id, username)
    
    def open_private_chat_window(self, target_user_id, target_username):
        """打开私聊窗口"""
        if target_user_id in self.private_chat_windows:
            self.private_chat_windows[target_user_id].lift()
            return
        
        # 创建私聊窗口
        private_window = tk.Toplevel(self.root)
        private_window.title(f"共享私聊 - {target_username}")
        private_window.geometry("500x400")
        
        frame = ttk.Frame(private_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # 消息显示
        message_display = scrolledtext.ScrolledText(frame, height=15, state=tk.DISABLED)
        message_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 输入区域
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
        
        message_entry.bind('<Return>', send_private_message)
        
        send_btn = ttk.Button(input_frame, text="发送", command=send_private_message)
        send_btn.grid(row=0, column=1)
        
        # 存储窗口引用
        self.private_chat_windows[target_user_id] = private_window
        private_window.message_display = message_display
        
        def on_close():
            if target_user_id in self.private_chat_windows:
                del self.private_chat_windows[target_user_id]
            private_window.destroy()
        
        private_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # 添加欢迎消息
        message_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        message_display.insert(tk.END, f"[{timestamp}] [系统] 开始与 {target_username} 的私聊\n")
        message_display.config(state=tk.DISABLED)
        
        message_entry.focus()
    
    def show_private_message(self, chat_partner_id, chat_partner_name, message_text, message_data=None):
        """显示私聊消息"""
        if chat_partner_id not in self.private_chat_windows:
            self.open_private_chat_window(chat_partner_id, chat_partner_name)
        
        window = self.private_chat_windows[chat_partner_id]
        if hasattr(window, 'message_display'):
            window.message_display.config(state=tk.NORMAL)
            window.message_display.insert(tk.END, f"{message_text}\n")
            window.message_display.config(state=tk.DISABLED)
            window.message_display.see(tk.END)
            
            if not window.focus_displayof():
                window.bell()
    
    def add_system_message(self, message):
        """添加系统消息"""
        self.message_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_display.insert(tk.END, f"[{timestamp}] [系统] {message}\n")
        self.message_display.config(state=tk.DISABLED)
        self.message_display.see(tk.END)
    
    def add_chat_message(self, message):
        """添加聊天消息"""
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, f"{message}\n")
        self.message_display.config(state=tk.DISABLED)
        self.message_display.see(tk.END)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.connected:
            self.disconnect_from_share()
        self.root.destroy()
    
    def run(self):
        """运行客户端"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """主函数"""
    try:
        print("🚀 启动修复版网络共享聊天客户端")
        client = NetworkShareChatClient()
        client.run()
    except KeyboardInterrupt:
        print("客户端已停止")

if __name__ == "__main__":
    main()