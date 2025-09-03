#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修复补丁 - 应用到您的 improved_file_manager.py 文件

这个补丁解决两个问题：
1. UTF-8解码错误 - 移除加密处理
2. Tkinter文件对话框参数错误 - initialname -> initialfile

使用方法：
1. 找到您的 improved_file_manager.py 文件中的问题代码
2. 用下面的修复代码替换对应部分
"""

# ========================================
# 修复1: download_selected_file 方法
# ========================================

def download_selected_file(self):
    """
    修复后的文件下载方法
    - 移除了加密/解密处理
    - 修复了filedialog参数错误
    """
    try:
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
            
        # 获取选中的文件信息
        selected_item = self.file_listbox.get(selection[0])
        # 根据您的文件列表格式调整文件名提取逻辑
        file_name = selected_item.split(' (')[0] if ' (' in selected_item else selected_item.split()[0]
        
        # 修复：使用 initialfile 而不是 initialname
        save_path = filedialog.asksaveasfilename(
            title="保存文件",
            initialfile=file_name,  # ✅ 修复：正确的参数名
            defaultextension="",
            filetypes=[
                ("所有文件", "*.*"),
                ("文本文件", "*.txt"),
                ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("文档文件", "*.pdf;*.doc;*.docx"),
                ("压缩文件", "*.zip;*.rar;*.7z")
            ]
        )
        
        if save_path:
            # 获取文件数据 - 无解密处理
            file_data = self.get_file_content_without_decryption(file_name)
            
            if file_data is not None:
                # 直接保存文件，无需解密
                self.save_file_directly(save_path, file_data, file_name)
            else:
                messagebox.showerror("错误", "无法获取文件数据")
                
    except Exception as e:
        messagebox.showerror("错误", f"下载文件失败: {str(e)}")


# ========================================
# 修复2: 文件内容获取方法（无解密）
# ========================================

def get_file_content_without_decryption(self, file_name):
    """
    获取文件内容，无解密处理
    替换原来的解密逻辑
    """
    try:
        # 如果您的文件存储在字典中
        if hasattr(self, 'shared_files') and file_name in self.shared_files:
            return self.shared_files[file_name]
        
        # 如果您的文件存储在其他地方，请根据实际情况调整
        # 例如：从服务器获取、从数据库读取等
        
        return None
        
    except Exception as e:
        print(f"获取文件内容失败: {e}")
        return None


# ========================================
# 修复3: 直接保存文件方法
# ========================================

def save_file_directly(self, save_path, file_data, file_name):
    """
    直接保存文件，无解密处理
    """
    try:
        if isinstance(file_data, dict):
            # 如果file_data是字典格式
            content = file_data.get('content', '')
            file_type = file_data.get('type', 'text')
            
            if file_type == 'text' or isinstance(content, str):
                # 文本文件
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # 二进制文件（base64编码）
                import base64
                binary_content = base64.b64decode(content)
                with open(save_path, 'wb') as f:
                    f.write(binary_content)
        
        elif isinstance(file_data, str):
            # 直接是字符串内容
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(file_data)
                
        elif isinstance(file_data, bytes):
            # 直接是字节内容
            with open(save_path, 'wb') as f:
                f.write(file_data)
        
        else:
            # 其他类型，转换为字符串
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(str(file_data))
        
        messagebox.showinfo("成功", f"文件已保存到: {save_path}")
        
    except Exception as e:
        messagebox.showerror("错误", f"保存文件失败: {str(e)}")


# ========================================
# 修复4: 文件双击事件处理
# ========================================

def on_file_double_click(self, event=None):
    """
    修复后的文件双击处理
    简化错误处理
    """
    try:
        self.download_selected_file()
    except Exception as e:
        messagebox.showerror("错误", f"处理文件双击事件失败: {str(e)}")


# ========================================
# 完整的替换代码块
# ========================================

COMPLETE_REPLACEMENT_CODE = '''
    def download_selected_file(self):
        """下载选中的文件 - 修复版本，无加密处理"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个文件")
                return
                
            selected_item = self.file_listbox.get(selection[0])
            file_name = selected_item.split(' (')[0] if ' (' in selected_item else selected_item.split()[0]
            
            # 修复：使用 initialfile 而不是 initialname
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_name,  # ✅ 修复：正确的参数名
                defaultextension="",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文本文件", "*.txt"),
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("文档文件", "*.pdf;*.doc;*.docx")
                ]
            )
            
            if save_path:
                # 获取文件数据 - 移除解密处理
                file_data = self.get_file_content_no_decrypt(file_name)
                
                if file_data is not None:
                    # 直接保存，无需解密
                    if isinstance(file_data, dict):
                        content = file_data.get('content', '')
                        if file_data.get('type') == 'binary':
                            import base64
                            content = base64.b64decode(content)
                            with open(save_path, 'wb') as f:
                                f.write(content)
                        else:
                            with open(save_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                    elif isinstance(file_data, str):
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(file_data)
                    else:
                        with open(save_path, 'wb') as f:
                            f.write(file_data)
                    
                    messagebox.showinfo("成功", f"文件已保存到: {save_path}")
                else:
                    messagebox.showerror("错误", "无法获取文件数据")
                    
        except Exception as e:
            messagebox.showerror("错误", f"下载文件失败: {str(e)}")

    def get_file_content_no_decrypt(self, file_name):
        """获取文件内容，无解密处理"""
        try:
            # 根据您的实际数据存储方式调整
            if hasattr(self, 'shared_files') and file_name in self.shared_files:
                return self.shared_files[file_name]
            elif hasattr(self, 'files') and file_name in self.files:
                return self.files[file_name]
            else:
                # 如果是从网络获取，请在这里添加网络请求代码
                return None
        except Exception as e:
            print(f"获取文件内容失败: {e}")
            return None

    def on_file_double_click(self, event=None):
        """文件双击处理 - 简化版本"""
        try:
            self.download_selected_file()
        except Exception as e:
            messagebox.showerror("错误", f"处理文件双击事件失败: {str(e)}")
'''

print("=" * 60)
print("直接修复补丁")
print("=" * 60)
print()
print("应用方法：")
print("1. 在您的 improved_file_manager.py 文件中找到第261行附近的 download_selected_file 方法")
print("2. 将整个方法替换为上面的 COMPLETE_REPLACEMENT_CODE 中的代码")
print()
print("关键修复点：")
print("✅ initialname -> initialfile (第261行附近)")
print("✅ 移除所有加密/解密相关代码")
print("✅ 添加了安全的文件读取和保存逻辑")
print("✅ 改进了错误处理")
print()
print("修复后将解决：")
print("- UTF-8解码错误（因为移除了解密）")
print("- Tkinter文件对话框参数错误")
print("- 文件下载功能正常工作")
print("=" * 60)