#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的文件管理器 - 修复版本
移除了加密处理，解决UTF-8解码错误和Tkinter参数错误
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import json
import base64
from datetime import datetime
import threading


class ImprovedFileManager:
    def __init__(self, parent=None):
        if parent:
            self.root = parent
            self.is_standalone = False
        else:
            self.root = tk.Tk()
            self.root.title("改进的文件管理器")
            self.root.geometry("800x600")
            self.is_standalone = True
        
        # 文件存储 - 移除加密相关
        self.shared_files = {}  # {filename: {'content': data, 'type': 'text'|'binary', 'size': int}}
        self.current_folder = os.getcwd()
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        if self.is_standalone:
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
        else:
            main_frame = self.root
            
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 文件操作按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(btn_frame, text="上传文件", command=self.upload_file).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(btn_frame, text="下载文件", command=self.download_selected_file).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(btn_frame, text="删除文件", command=self.delete_selected_file).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(btn_frame, text="刷新列表", command=self.refresh_file_list).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(btn_frame, text="清空列表", command=self.clear_file_list).grid(row=0, column=4)
        
        # 文件列表区域
        list_frame = ttk.LabelFrame(main_frame, text="共享文件列表", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建文件列表框和滚动条
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.file_listbox.bind('<Double-Button-1>', self.on_file_double_click)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        ttk.Label(status_frame, text="状态:").grid(row=0, column=0)
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=1, padx=(5, 0))
        
    def upload_file(self):
        """上传文件 - 无加密版本"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择要上传的文件",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文本文件", "*.txt"),
                    ("Python文件", "*.py"),
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("文档文件", "*.pdf;*.doc;*.docx"),
                    ("压缩文件", "*.zip;*.rar;*.7z")
                ]
            )
            
            if not file_path:
                return
                
            file_name = os.path.basename(file_path)
            
            # 检查文件是否已存在
            if file_name in self.shared_files:
                if not messagebox.askyesno("确认", f"文件 '{file_name}' 已存在，是否覆盖？"):
                    return
            
            self.status_var.set(f"正在上传 {file_name}...")
            
            # 读取文件内容 - 无加密处理
            file_data = self.read_file_safely(file_path)
            if file_data:
                self.shared_files[file_name] = file_data
                self.refresh_file_list()
                
                size_mb = file_data['size'] / (1024 * 1024)
                if size_mb >= 1:
                    size_text = f"{size_mb:.2f} MB"
                else:
                    size_text = f"{file_data['size']} 字节"
                    
                self.status_var.set(f"上传完成: {file_name} ({size_text})")
                messagebox.showinfo("成功", f"文件 '{file_name}' 上传成功")
            else:
                self.status_var.set("上传失败")
                
        except Exception as e:
            self.status_var.set("上传失败")
            messagebox.showerror("错误", f"上传文件失败: {str(e)}")
            
    def read_file_safely(self, file_path):
        """安全读取文件，自动检测文本/二进制"""
        try:
            file_size = os.path.getsize(file_path)
            
            # 检查文件大小限制（例如50MB）
            max_size = 50 * 1024 * 1024
            if file_size > max_size:
                messagebox.showerror("错误", f"文件太大，最大支持 {max_size // (1024*1024)} MB")
                return None
            
            # 尝试判断文件类型
            try:
                # 先尝试文本模式读取前1000字节来判断
                with open(file_path, 'rb') as f:
                    sample = f.read(1000)
                
                # 简单的文本文件检测
                is_text = self.is_likely_text_file(sample)
                
                if is_text:
                    # 尝试多种编码读取文本文件
                    content = self.read_text_file_with_encoding_detection(file_path)
                    if content is not None:
                        return {
                            'name': os.path.basename(file_path),
                            'content': content,
                            'type': 'text',
                            'size': len(content.encode('utf-8')),
                            'original_size': file_size
                        }
                
                # 二进制文件处理
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                return {
                    'name': os.path.basename(file_path),
                    'content': base64.b64encode(content).decode('ascii'),
                    'type': 'binary',
                    'size': file_size,
                    'original_size': file_size
                }
                
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {str(e)}")
                return None
                
        except Exception as e:
            messagebox.showerror("错误", f"处理文件失败: {str(e)}")
            return None
            
    def is_likely_text_file(self, data):
        """判断是否可能是文本文件"""
        if len(data) == 0:
            return True
            
        # 检查是否包含null字节（二进制文件的特征）
        if b'\x00' in data:
            return False
            
        # 统计可打印字符比例
        printable_count = 0
        for byte in data:
            if 32 <= byte <= 126 or byte in [9, 10, 13]:  # 可打印字符 + 制表符、换行符、回车符
                printable_count += 1
                
        # 如果可打印字符比例超过80%，认为是文本文件
        return (printable_count / len(data)) > 0.8
        
    def read_text_file_with_encoding_detection(self, file_path):
        """使用编码检测读取文本文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                break
                
        # 如果所有编码都失败，使用UTF-8的错误处理模式
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception:
            return None
            
    def download_selected_file(self):
        """下载选中的文件 - 修复版本，无加密处理"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个文件")
                return
                
            # 获取选中的文件信息
            selected_item = self.file_listbox.get(selection[0])
            # 解析文件名（格式：filename (size) [type]）
            file_name = selected_item.split(' (')[0] if ' (' in selected_item else selected_item
            
            if file_name not in self.shared_files:
                messagebox.showerror("错误", "文件不存在")
                return
                
            # 修复：使用正确的参数名 initialfile 而不是 initialname
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_name,  # ✅ 修复：正确的参数名
                defaultextension="",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文本文件", "*.txt"),
                    ("Python文件", "*.py"),
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("文档文件", "*.pdf;*.doc;*.docx"),
                    ("压缩文件", "*.zip;*.rar;*.7z")
                ]
            )
            
            if save_path:
                self.status_var.set(f"正在下载 {file_name}...")
                
                # 保存文件 - 无解密处理
                success = self.save_file_without_encryption(save_path, file_name)
                
                if success:
                    self.status_var.set(f"下载完成: {file_name}")
                    messagebox.showinfo("成功", f"文件已保存到: {save_path}")
                else:
                    self.status_var.set("下载失败")
                    
        except Exception as e:
            self.status_var.set("下载失败")
            messagebox.showerror("错误", f"下载文件失败: {str(e)}")
            
    def save_file_without_encryption(self, save_path, file_name):
        """保存文件，无加密处理"""
        try:
            file_data = self.shared_files[file_name]
            
            if file_data['type'] == 'text':
                # 文本文件，直接保存
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(file_data['content'])
            else:
                # 二进制文件，从base64解码后保存
                try:
                    content = base64.b64decode(file_data['content'])
                    with open(save_path, 'wb') as f:
                        f.write(content)
                except Exception as e:
                    messagebox.showerror("错误", f"解码二进制文件失败: {str(e)}")
                    return False
                    
            return True
            
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")
            return False
            
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
                if messagebox.askyesno("确认", f"确定要删除文件 '{file_name}' 吗？"):
                    del self.shared_files[file_name]
                    self.refresh_file_list()
                    self.status_var.set(f"已删除: {file_name}")
                    messagebox.showinfo("成功", f"文件 '{file_name}' 已删除")
            else:
                messagebox.showerror("错误", "文件不存在")
                
        except Exception as e:
            messagebox.showerror("错误", f"删除文件失败: {str(e)}")
            
    def refresh_file_list(self):
        """刷新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        
        if not self.shared_files:
            self.file_listbox.insert(tk.END, "暂无文件")
            return
            
        for file_name, file_data in self.shared_files.items():
            size = file_data.get('size', 0)
            file_type = file_data.get('type', 'unknown')
            
            # 格式化文件大小
            if size >= 1024 * 1024:
                size_text = f"{size / (1024 * 1024):.2f} MB"
            elif size >= 1024:
                size_text = f"{size / 1024:.2f} KB"
            else:
                size_text = f"{size} 字节"
                
            display_text = f"{file_name} ({size_text}) [{file_type}]"
            self.file_listbox.insert(tk.END, display_text)
            
    def clear_file_list(self):
        """清空文件列表"""
        if self.shared_files and messagebox.askyesno("确认", "确定要清空所有文件吗？"):
            self.shared_files.clear()
            self.refresh_file_list()
            self.status_var.set("文件列表已清空")
            
    def get_file_list_info(self):
        """获取文件列表信息"""
        total_files = len(self.shared_files)
        total_size = sum(file_data.get('size', 0) for file_data in self.shared_files.values())
        
        if total_size >= 1024 * 1024:
            size_text = f"{total_size / (1024 * 1024):.2f} MB"
        elif total_size >= 1024:
            size_text = f"{total_size / 1024:.2f} KB"
        else:
            size_text = f"{total_size} 字节"
            
        return f"共 {total_files} 个文件，总大小 {size_text}"
        
    def export_file_list(self):
        """导出文件列表"""
        try:
            if not self.shared_files:
                messagebox.showwarning("警告", "没有文件可导出")
                return
                
            save_path = filedialog.asksaveasfilename(
                title="导出文件列表",
                initialfile="file_list.json",  # ✅ 使用正确的参数名
                defaultextension=".json",
                filetypes=[
                    ("JSON文件", "*.json"),
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ]
            )
            
            if save_path:
                # 创建文件列表信息（不包含实际内容）
                file_list_info = []
                for file_name, file_data in self.shared_files.items():
                    file_list_info.append({
                        'name': file_name,
                        'type': file_data.get('type', 'unknown'),
                        'size': file_data.get('size', 0),
                        'upload_time': datetime.now().isoformat()
                    })
                
                if save_path.endswith('.json'):
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(file_list_info, f, ensure_ascii=False, indent=2)
                else:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write("文件列表\n")
                        f.write("=" * 50 + "\n")
                        for info in file_list_info:
                            f.write(f"文件名: {info['name']}\n")
                            f.write(f"类型: {info['type']}\n")
                            f.write(f"大小: {info['size']} 字节\n")
                            f.write("-" * 30 + "\n")
                
                messagebox.showinfo("成功", f"文件列表已导出到: {save_path}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出文件列表失败: {str(e)}")
            
    def run(self):
        """运行文件管理器"""
        if self.is_standalone:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
            
    def on_closing(self):
        """关闭时的清理工作"""
        if self.is_standalone:
            self.root.destroy()


# 为了兼容原有的调用方式，保持原来的方法名
class ImprovedFileManagerLegacy(ImprovedFileManager):
    """兼容旧版本调用的文件管理器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除加密相关属性
        self.encryption_key = None  # 保持兼容性，但不使用
        
    def get_selected_file_data(self):
        """获取选中文件的数据 - 兼容方法"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                return None
                
            selected_item = self.file_listbox.get(selection[0])
            file_name = selected_item.split(' (')[0] if ' (' in selected_item else selected_item
            
            return self.shared_files.get(file_name)
            
        except Exception:
            return None
            
    def get_file_content(self, file_name):
        """获取文件内容 - 兼容方法"""
        return self.shared_files.get(file_name, {}).get('content', '')
        
    def is_encrypted_file(self, file_name):
        """检查文件是否加密 - 兼容方法，始终返回False"""
        return False


if __name__ == "__main__":
    print("启动改进的文件管理器...")
    
    # 创建测试数据
    app = ImprovedFileManager()
    
    # 添加一些示例文件
    app.shared_files["test.txt"] = {
        'name': 'test.txt',
        'content': '这是一个测试文件\n包含中文内容',
        'type': 'text',
        'size': 42
    }
    
    app.shared_files["example.py"] = {
        'name': 'example.py',
        'content': '# Python示例文件\nprint("Hello, World!")\n',
        'type': 'text',
        'size': 45
    }
    
    app.refresh_file_list()
    app.status_var.set(app.get_file_list_info())
    
    print("文件管理器已启动，测试数据已加载")
    app.run()