#!/usr/bin/env python3
"""
测试修复后的下载功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tempfile
import os
from pathlib import Path

def test_filedialog_fix():
    """测试修复的文件对话框"""
    print("🧪 测试修复的文件下载对话框")
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是一个测试文件")
        test_file = f.name
    
    try:
        # 创建GUI测试
        root = tk.Tk()
        root.title("下载功能测试")
        root.geometry("500x300")
        
        frame = ttk.Frame(root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="测试改进的文件下载功能", font=("Arial", 14, "bold")).pack(pady=10)
        
        info_text = f"测试文件: {os.path.basename(test_file)}\n"
        info_text += f"文件路径: {test_file}\n"
        info_text += f"文件大小: {os.path.getsize(test_file)} 字节"
        
        ttk.Label(frame, text=info_text, justify=tk.LEFT).pack(pady=10)
        
        def test_download():
            try:
                from tkinter import filedialog
                
                # 使用修复后的参数
                save_path = filedialog.asksaveasfilename(
                    parent=root,
                    title="保存测试文件",
                    initialfile=os.path.basename(test_file),
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
                )
                
                if save_path:
                    # 复制文件
                    import shutil
                    shutil.copy2(test_file, save_path)
                    
                    if os.path.exists(save_path):
                        messagebox.showinfo("下载成功", f"文件已保存到:\n{save_path}")
                    else:
                        messagebox.showerror("下载失败", "文件保存失败")
                else:
                    messagebox.showinfo("取消", "用户取消了下载")
                    
            except Exception as e:
                messagebox.showerror("错误", f"下载测试失败: {str(e)}")
        
        ttk.Button(frame, text="📥 测试下载功能", command=test_download).pack(pady=20)
        
        ttk.Label(frame, text="测试说明:\n1. 点击按钮打开保存对话框\n2. 选择保存位置\n3. 确认文件下载成功", 
                 justify=tk.LEFT).pack(pady=10)
        
        print("🎮 GUI测试窗口已打开，请点击按钮测试下载功能")
        root.mainloop()
        
    finally:
        # 清理测试文件
        try:
            os.unlink(test_file)
            print("🧹 已清理测试文件")
        except:
            pass

if __name__ == "__main__":
    test_filedialog_fix()