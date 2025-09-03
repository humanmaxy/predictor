#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理器错误修复示例
解决UTF-8解码错误和Tkinter文件对话框错误
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import base64
from cryptography.fernet import Fernet
import os

class FileManagerFixes:
    """文件管理器错误修复类"""
    
    def __init__(self):
        self.encryption_key = None
        
    def safe_decrypt_file(self, encrypted_data, key):
        """
        安全解密文件数据，处理UTF-8解码错误
        
        Args:
            encrypted_data: 加密的数据
            key: 解密密钥
            
        Returns:
            tuple: (success: bool, data: bytes or str, error_msg: str)
        """
        try:
            # 创建Fernet实例
            fernet = Fernet(key)
            
            # 解密数据
            decrypted_bytes = fernet.decrypt(encrypted_data)
            
            # 尝试多种编码方式解码
            encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
            
            for encoding in encodings_to_try:
                try:
                    decoded_text = decrypted_bytes.decode(encoding)
                    return True, decoded_text, f"成功使用{encoding}编码解码"
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，返回原始字节数据
            return True, decrypted_bytes, "无法解码为文本，返回原始字节数据"
            
        except Exception as e:
            return False, None, f"解密失败: {str(e)}"
    
    def safe_decrypt_with_error_handling(self, encrypted_data, key):
        """
        带错误处理的安全解密方法
        """
        try:
            fernet = Fernet(key)
            decrypted_bytes = fernet.decrypt(encrypted_data)
            
            # 方法1: 使用errors='replace'参数
            try:
                decoded_text = decrypted_bytes.decode('utf-8', errors='replace')
                return True, decoded_text, "UTF-8解码成功（替换无效字符）"
            except Exception:
                pass
            
            # 方法2: 使用errors='ignore'参数
            try:
                decoded_text = decrypted_bytes.decode('utf-8', errors='ignore')
                return True, decoded_text, "UTF-8解码成功（忽略无效字符）"
            except Exception:
                pass
            
            # 方法3: 返回base64编码的字符串
            try:
                b64_text = base64.b64encode(decrypted_bytes).decode('ascii')
                return True, b64_text, "返回Base64编码的数据"
            except Exception:
                pass
            
            # 最后的备选方案：返回十六进制字符串
            hex_text = decrypted_bytes.hex()
            return True, hex_text, "返回十六进制编码的数据"
            
        except Exception as e:
            return False, None, f"解密失败: {str(e)}"
    
    def download_selected_file_fixed(self, file_name, file_data):
        """
        修复后的文件下载方法
        
        Args:
            file_name: 文件名
            file_data: 文件数据（可能是加密的）
        """
        try:
            # 修复Tkinter文件对话框参数错误
            # 错误的写法: initialname=file_name
            # 正确的写法: initialfile=file_name
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_name,  # 修复：使用initialfile而不是initialname
                defaultextension="",
                filetypes=[
                    ("所有文件", "*.*"),
                    ("文本文件", "*.txt"),
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("文档文件", "*.pdf;*.doc;*.docx")
                ]
            )
            
            if save_path:
                # 如果数据是加密的，先解密
                if self.encryption_key:
                    success, decrypted_data, msg = self.safe_decrypt_file(file_data, self.encryption_key)
                    if not success:
                        messagebox.showerror("错误", f"解密失败: {msg}")
                        return False
                    
                    # 保存解密后的数据
                    if isinstance(decrypted_data, str):
                        # 文本数据
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(decrypted_data)
                    else:
                        # 二进制数据
                        with open(save_path, 'wb') as f:
                            f.write(decrypted_data)
                else:
                    # 直接保存未加密的数据
                    if isinstance(file_data, str):
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(file_data)
                    else:
                        with open(save_path, 'wb') as f:
                            f.write(file_data)
                
                messagebox.showinfo("成功", f"文件已保存到: {save_path}")
                return True
                
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")
            return False
    
    def on_file_double_click_fixed(self, event=None):
        """
        修复后的文件双击处理方法
        """
        try:
            # 获取选中的文件信息
            selection = self.file_listbox.curselection()
            if not selection:
                return
            
            file_info = self.file_listbox.get(selection[0])
            file_name = file_info.split()[0]  # 假设文件名是第一个部分
            
            # 获取文件数据（这里需要根据实际的数据获取逻辑调整）
            file_data = self.get_file_data(file_name)
            
            # 调用修复后的下载方法
            self.download_selected_file_fixed(file_name, file_data)
            
        except Exception as e:
            messagebox.showerror("错误", f"处理文件失败: {str(e)}")
    
    def get_file_data(self, file_name):
        """
        获取文件数据的示例方法
        需要根据实际的数据存储方式实现
        """
        # 这里需要根据实际情况实现文件数据获取逻辑
        pass

# 通用的UTF-8解码错误处理函数
def safe_decode_bytes(data, default_encoding='utf-8'):
    """
    安全解码字节数据，处理编码错误
    
    Args:
        data: 要解码的字节数据
        default_encoding: 默认编码
        
    Returns:
        str: 解码后的字符串
    """
    if isinstance(data, str):
        return data
    
    if not isinstance(data, bytes):
        return str(data)
    
    # 尝试不同的编码
    encodings = [default_encoding, 'gbk', 'gb2312', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，使用errors='replace'
    return data.decode(default_encoding, errors='replace')

# 修复Tkinter文件对话框的通用函数
def fixed_asksaveasfilename(initial_filename=None, **kwargs):
    """
    修复后的文件保存对话框
    
    Args:
        initial_filename: 初始文件名
        **kwargs: 其他参数
        
    Returns:
        str: 选择的文件路径
    """
    # 修复参数名称
    dialog_kwargs = kwargs.copy()
    
    # 如果传入了initialname，改为initialfile
    if 'initialname' in dialog_kwargs:
        dialog_kwargs['initialfile'] = dialog_kwargs.pop('initialname')
    
    # 如果传入了initial_filename，设置为initialfile
    if initial_filename:
        dialog_kwargs['initialfile'] = initial_filename
    
    return filedialog.asksaveasfilename(**dialog_kwargs)

if __name__ == "__main__":
    # 测试UTF-8解码修复
    test_bytes = b'\xcf\x80\x81'  # 无效的UTF-8字节序列
    result = safe_decode_bytes(test_bytes)
    print(f"解码结果: {repr(result)}")
    
    # 测试文件对话框修复
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    try:
        # 这会成功，因为使用了正确的参数名
        filename = fixed_asksaveasfilename(
            initial_filename="test.txt",
            title="保存文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        print(f"选择的文件: {filename}")
    except Exception as e:
        print(f"文件对话框错误: {e}")
    
    root.destroy()