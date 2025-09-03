#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络共享聊天应用 - 无加密版本
修复了UTF-8解码错误和Tkinter文件对话框参数错误
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import socket
import threading
import json
import os
import time
from datetime import datetime
import base64


class NetworkShareChat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("网络共享聊天")
        self.root.geometry("1000x700")
        
        # 网络相关
        self.server_socket = None
        self.client_socket = None
        self.is_server = False
        self.is_connected = False
        self.clients = {}
        
        # 文件共享相关 - 移除加密
        self.shared_files = {}  # 存储共享文件 {filename: file_data}
        self.download_folder = os.path.expanduser("~/Downloads")
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 连接控制区域
        conn_frame = ttk.LabelFrame(main_frame, text="连接设置", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 服务器/客户端选择
        ttk.Label(conn_frame, text="模式:").grid(row=0, column=0, padx=(0, 5))
        self.mode_var = tk.StringVar(value="server")
        ttk.Radiobutton(conn_frame, text="服务器", variable=self.mode_var, value="server").grid(row=0, column=1)
        ttk.Radiobutton(conn_frame, text="客户端", variable=self.mode_var, value="client").grid(row=0, column=2)
        
        # IP和端口设置
        ttk.Label(conn_frame, text="IP:").grid(row=0, column=3, padx=(20, 5))
        self.ip_var = tk.StringVar(value="localhost")
        ttk.Entry(conn_frame, textvariable=self.ip_var, width=15).grid(row=0, column=4)
        
        ttk.Label(conn_frame, text="端口:").grid(row=0, column=5, padx=(10, 5))
        self.port_var = tk.StringVar(value="8888")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=8).grid(row=0, column=6)
        
        # 连接按钮
        self.connect_btn = ttk.Button(conn_frame, text="连接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=7, padx=(10, 0))
        
        # 状态显示
        self.status_var = tk.StringVar(value="未连接")
        ttk.Label(conn_frame, textvariable=self.status_var).grid(row=0, column=8, padx=(10, 0))
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 左侧：聊天区域
        self.create_chat_area(left_frame)
        
        # 右侧：文件管理区域
        self.create_file_area(right_frame)
        
    def create_chat_area(self, parent):
        """创建聊天区域"""
        chat_frame = ttk.LabelFrame(parent, text="聊天区域", padding="5")
        chat_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # 聊天显示区域
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=20, state='disabled')
        self.chat_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 消息输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var)
        self.message_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message)
        
        ttk.Button(input_frame, text="发送", command=self.send_message).grid(row=0, column=1)
        
    def create_file_area(self, parent):
        """创建文件管理区域"""
        file_frame = ttk.LabelFrame(parent, text="文件共享", padding="5")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)
        
        # 文件操作按钮
        btn_frame = ttk.Frame(file_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(btn_frame, text="上传文件", command=self.upload_file).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(btn_frame, text="下载文件", command=self.download_selected_file).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(btn_frame, text="删除文件", command=self.delete_selected_file).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(btn_frame, text="刷新列表", command=self.refresh_file_list).grid(row=0, column=3)
        
        # 文件列表
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建带滚动条的列表框
        self.file_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.file_listbox.bind('<Double-Button-1>', self.on_file_double_click)
        
    def toggle_connection(self):
        """切换连接状态"""
        if not self.is_connected:
            self.start_connection()
        else:
            self.stop_connection()
            
    def start_connection(self):
        """开始连接"""
        try:
            ip = self.ip_var.get()
            port = int(self.port_var.get())
            
            if self.mode_var.get() == "server":
                self.start_server(ip, port)
            else:
                self.start_client(ip, port)
                
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
            
    def start_server(self, ip, port):
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((ip, port))
            self.server_socket.listen(5)
            
            self.is_server = True
            self.is_connected = True
            self.status_var.set(f"服务器运行中 - {ip}:{port}")
            self.connect_btn.config(text="断开")
            
            # 在新线程中接受连接
            threading.Thread(target=self.accept_connections, daemon=True).start()
            
            self.add_chat_message("系统", f"服务器启动成功，监听 {ip}:{port}")
            
        except Exception as e:
            self.status_var.set("连接失败")
            raise e
            
    def start_client(self, ip, port):
        """启动客户端"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
            
            self.is_server = False
            self.is_connected = True
            self.status_var.set(f"已连接到 {ip}:{port}")
            self.connect_btn.config(text="断开")
            
            # 在新线程中接收消息
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            self.add_chat_message("系统", f"已连接到服务器 {ip}:{port}")
            
        except Exception as e:
            self.status_var.set("连接失败")
            raise e
            
    def stop_connection(self):
        """停止连接"""
        self.is_connected = False
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            
        self.clients.clear()
        self.status_var.set("未连接")
        self.connect_btn.config(text="连接")
        self.add_chat_message("系统", "连接已断开")
        
    def accept_connections(self):
        """接受客户端连接"""
        while self.is_connected and self.server_socket:
            try:
                client_socket, addr = self.server_socket.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                self.clients[client_id] = client_socket
                
                self.add_chat_message("系统", f"客户端 {client_id} 已连接")
                
                # 为每个客户端创建接收线程
                threading.Thread(target=self.handle_client, args=(client_socket, client_id), daemon=True).start()
                
            except Exception as e:
                if self.is_connected:
                    self.add_chat_message("系统", f"接受连接时出错: {str(e)}")
                break
                
    def handle_client(self, client_socket, client_id):
        """处理客户端消息"""
        while self.is_connected:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                message = data.decode('utf-8')
                self.process_received_message(message, client_id)
                
            except Exception as e:
                self.add_chat_message("系统", f"处理客户端 {client_id} 消息时出错: {str(e)}")
                break
                
        # 清理断开的客户端
        if client_id in self.clients:
            del self.clients[client_id]
            self.add_chat_message("系统", f"客户端 {client_id} 已断开")
            
    def receive_messages(self):
        """接收服务器消息"""
        while self.is_connected and self.client_socket:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                    
                message = data.decode('utf-8')
                self.process_received_message(message, "服务器")
                
            except Exception as e:
                if self.is_connected:
                    self.add_chat_message("系统", f"接收消息时出错: {str(e)}")
                break
                
    def process_received_message(self, message, sender):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'chat')
            
            if msg_type == 'chat':
                self.add_chat_message(sender, data.get('content', ''))
            elif msg_type == 'file_list':
                self.update_remote_file_list(data.get('files', []))
            elif msg_type == 'file_data':
                self.receive_file_data(data)
                
        except json.JSONDecodeError:
            # 如果不是JSON，当作普通聊天消息处理
            self.add_chat_message(sender, message)
            
    def send_message(self, event=None):
        """发送聊天消息"""
        message = self.message_var.get().strip()
        if not message or not self.is_connected:
            return
            
        try:
            msg_data = {
                'type': 'chat',
                'content': message,
                'timestamp': datetime.now().isoformat()
            }
            
            json_message = json.dumps(msg_data, ensure_ascii=False)
            
            if self.is_server:
                # 服务器广播给所有客户端
                for client_socket in self.clients.values():
                    try:
                        client_socket.send(json_message.encode('utf-8'))
                    except:
                        pass
            else:
                # 客户端发送给服务器
                self.client_socket.send(json_message.encode('utf-8'))
                
            self.add_chat_message("我", message)
            self.message_var.set("")
            
        except Exception as e:
            messagebox.showerror("错误", f"发送消息失败: {str(e)}")
            
    def add_chat_message(self, sender, message):
        """添加聊天消息到显示区域"""
        self.chat_text.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_text.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
        
    def upload_file(self):
        """上传文件到共享列表 - 无加密版本"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择要上传的文件",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文本文件", "*.txt"),
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("文档文件", "*.pdf;*.doc;*.docx")
                ]
            )
            
            if file_path:
                file_name = os.path.basename(file_path)
                
                # 读取文件内容 - 无加密处理
                try:
                    # 尝试以文本模式读取
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        file_data = {
                            'name': file_name,
                            'content': file_content,
                            'type': 'text',
                            'size': len(file_content.encode('utf-8'))
                        }
                except UnicodeDecodeError:
                    # 如果文本读取失败，以二进制模式读取
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        # 转换为base64以便JSON传输
                        file_data = {
                            'name': file_name,
                            'content': base64.b64encode(file_content).decode('ascii'),
                            'type': 'binary',
                            'size': len(file_content)
                        }
                
                # 存储到共享文件列表
                self.shared_files[file_name] = file_data
                self.refresh_file_list()
                
                self.add_chat_message("系统", f"文件 '{file_name}' 上传成功 ({file_data['size']} 字节)")
                
                # 通知其他用户文件列表更新
                self.broadcast_file_list()
                
        except Exception as e:
            messagebox.showerror("错误", f"上传文件失败: {str(e)}")
            
    def download_selected_file(self):
        """下载选中的文件 - 修复版本，无加密处理"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个文件")
                return
                
            # 获取选中的文件信息
            selected_item = self.file_listbox.get(selection[0])
            # 解析文件名（假设格式为 "filename (size bytes)"）
            file_name = selected_item.split(' (')[0] if ' (' in selected_item else selected_item
            
            if file_name not in self.shared_files:
                messagebox.showerror("错误", "文件不存在")
                return
                
            # 修复：使用正确的参数名 initialfile
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_name,  # ✅ 修复：使用 initialfile 而不是 initialname
                defaultextension="",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文本文件", "*.txt"),
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("文档文件", "*.pdf;*.doc;*.docx")
                ]
            )
            
            if save_path:
                file_data = self.shared_files[file_name]
                
                # 保存文件 - 无解密处理
                try:
                    if file_data['type'] == 'text':
                        # 文本文件
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(file_data['content'])
                    else:
                        # 二进制文件，从base64解码
                        content = base64.b64decode(file_data['content'])
                        with open(save_path, 'wb') as f:
                            f.write(content)
                            
                    messagebox.showinfo("成功", f"文件已保存到: {save_path}")
                    self.add_chat_message("系统", f"文件 '{file_name}' 下载完成")
                    
                except Exception as e:
                    messagebox.showerror("错误", f"保存文件失败: {str(e)}")
                    
        except Exception as e:
            messagebox.showerror("错误", f"下载文件失败: {str(e)}")
            
    def on_file_double_click(self, event=None):
        """文件双击处理 - 修复版本"""
        try:
            self.download_selected_file()
        except Exception as e:
            messagebox.showerror("错误", f"处理文件双击事件失败: {str(e)}")
            
    def delete_selected_file(self):
        """删除选中的文件"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个文件")
                return
                
            selected_item = self.file_listbox.get(selection[0])
            file_name = selected_item.split(' (')[0] if ' (' in selected_item else selected_item
            
            if file_name in self.shared_files:
                # 确认删除
                if messagebox.askyesno("确认", f"确定要删除文件 '{file_name}' 吗？"):
                    del self.shared_files[file_name]
                    self.refresh_file_list()
                    self.add_chat_message("系统", f"文件 '{file_name}' 已删除")
                    self.broadcast_file_list()
            else:
                messagebox.showerror("错误", "文件不存在")
                
        except Exception as e:
            messagebox.showerror("错误", f"删除文件失败: {str(e)}")
            
    def refresh_file_list(self):
        """刷新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        
        for file_name, file_data in self.shared_files.items():
            size_text = f" ({file_data['size']} 字节)"
            type_text = f" [{file_data['type']}]"
            display_text = f"{file_name}{size_text}{type_text}"
            self.file_listbox.insert(tk.END, display_text)
            
    def broadcast_file_list(self):
        """广播文件列表给所有连接的用户"""
        try:
            file_list = []
            for file_name, file_data in self.shared_files.items():
                file_list.append({
                    'name': file_name,
                    'size': file_data['size'],
                    'type': file_data['type']
                })
                
            msg_data = {
                'type': 'file_list',
                'files': file_list
            }
            
            json_message = json.dumps(msg_data, ensure_ascii=False)
            
            if self.is_server:
                # 服务器广播给所有客户端
                for client_socket in self.clients.values():
                    try:
                        client_socket.send(json_message.encode('utf-8'))
                    except:
                        pass
            else:
                # 客户端发送给服务器
                if self.client_socket:
                    self.client_socket.send(json_message.encode('utf-8'))
                    
        except Exception as e:
            self.add_chat_message("系统", f"广播文件列表失败: {str(e)}")
            
    def update_remote_file_list(self, files):
        """更新远程文件列表"""
        # 这里可以显示远程文件，或者合并到本地列表
        # 为简化，这里只显示消息
        self.add_chat_message("系统", f"收到远程文件列表，共 {len(files)} 个文件")
        
    def receive_file_data(self, data):
        """接收文件数据"""
        try:
            file_name = data.get('name')
            file_content = data.get('content')
            file_type = data.get('type', 'text')
            
            if file_name and file_content:
                self.shared_files[file_name] = {
                    'name': file_name,
                    'content': file_content,
                    'type': file_type,
                    'size': len(file_content)
                }
                self.refresh_file_list()
                self.add_chat_message("系统", f"收到文件: {file_name}")
                
        except Exception as e:
            self.add_chat_message("系统", f"接收文件失败: {str(e)}")
            
    def run(self):
        """运行应用"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """关闭应用时的清理工作"""
        self.stop_connection()
        self.root.destroy()


if __name__ == "__main__":
    print("启动网络共享聊天应用...")
    app = NetworkShareChat()
    app.run()