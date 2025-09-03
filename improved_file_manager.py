#!/usr/bin/env python3
"""
改进的文件管理器
提供稳定的文件下载和管理功能
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
import threading
import json
from typing import Dict, List, Optional

class FileManagerWindow:
    """文件管理窗口"""
    
    def __init__(self, parent, chat_manager, user_id: str, username: str):
        self.parent = parent
        self.chat_manager = chat_manager
        self.user_id = user_id
        self.username = username
        
        # 创建文件管理窗口
        self.window = tk.Toplevel(parent)
        self.window.title("文件管理器")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # 文件列表
        self.file_list = []
        self.selected_file = None
        
        # 创建界面
        self.create_widgets()
        
        # 加载文件列表
        self.refresh_file_list()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📁 共享文件管理器", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar_frame, text="🔄 刷新", command=self.refresh_file_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="📤 上传文件", command=self.upload_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="🖼️ 上传图片", command=self.upload_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # 文件列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview显示文件
        columns = ("name", "type", "size", "uploader", "time")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        self.file_tree.heading("name", text="文件名")
        self.file_tree.heading("type", text="类型")
        self.file_tree.heading("size", text="大小")
        self.file_tree.heading("uploader", text="上传者")
        self.file_tree.heading("time", text="上传时间")
        
        # 设置列宽
        self.file_tree.column("name", width=200)
        self.file_tree.column("type", width=80)
        self.file_tree.column("size", width=100)
        self.file_tree.column("uploader", width=120)
        self.file_tree.column("time", width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        
        # 操作按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.download_btn = ttk.Button(button_frame, text="📥 下载选中文件", 
                                      command=self.download_selected_file, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.preview_btn = ttk.Button(button_frame, text="👁️ 预览", 
                                     command=self.preview_selected_file, state=tk.DISABLED)
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.info_btn = ttk.Button(button_frame, text="ℹ️ 详细信息", 
                                  command=self.show_file_info, state=tk.DISABLED)
        self.info_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def refresh_file_list(self):
        """刷新文件列表"""
        self.status_var.set("正在加载文件列表...")
        self.window.update()
        
        try:
            # 清空当前列表
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            
            # 获取文件统计信息
            stats = self.chat_manager.get_file_storage_stats()
            
            # 扫描文件目录
            self.file_list = []
            self._scan_directory(self.chat_manager.file_manager.files_dir, "文件")
            self._scan_directory(self.chat_manager.file_manager.images_dir, "图片")
            
            # 按上传时间排序（最新的在前）
            self.file_list.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
            
            # 填充到TreeView
            for file_info in self.file_list:
                self.file_tree.insert("", tk.END, values=(
                    file_info['original_name'],
                    file_info['type'],
                    self._format_size(file_info['size']),
                    file_info['uploader'],
                    self._format_time(file_info['upload_time'])
                ))
            
            self.status_var.set(f"加载完成，共 {len(self.file_list)} 个文件")
            
        except Exception as e:
            self.status_var.set(f"加载失败: {str(e)}")
            messagebox.showerror("错误", f"加载文件列表失败: {str(e)}")
    
    def _scan_directory(self, directory: Path, file_type: str):
        """扫描目录获取文件信息"""
        if not directory.exists():
            return
        
        for file_path in directory.glob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    stat = file_path.stat()
                    
                    # 从文件名解析信息
                    filename = file_path.name
                    parts = filename.split('_')
                    
                    if len(parts) >= 3:
                        # 格式：YYYYMMDD_HHMMSS_userid_hash.ext
                        date_part = parts[0]
                        time_part = parts[1]
                        user_part = parts[2]
                        
                        # 构造上传时间
                        try:
                            upload_time = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                        except:
                            upload_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 获取原始文件名（去掉时间戳和用户ID前缀）
                        original_name = filename
                        if len(parts) >= 4:
                            # 如果有哈希部分，重新构造原始名称
                            original_name = filename  # 暂时使用完整文件名
                    else:
                        upload_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        user_part = "unknown"
                        original_name = filename
                    
                    file_info = {
                        'filename': filename,
                        'original_name': original_name,
                        'type': file_type,
                        'size': stat.st_size,
                        'uploader': user_part,
                        'upload_time': upload_time,
                        'full_path': str(file_path),
                        'relative_path': str(file_path.relative_to(self.chat_manager.share_path))
                    }
                    
                    self.file_list.append(file_info)
                    
                except Exception as e:
                    print(f"处理文件失败 {file_path}: {e}")
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    
    def _format_time(self, time_str: str) -> str:
        """格式化时间"""
        try:
            if '-' in time_str:
                return time_str
            else:
                # 如果是ISO格式，转换为易读格式
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return time_str
    
    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.file_tree.selection()
        if selection:
            # 获取选中的文件索引
            item = selection[0]
            index = self.file_tree.index(item)
            
            if 0 <= index < len(self.file_list):
                self.selected_file = self.file_list[index]
                self.download_btn.config(state=tk.NORMAL)
                self.info_btn.config(state=tk.NORMAL)
                
                # 如果是图片，启用预览按钮
                if self.selected_file['type'] == '图片':
                    self.preview_btn.config(state=tk.NORMAL)
                else:
                    self.preview_btn.config(state=tk.DISABLED)
                    
                self.status_var.set(f"已选择: {self.selected_file['original_name']}")
        else:
            self.selected_file = None
            self.download_btn.config(state=tk.DISABLED)
            self.preview_btn.config(state=tk.DISABLED)
            self.info_btn.config(state=tk.DISABLED)
            self.status_var.set("就绪")
    
    def on_file_double_click(self, event):
        """文件双击事件"""
        if self.selected_file:
            self.download_selected_file()
    
    def download_selected_file(self):
        """下载选中的文件"""
        if not self.selected_file:
            messagebox.showwarning("提示", "请先选择要下载的文件")
            return
        
        # 选择保存位置
        save_path = filedialog.asksaveasfilename(
            title="保存文件",
            initialfile=self.selected_file['original_name'],
            defaultextension=Path(self.selected_file['original_name']).suffix
        )
        
        if save_path:
            self._download_file_thread(save_path)
    
    def _download_file_thread(self, save_path: str):
        """在后台线程中下载文件"""
        def download_task():
            try:
                self.status_var.set("正在下载文件...")
                self.window.update()
                
                # 复制文件
                source_path = Path(self.selected_file['full_path'])
                target_path = Path(save_path)
                
                if not source_path.exists():
                    raise FileNotFoundError(f"源文件不存在: {source_path}")
                
                # 复制文件
                import shutil
                shutil.copy2(source_path, target_path)
                
                # 更新状态
                self.window.after(0, lambda: self.status_var.set(f"下载完成: {target_path}"))
                self.window.after(0, lambda: messagebox.showinfo("下载完成", f"文件已保存到:\n{target_path}"))
                
            except Exception as e:
                error_msg = f"下载失败: {str(e)}"
                self.window.after(0, lambda: self.status_var.set(error_msg))
                self.window.after(0, lambda: messagebox.showerror("下载失败", error_msg))
        
        # 在后台线程中执行下载
        thread = threading.Thread(target=download_task, daemon=True)
        thread.start()
    
    def preview_selected_file(self):
        """预览选中的文件"""
        if not self.selected_file:
            return
        
        if self.selected_file['type'] == '图片':
            self._preview_image()
        else:
            messagebox.showinfo("提示", "该文件类型不支持预览")
    
    def _preview_image(self):
        """预览图片"""
        try:
            # 创建预览窗口
            preview_window = tk.Toplevel(self.window)
            preview_window.title(f"图片预览 - {self.selected_file['original_name']}")
            preview_window.geometry("600x500")
            
            # 尝试使用PIL显示图片
            try:
                from PIL import Image, ImageTk
                
                # 加载图片
                image_path = self.selected_file['full_path']
                image = Image.open(image_path)
                
                # 调整图片大小以适应窗口
                image.thumbnail((550, 400), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # 显示图片
                label = tk.Label(preview_window, image=photo)
                label.image = photo  # 保持引用
                label.pack(pady=10)
                
                # 图片信息
                info_text = f"文件名: {self.selected_file['original_name']}\n"
                info_text += f"大小: {self._format_size(self.selected_file['size'])}\n"
                info_text += f"上传者: {self.selected_file['uploader']}\n"
                info_text += f"上传时间: {self.selected_file['upload_time']}"
                
                info_label = ttk.Label(preview_window, text=info_text, justify=tk.LEFT)
                info_label.pack(pady=10)
                
            except ImportError:
                # 如果没有PIL，显示文件信息
                info_text = f"图片预览需要安装PIL库\n\n"
                info_text += f"文件名: {self.selected_file['original_name']}\n"
                info_text += f"大小: {self._format_size(self.selected_file['size'])}\n"
                info_text += f"上传者: {self.selected_file['uploader']}\n"
                info_text += f"上传时间: {self.selected_file['upload_time']}\n\n"
                info_text += "安装方法: pip install Pillow"
                
                info_label = ttk.Label(preview_window, text=info_text, justify=tk.LEFT)
                info_label.pack(pady=20)
                
        except Exception as e:
            messagebox.showerror("预览失败", f"无法预览图片: {str(e)}")
    
    def show_file_info(self):
        """显示文件详细信息"""
        if not self.selected_file:
            return
        
        info_text = f"文件详细信息\n{'='*30}\n\n"
        info_text += f"原始文件名: {self.selected_file['original_name']}\n"
        info_text += f"存储文件名: {self.selected_file['filename']}\n"
        info_text += f"文件类型: {self.selected_file['type']}\n"
        info_text += f"文件大小: {self._format_size(self.selected_file['size'])}\n"
        info_text += f"上传者: {self.selected_file['uploader']}\n"
        info_text += f"上传时间: {self.selected_file['upload_time']}\n"
        info_text += f"存储路径: {self.selected_file['relative_path']}\n"
        
        messagebox.showinfo("文件信息", info_text)
    
    def upload_file(self):
        """上传文件"""
        file_path = filedialog.askopenfilename(
            title="选择要上传的文件",
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
            self._upload_file(file_path, "文件")
    
    def upload_image(self):
        """上传图片"""
        image_path = filedialog.askopenfilename(
            title="选择要上传的图片",
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
            self._upload_file(image_path, "图片")
    
    def _upload_file(self, file_path: str, file_type: str):
        """上传文件的后台任务"""
        def upload_task():
            try:
                self.window.after(0, lambda: self.status_var.set(f"正在上传{file_type}..."))
                
                # 上传文件
                file_info = self.chat_manager.upload_file(file_path, self.user_id, self.username)
                
                if file_info:
                    # 发送文件消息
                    file_name = file_info['original_name']
                    message = f"上传了{file_type}: {file_name}"
                    
                    success = self.chat_manager.send_public_message(
                        self.user_id, self.username, message, file_info
                    )
                    
                    if success:
                        self.window.after(0, lambda: self.status_var.set(f"{file_type}上传成功"))
                        self.window.after(0, self.refresh_file_list)  # 刷新文件列表
                        self.window.after(0, lambda: messagebox.showinfo("上传成功", f"{file_type}上传成功: {file_name}"))
                    else:
                        self.window.after(0, lambda: self.status_var.set(f"{file_type}发送失败"))
                        self.window.after(0, lambda: messagebox.showerror("发送失败", f"{file_type}上传成功但发送消息失败"))
                else:
                    self.window.after(0, lambda: self.status_var.set(f"{file_type}上传失败"))
                    self.window.after(0, lambda: messagebox.showerror("上传失败", f"{file_type}上传失败"))
                    
            except Exception as e:
                error_msg = f"上传{file_type}失败: {str(e)}"
                self.window.after(0, lambda: self.status_var.set(error_msg))
                self.window.after(0, lambda: messagebox.showerror("上传失败", error_msg))
        
        # 在后台线程中执行上传
        thread = threading.Thread(target=upload_task, daemon=True)
        thread.start()

class DownloadButton:
    """下载按钮组件"""
    
    def __init__(self, parent_widget, file_info: dict, chat_manager):
        self.parent = parent_widget
        self.file_info = file_info
        self.chat_manager = chat_manager
        
        # 创建下载按钮框架
        self.frame = ttk.Frame(parent_widget)
        
        # 文件信息
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
        
        # 文件图标
        icon = "🖼️" if file_type == 'image' else "📎"
        
        # 文件信息标签
        info_label = ttk.Label(self.frame, text=f"{icon} {file_name} ({size_str})")
        info_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 下载按钮
        download_btn = ttk.Button(self.frame, text="📥 下载", 
                                 command=self.download_file, width=8)
        download_btn.pack(side=tk.RIGHT)
        
        # 如果是图片，添加预览按钮
        if file_type == 'image':
            preview_btn = ttk.Button(self.frame, text="👁️", 
                                   command=self.preview_file, width=3)
            preview_btn.pack(side=tk.RIGHT, padx=(0, 5))
    
    def download_file(self):
        """下载文件"""
        try:
            # 选择保存位置
            file_name = self.file_info.get('original_name', 'download_file')
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_name,
                defaultextension=Path(file_name).suffix
            )
            
            if save_path:
                # 执行下载
                success = self.chat_manager.download_file(self.file_info, os.path.dirname(save_path))
                
                if success:
                    messagebox.showinfo("下载完成", f"文件已保存到:\n{save_path}")
                else:
                    messagebox.showerror("下载失败", "文件下载失败，请检查文件是否存在")
                    
        except Exception as e:
            messagebox.showerror("下载错误", f"下载文件时发生错误: {str(e)}")
    
    def preview_file(self):
        """预览文件（仅图片）"""
        try:
            if self.file_info.get('file_type') == 'image':
                # 这里可以实现图片预览功能
                messagebox.showinfo("预览", f"预览功能：{self.file_info.get('original_name')}")
            else:
                messagebox.showinfo("提示", "该文件类型不支持预览")
        except Exception as e:
            messagebox.showerror("预览错误", f"预览文件时发生错误: {str(e)}")
    
    def pack(self, **kwargs):
        """打包组件"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self.frame.grid(**kwargs)

def test_file_manager():
    """测试文件管理器"""
    import tempfile
    from network_share_chat import NetworkShareChatManager
    
    print("🧪 测试文件管理器")
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"测试目录: {temp_dir}")
        
        # 创建聊天管理器
        chat_manager = NetworkShareChatManager(temp_dir)
        
        # 创建测试文件
        test_file = Path(temp_dir) / "test_file.txt"
        test_file.write_text("这是一个测试文件", encoding='utf-8')
        
        # 上传测试文件
        file_info = chat_manager.upload_file(str(test_file), "test_user", "测试用户")
        
        if file_info:
            print("✅ 测试文件上传成功")
            
            # 创建GUI测试
            root = tk.Tk()
            root.title("文件管理器测试")
            
            # 创建文件管理窗口
            file_manager = FileManagerWindow(root, chat_manager, "test_user", "测试用户")
            
            print("🎮 GUI测试窗口已打开，请手动测试功能")
            root.mainloop()
        else:
            print("❌ 测试文件上传失败")

if __name__ == "__main__":
    test_file_manager()