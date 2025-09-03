#!/usr/bin/env python3
"""
自动下载管理器
提供更简单的文件下载方式
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import shutil
import threading

class AutoDownloadManager:
    """自动下载管理器"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.download_dir = str(Path.home() / "Downloads" / "ChatFiles")  # 默认下载目录
        self.auto_download = False  # 是否自动下载
        
        # 确保下载目录存在
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
    
    def set_download_directory(self):
        """设置下载目录"""
        new_dir = filedialog.askdirectory(
            title="选择文件下载目录",
            initialdir=self.download_dir
        )
        
        if new_dir:
            self.download_dir = new_dir
            Path(self.download_dir).mkdir(parents=True, exist_ok=True)
            messagebox.showinfo("设置成功", f"下载目录已设置为:\n{self.download_dir}")
            return True
        return False
    
    def download_file(self, source_path: str, original_name: str, show_dialog: bool = True):
        """下载文件到指定目录"""
        try:
            source = Path(source_path)
            if not source.exists():
                if show_dialog:
                    messagebox.showerror("错误", f"源文件不存在:\n{source_path}")
                return False
            
            # 构建目标路径
            target_path = Path(self.download_dir) / original_name
            
            # 如果文件已存在，添加序号
            counter = 1
            original_target = target_path
            while target_path.exists():
                stem = original_target.stem
                suffix = original_target.suffix
                target_path = original_target.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # 在后台线程中下载
            def download_task():
                try:
                    # 复制文件
                    shutil.copy2(source, target_path)
                    
                    # 验证下载
                    if target_path.exists() and target_path.stat().st_size > 0:
                        success_msg = f"文件下载成功!\n保存位置: {target_path}"
                        if show_dialog:
                            self.parent_window.after(0, lambda: messagebox.showinfo("下载完成", success_msg))
                        print(f"下载成功: {target_path}")
                        return True
                    else:
                        raise Exception("下载的文件为空")
                        
                except Exception as e:
                    error_msg = f"下载失败: {str(e)}"
                    if show_dialog:
                        self.parent_window.after(0, lambda: messagebox.showerror("下载失败", error_msg))
                    print(error_msg)
                    return False
            
            # 启动下载线程
            thread = threading.Thread(target=download_task, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            if show_dialog:
                messagebox.showerror("下载错误", f"下载操作失败: {str(e)}")
            return False

def create_simple_download_button(text_widget, file_info: dict, chat_manager, download_manager):
    """在文本框中创建简单的下载按钮"""
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
        
        # 文件图标
        icon = "🖼️" if file_type == 'image' else "📎"
        
        # 启用文本框编辑
        text_widget.config(state=tk.NORMAL)
        
        # 插入文件信息
        file_info_text = f"    {icon} {file_name} ({size_str})\n"
        text_widget.insert(tk.END, file_info_text)
        
        # 插入下载链接
        download_text = f"    📥 "
        text_widget.insert(tk.END, download_text)
        
        # 创建可点击的下载链接
        start_index = text_widget.index(tk.END + "-1c")
        link_text = f"[点击下载到 {os.path.basename(download_manager.download_dir)}]"
        text_widget.insert(tk.END, link_text)
        end_index = text_widget.index(tk.END + "-1c")
        
        # 为链接添加样式和事件
        tag_name = f"download_{id(file_info)}"
        text_widget.tag_add(tag_name, start_index, end_index)
        text_widget.tag_config(tag_name, foreground="blue", underline=True)
        
        # 绑定下载事件
        def download_file(event=None):
            try:
                # 构建源文件路径
                if 'relative_path' in file_info:
                    source_path = chat_manager.share_path / file_info['relative_path']
                else:
                    # 根据文件类型构建路径
                    filename = file_info.get('filename', file_info.get('original_name', ''))
                    if file_type == 'image':
                        source_path = chat_manager.file_manager.images_dir / filename
                    else:
                        source_path = chat_manager.file_manager.files_dir / filename
                
                # 下载文件
                download_manager.download_file(
                    str(source_path), 
                    file_info.get('original_name', 'download_file'),
                    show_dialog=True
                )
                
            except Exception as e:
                messagebox.showerror("下载错误", f"下载失败: {str(e)}")
        
        text_widget.tag_bind(tag_name, "<Button-1>", download_file)
        text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
        text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))
        
        text_widget.insert(tk.END, "\n")
        text_widget.config(state=tk.DISABLED)
        text_widget.see(tk.END)
        
    except Exception as e:
        print(f"创建下载按钮失败: {e}")

def test_auto_download():
    """测试自动下载管理器"""
    import tempfile
    
    print("🧪 测试自动下载管理器")
    
    root = tk.Tk()
    root.title("自动下载测试")
    root.geometry("600x400")
    
    # 创建下载管理器
    download_manager = AutoDownloadManager(root)
    
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="自动下载管理器测试", font=("Arial", 14, "bold")).pack(pady=10)
    
    # 显示当前下载目录
    dir_var = tk.StringVar(value=f"当前下载目录: {download_manager.download_dir}")
    dir_label = ttk.Label(frame, textvariable=dir_var, wraplength=500)
    dir_label.pack(pady=10)
    
    def set_dir():
        if download_manager.set_download_directory():
            dir_var.set(f"当前下载目录: {download_manager.download_dir}")
    
    ttk.Button(frame, text="📁 设置下载目录", command=set_dir).pack(pady=5)
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是一个测试文件\n用于测试自动下载功能")
        test_file_path = f.name
    
    def test_download():
        download_manager.download_file(test_file_path, "测试文件.txt", show_dialog=True)
    
    ttk.Button(frame, text="📥 测试下载", command=test_download).pack(pady=5)
    
    ttk.Label(frame, text="测试完成后请关闭窗口", font=("Arial", 10)).pack(pady=20)
    
    def cleanup():
        try:
            os.unlink(test_file_path)
        except:
            pass
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", cleanup)
    
    print("🎮 GUI测试窗口已打开")
    root.mainloop()

if __name__ == "__main__":
    test_auto_download()