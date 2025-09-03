#!/usr/bin/env python3
"""
简单稳定的文件下载组件
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import shutil
import threading

class SimpleFileDownloader:
    """简单文件下载器"""
    
    @staticmethod
    def download_file_simple(source_path: str, original_name: str, parent_window=None):
        """简单的文件下载方法"""
        try:
            source = Path(source_path)
            if not source.exists():
                messagebox.showerror("错误", f"源文件不存在:\n{source_path}")
                return False
            
            # 选择保存位置 - 使用更兼容的参数
            save_path = filedialog.asksaveasfilename(
                parent=parent_window,
                title="保存文件",
                initialfile=original_name,
                filetypes=[("所有文件", "*.*")]
            )
            
            if not save_path:
                return False  # 用户取消
            
            # 在后台线程中执行下载
            def download_task():
                try:
                    target = Path(save_path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(source, target)
                    
                    # 验证下载
                    if target.exists() and target.stat().st_size > 0:
                        if parent_window:
                            parent_window.after(0, lambda: messagebox.showinfo(
                                "下载完成", f"文件已保存到:\n{target}"
                            ))
                        else:
                            print(f"下载完成: {target}")
                        return True
                    else:
                        raise Exception("下载的文件为空")
                        
                except Exception as e:
                    error_msg = f"下载失败: {str(e)}"
                    if parent_window:
                        parent_window.after(0, lambda: messagebox.showerror("下载失败", error_msg))
                    else:
                        print(error_msg)
                    return False
            
            # 启动下载线程
            thread = threading.Thread(target=download_task, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            messagebox.showerror("下载错误", f"下载操作失败: {str(e)}")
            return False

class FileMessageWidget:
    """文件消息组件"""
    
    def __init__(self, parent_frame, file_info: dict, chat_manager, message_widget):
        self.parent_frame = parent_frame
        self.file_info = file_info
        self.chat_manager = chat_manager
        self.message_widget = message_widget
        
        # 创建文件消息框架
        self.create_file_message()
    
    def create_file_message(self):
        """创建文件消息界面"""
        # 文件信息
        file_name = self.file_info.get('original_name', '未知文件')
        file_size = self.file_info.get('file_size', 0)
        file_type = self.file_info.get('file_type', 'file')
        
        # 格式化文件大小
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # 文件图标
        icon = "🖼️" if file_type == 'image' else "📎"
        
        # 在消息框中插入文件信息
        self.message_widget.config(state=tk.NORMAL)
        
        # 插入文件信息行
        file_info_text = f"    {icon} {file_name} ({size_str})\n"
        self.message_widget.insert(tk.END, file_info_text)
        
        # 插入下载提示
        download_text = f"    📥 点击下载: "
        self.message_widget.insert(tk.END, download_text)
        
        # 创建下载链接（使用tag）
        start_index = self.message_widget.index(tk.END + "-1c")
        download_link_text = f"[下载 {file_name}]"
        self.message_widget.insert(tk.END, download_link_text)
        end_index = self.message_widget.index(tk.END + "-1c")
        
        # 为下载链接添加tag
        tag_name = f"download_{id(self.file_info)}"
        self.message_widget.tag_add(tag_name, start_index, end_index)
        self.message_widget.tag_config(tag_name, foreground="blue", underline=True)
        
        # 绑定点击事件
        self.message_widget.tag_bind(tag_name, "<Button-1>", lambda e: self.download_file())
        self.message_widget.tag_bind(tag_name, "<Enter>", lambda e: self.message_widget.config(cursor="hand2"))
        self.message_widget.tag_bind(tag_name, "<Leave>", lambda e: self.message_widget.config(cursor=""))
        
        self.message_widget.insert(tk.END, "\n")
        self.message_widget.config(state=tk.DISABLED)
        self.message_widget.see(tk.END)
    
    def download_file(self):
        """下载文件"""
        try:
            # 构建源文件路径
            if 'relative_path' in self.file_info:
                source_path = self.chat_manager.share_path / self.file_info['relative_path']
            else:
                # 根据文件类型和文件名构建路径
                file_type = self.file_info.get('file_type', 'file')
                filename = self.file_info.get('filename', self.file_info.get('original_name', ''))
                
                if file_type == 'image':
                    source_path = self.chat_manager.file_manager.images_dir / filename
                else:
                    source_path = self.chat_manager.file_manager.files_dir / filename
            
            # 使用简单下载器下载
            SimpleFileDownloader.download_file_simple(
                str(source_path), 
                self.file_info.get('original_name', 'download_file'),
                self.parent_frame.winfo_toplevel()
            )
            
        except Exception as e:
            messagebox.showerror("下载错误", f"下载文件时发生错误: {str(e)}")

def create_download_button_in_text(text_widget, file_info: dict, chat_manager):
    """在文本框中创建下载按钮"""
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
        link_text = f"[点击下载]"
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
                SimpleFileDownloader.download_file_simple(
                    str(source_path), 
                    file_info.get('original_name', 'download_file'),
                    text_widget.winfo_toplevel()
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

def test_simple_downloader():
    """测试简单下载器"""
    import tempfile
    
    print("🧪 测试简单文件下载器")
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是一个测试文件\n用于测试下载功能")
        test_file_path = f.name
    
    try:
        print(f"创建测试文件: {test_file_path}")
        
        # 创建简单的GUI测试
        root = tk.Tk()
        root.title("下载测试")
        root.geometry("400x200")
        
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="点击下面的按钮测试下载功能:").pack(pady=10)
        
        def test_download():
            SimpleFileDownloader.download_file_simple(
                test_file_path,
                "测试文件.txt",
                root
            )
        
        ttk.Button(frame, text="📥 测试下载", command=test_download).pack(pady=10)
        
        ttk.Label(frame, text="测试完成后请关闭窗口").pack(pady=10)
        
        print("🎮 GUI测试窗口已打开")
        root.mainloop()
        
    finally:
        # 清理测试文件
        try:
            os.unlink(test_file_path)
            print("🧹 已清理测试文件")
        except:
            pass

if __name__ == "__main__":
    test_simple_downloader()