#!/usr/bin/env python3
"""
基于腾讯云COS的聊天客户端
聊天记录存储在COS上，通过定时读取文件实现消息同步
"""

import sys
import os
import json
import time
import uuid
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, List
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# COS相关导入
try:
    from qcloud_cos import CosConfig, CosS3Client
    from qcloud_cos.cos_comm import format_region
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("请安装腾讯云COS SDK: pip install cos-python-sdk-v5")
    sys.exit(1)

class COSChatConfig:
    """COS聊天配置"""
    def __init__(self):
        self.secret_id = ""
        self.secret_key = ""
        self.region = "fjnds"
        self.bucket = ""
        self.chat_room_prefix = "chat-room"  # COS上的聊天室根目录
        self.domain = "cos.catlimd.com"  # 自定义域名

class COSChatManager:
    """COS聊天管理器"""
    def __init__(self, config: COSChatConfig):
        self.config = config
        self.client = self._create_client()
        self.last_sync_time = datetime.now()
        self.message_cache = set()  # 已处理的消息文件名缓存
        
    def _create_client(self):
        """创建COS客户端"""
        endpoint = "{}.{}".format(
            format_region(self.config.region, module='cos.', EnableOldDomain=False, EnableInternalDomain=False), 
            self.config.domain
        )
        
        cos_config = CosConfig(
            Region=self.config.region,
            SecretId=self.config.secret_id,
            SecretKey=self.config.secret_key,
            Endpoint=endpoint,
            Token=None,
            Scheme="https",
            VerifySSL=False,
            EnableInternalDomain=True,
            SignHost=True
        )
        return CosS3Client(cos_config)
    
    def send_public_message(self, user_id: str, username: str, message: str):
        """发送群聊消息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
        filename = f"msg_{timestamp}_{user_id}.json"
        
        message_data = {
            "type": "public",
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        cos_key = f"{self.config.chat_room_prefix}/public/{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.config.bucket,
                Key=cos_key,
                Body=json.dumps(message_data, ensure_ascii=False).encode('utf-8')
            )
            return True
        except Exception as e:
            print(f"发送群聊消息失败: {e}")
            return False
    
    def send_private_message(self, sender_id: str, sender_name: str, target_id: str, message: str):
        """发送私聊消息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"msg_{timestamp}_{sender_id}.json"
        
        # 私聊目录：按用户ID字母序排列确保一致性
        chat_pair = "_".join(sorted([sender_id, target_id]))
        
        message_data = {
            "type": "private",
            "sender_id": sender_id,
            "sender_name": sender_name,
            "target_id": target_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        cos_key = f"{self.config.chat_room_prefix}/private/{chat_pair}/{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.config.bucket,
                Key=cos_key,
                Body=json.dumps(message_data, ensure_ascii=False).encode('utf-8')
            )
            return True
        except Exception as e:
            print(f"发送私聊消息失败: {e}")
            return False
    
    def get_new_messages(self, message_types=['public', 'private']):
        """获取新消息"""
        new_messages = []
        
        for msg_type in message_types:
            if msg_type == 'public':
                prefix = f"{self.config.chat_room_prefix}/public/"
                messages = self._get_messages_from_prefix(prefix)
                new_messages.extend(messages)
            elif msg_type == 'private':
                # 获取所有私聊消息
                prefix = f"{self.config.chat_room_prefix}/private/"
                messages = self._get_messages_from_prefix(prefix, recursive=True)
                new_messages.extend(messages)
        
        # 按时间戳排序
        new_messages.sort(key=lambda x: x.get('timestamp', ''))
        return new_messages
    
    def _get_messages_from_prefix(self, prefix: str, recursive=False):
        """从指定前缀获取消息"""
        messages = []
        marker = ""
        
        try:
            while True:
                response = self.client.list_objects(
                    Bucket=self.config.bucket,
                    Prefix=prefix,
                    Marker=marker,
                    MaxKeys=1000
                )
                
                if 'Contents' not in response:
                    break
                
                for content in response['Contents']:
                    key = content['Key']
                    filename = os.path.basename(key)
                    
                    # 跳过已处理的消息
                    if filename in self.message_cache:
                        continue
                    
                    # 只处理JSON消息文件
                    if not filename.startswith('msg_') or not filename.endswith('.json'):
                        continue
                    
                    try:
                        # 获取文件内容
                        obj_response = self.client.get_object(
                            Bucket=self.config.bucket,
                            Key=key
                        )
                        content_data = obj_response['Body'].read().decode('utf-8')
                        message_data = json.loads(content_data)
                        
                        # 添加文件信息
                        message_data['_filename'] = filename
                        message_data['_cos_key'] = key
                        
                        messages.append(message_data)
                        self.message_cache.add(filename)
                        
                    except Exception as e:
                        print(f"读取消息文件失败 {key}: {e}")
                
                if response['IsTruncated'] == 'false':
                    break
                    
                marker = response['NextMarker']
                
        except Exception as e:
            print(f"获取消息列表失败: {e}")
        
        return messages
    
    def get_online_users(self):
        """获取在线用户列表（基于最近消息活动）"""
        # 获取最近5分钟的消息来判断在线用户
        recent_messages = self.get_new_messages(['public'])
        current_time = datetime.now()
        online_users = set()
        
        for msg in recent_messages:
            try:
                msg_time = datetime.fromisoformat(msg.get('timestamp', ''))
                if (current_time - msg_time).total_seconds() < 300:  # 5分钟内活跃
                    online_users.add((msg.get('user_id', ''), msg.get('username', '')))
            except:
                pass
        
        return list(online_users)

class COSChatClient:
    """基于COS的聊天客户端"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("COS云端聊天室")
        self.root.geometry("900x700")
        
        # COS相关
        self.cos_config = COSChatConfig()
        self.cos_manager = None
        self.connected = False
        
        # 用户信息
        self.user_id = str(uuid.uuid4())[:8]
        self.username = ""
        
        # 消息同步
        self.sync_thread = None
        self.sync_running = False
        self.sync_interval = 3  # 3秒同步间隔
        
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
        
        # COS配置区域
        config_frame = ttk.LabelFrame(main_frame, text="腾讯云COS配置", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Secret ID
        ttk.Label(config_frame, text="Secret ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.secret_id_var = tk.StringVar()
        secret_id_entry = ttk.Entry(config_frame, textvariable=self.secret_id_var, width=30)
        secret_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Secret Key
        ttk.Label(config_frame, text="Secret Key:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.secret_key_var = tk.StringVar()
        secret_key_entry = ttk.Entry(config_frame, textvariable=self.secret_key_var, show="*", width=30)
        secret_key_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        # Bucket和Region
        ttk.Label(config_frame, text="Bucket:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.bucket_var = tk.StringVar()
        bucket_entry = ttk.Entry(config_frame, textvariable=self.bucket_var, width=30)
        bucket_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        
        ttk.Label(config_frame, text="Region:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.region_var = tk.StringVar(value="fjnds")
        region_entry = ttk.Entry(config_frame, textvariable=self.region_var, width=20)
        region_entry.grid(row=1, column=3, sticky=tk.W, pady=(5, 0))
        
        # 聊天室路径
        ttk.Label(config_frame, text="聊天室路径:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.chat_room_var = tk.StringVar(value="chat-room")
        chat_room_entry = ttk.Entry(config_frame, textvariable=self.chat_room_var, width=30)
        chat_room_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        
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
        self.connect_btn = ttk.Button(user_frame, text="连接COS聊天室", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        # 聊天区域
        chat_frame = ttk.LabelFrame(main_frame, text="COS云端聊天室", padding="5")
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
        
        # 初始状态设置
        self.set_chat_state(False)
        
        # 状态栏
        self.status_var = tk.StringVar(value="未连接到COS")
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
    
    def set_chat_state(self, enabled: bool):
        """设置聊天界面状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.message_entry.config(state=state)
        self.send_btn.config(state=state)
    
    def toggle_connection(self):
        """切换连接状态"""
        if not self.connected:
            self.connect_to_cos()
        else:
            self.disconnect_from_cos()
    
    def connect_to_cos(self):
        """连接到COS"""
        # 验证输入
        username = self.username_var.get().strip()
        user_id = self.user_id_var.get().strip()
        secret_id = self.secret_id_var.get().strip()
        secret_key = self.secret_key_var.get().strip()
        bucket = self.bucket_var.get().strip()
        
        if not all([username, user_id, secret_id, secret_key, bucket]):
            messagebox.showerror("错误", "请填写所有必要信息")
            return
        
        # 更新配置
        self.username = username
        self.user_id = user_id
        self.cos_config.secret_id = secret_id
        self.cos_config.secret_key = secret_key
        self.cos_config.bucket = bucket
        self.cos_config.region = self.region_var.get().strip()
        self.cos_config.chat_room_prefix = self.chat_room_var.get().strip()
        
        try:
            # 创建COS管理器
            self.cos_manager = COSChatManager(self.cos_config)
            
            # 测试连接
            self.cos_manager.client.head_bucket(Bucket=self.cos_config.bucket)
            
            # 连接成功
            self.connected = True
            self.connect_btn.config(text="断开连接")
            self.set_chat_state(True)
            self.status_var.set(f"已连接到COS聊天室: {bucket}")
            self.add_system_message("已连接到COS云端聊天室")
            self.add_system_message("消息将存储在腾讯云COS上，支持群聊和私聊")
            
            # 开始消息同步
            self.start_message_sync()
            
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到COS: {str(e)}")
    
    def disconnect_from_cos(self):
        """断开COS连接"""
        self.connected = False
        self.stop_message_sync()
        self.connect_btn.config(text="连接COS聊天室")
        self.set_chat_state(False)
        self.status_var.set("未连接到COS")
        self.sync_status_var.set("同步状态: 已停止")
        self.add_system_message("已断开COS连接")
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
    
    def _sync_messages(self):
        """消息同步循环"""
        while self.sync_running and self.connected:
            try:
                # 获取新消息
                new_messages = self.cos_manager.get_new_messages()
                
                # 在主线程中处理消息
                for message in new_messages:
                    self.root.after(0, lambda msg=message: self._handle_message(msg))
                
                # 更新在线用户列表
                online_users = self.cos_manager.get_online_users()
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
            self.show_private_message(chat_partner_id, chat_partner_name, message_text)
    
    def _update_online_users(self, users: List[tuple]):
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
        
        # 发送到COS
        success = self.cos_manager.send_public_message(self.user_id, self.username, message)
        if success:
            self.message_var.set("")  # 清空输入框
        else:
            messagebox.showerror("发送失败", "发送消息到COS失败")
    
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
            # 如果窗口已存在，则显示到前台
            self.private_chat_windows[target_user_id].lift()
            self.private_chat_windows[target_user_id].focus()
            return
        
        # 创建新的私聊窗口
        private_window = tk.Toplevel(self.root)
        private_window.title(f"COS私聊 - {target_username}")
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
                success = self.cos_manager.send_private_message(
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
        self.add_private_message(target_user_id, f"开始与 {target_username} 的COS私聊")
        
        message_entry.focus()
    
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
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.connected:
            self.disconnect_from_cos()
        self.root.destroy()
    
    def run(self):
        """运行客户端"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.mainloop()

def main():
    """主函数"""
    try:
        client = COSChatClient()
        client.run()
    except KeyboardInterrupt:
        print("COS聊天客户端已停止")

if __name__ == "__main__":
    main()