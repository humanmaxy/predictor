#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
improved_file_manager.py 错误修复补丁

使用方法:
1. 将此文件中的修复代码应用到您的 improved_file_manager.py 文件中
2. 或者直接替换对应的方法
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import base64
from cryptography.fernet import Fernet


def fixed_download_selected_file(self):
    """
    修复后的文件下载方法
    修复问题：
    1. Tkinter filedialog 参数错误 (initialname -> initialfile)
    2. UTF-8解码错误处理
    """
    try:
        # 获取选中的文件
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
        
        # 获取文件信息
        selected_item = self.file_listbox.get(selection[0])
        # 根据您的实际数据格式调整文件名提取逻辑
        file_name = selected_item.split()[0] if selected_item else "untitled"
        
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
            # 获取文件数据（根据您的实际实现调整）
            file_data = self.get_selected_file_data()
            
            if file_data is None:
                messagebox.showerror("错误", "无法获取文件数据")
                return
            
            # 如果文件是加密的，进行安全解密
            if hasattr(self, 'encryption_key') and self.encryption_key:
                success, processed_data, error_msg = self.safe_decrypt_file_data(file_data)
                if not success:
                    messagebox.showerror("错误", f"解密失败: {error_msg}")
                    return
                file_data = processed_data
            
            # 保存文件
            self.save_file_with_encoding_detection(save_path, file_data)
            
    except Exception as e:
        messagebox.showerror("错误", f"下载文件失败: {str(e)}")


def safe_decrypt_file_data(self, encrypted_data):
    """
    安全解密文件数据，处理UTF-8解码错误
    
    Returns:
        tuple: (success: bool, data: bytes/str, error_msg: str)
    """
    try:
        if not hasattr(self, 'encryption_key') or not self.encryption_key:
            return False, None, "未设置加密密钥"
        
        # 解密数据
        fernet = Fernet(self.encryption_key)
        decrypted_bytes = fernet.decrypt(encrypted_data)
        
        # 尝试检测文件类型
        if self.is_likely_text_file(decrypted_bytes):
            # 尝试多种编码解码文本文件
            return self.decode_text_with_multiple_encodings(decrypted_bytes)
        else:
            # 二进制文件直接返回字节数据
            return True, decrypted_bytes, "二进制文件解密成功"
            
    except Exception as e:
        return False, None, f"解密过程出错: {str(e)}"


def decode_text_with_multiple_encodings(self, data):
    """
    使用多种编码尝试解码文本数据
    """
    # 常见编码列表，按优先级排序
    encodings = [
        'utf-8',           # 首选UTF-8
        'gbk',             # 中文GBK编码
        'gb2312',          # 中文GB2312编码
        'utf-16',          # UTF-16编码
        'latin-1',         # 拉丁编码
        'cp1252',          # Windows编码
        'iso-8859-1'       # ISO编码
    ]
    
    for encoding in encodings:
        try:
            decoded_text = data.decode(encoding)
            return True, decoded_text, f"使用{encoding}编码解码成功"
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，使用UTF-8的错误处理模式
    try:
        # 替换无效字符
        decoded_text = data.decode('utf-8', errors='replace')
        return True, decoded_text, "UTF-8解码成功（已替换无效字符）"
    except Exception:
        try:
            # 忽略无效字符
            decoded_text = data.decode('utf-8', errors='ignore')
            return True, decoded_text, "UTF-8解码成功（已忽略无效字符）"
        except Exception:
            # 最后的备选方案：返回原始字节数据
            return True, data, "无法解码为文本，返回原始字节数据"


def is_likely_text_file(self, data):
    """
    判断数据是否可能是文本文件
    """
    if len(data) == 0:
        return True
    
    # 检查前1000字节中的可打印字符比例
    sample_size = min(1000, len(data))
    sample = data[:sample_size]
    
    # 统计可打印字符
    printable_count = 0
    for byte in sample:
        # ASCII可打印字符范围：32-126，加上常见的控制字符
        if 32 <= byte <= 126 or byte in [9, 10, 13]:  # 制表符、换行符、回车符
            printable_count += 1
    
    # 如果可打印字符比例超过70%，认为是文本文件
    return (printable_count / sample_size) > 0.7


def save_file_with_encoding_detection(self, file_path, data):
    """
    根据数据类型智能保存文件
    """
    try:
        if isinstance(data, str):
            # 文本数据，使用UTF-8编码保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)
        elif isinstance(data, bytes):
            # 二进制数据，直接写入
            with open(file_path, 'wb') as f:
                f.write(data)
        else:
            # 其他类型，转换为字符串后保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        messagebox.showinfo("成功", f"文件已保存到: {file_path}")
        
    except Exception as e:
        messagebox.showerror("错误", f"保存文件失败: {str(e)}")


def on_file_double_click_fixed(self, event=None):
    """
    修复后的文件双击处理方法
    """
    try:
        self.download_selected_file()
    except Exception as e:
        messagebox.showerror("错误", f"处理文件双击事件失败: {str(e)}")


# 通用的文件对话框修复函数
def fixed_asksaveasfilename(**kwargs):
    """
    修复Tkinter文件对话框参数的通用函数
    """
    # 修复常见的参数错误
    if 'initialname' in kwargs:
        kwargs['initialfile'] = kwargs.pop('initialname')
    
    # 确保参数有效
    valid_params = {
        'confirmoverwrite', 'defaultextension', 'filetypes',
        'initialdir', 'initialfile', 'parent', 'title', 'typevariable'
    }
    
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
    
    return filedialog.asksaveasfilename(**filtered_kwargs)


# 使用示例和测试代码
if __name__ == "__main__":
    # 测试UTF-8解码修复
    def test_utf8_decode_fix():
        """测试UTF-8解码修复"""
        # 模拟有问题的字节数据
        problematic_bytes = b'\xcf\x80\x81\xe4\xb8\xad\xe6\x96\x87'
        
        # 使用修复后的解码函数
        class MockSelf:
            pass
        
        mock_self = MockSelf()
        result = decode_text_with_multiple_encodings(mock_self, problematic_bytes)
        print(f"解码测试结果: {result}")
    
    # 测试文件对话框修复
    def test_filedialog_fix():
        """测试文件对话框修复"""
        root = tk.Tk()
        root.withdraw()
        
        try:
            # 使用修复后的函数
            filename = fixed_asksaveasfilename(
                initialname="test.txt",  # 这会被自动修复为initialfile
                title="保存测试文件",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            print(f"选择的文件: {filename}")
        except Exception as e:
            print(f"文件对话框错误: {e}")
        finally:
            root.destroy()
    
    print("开始测试修复...")
    test_utf8_decode_fix()
    # test_filedialog_fix()  # 需要GUI环境才能测试
    print("测试完成")