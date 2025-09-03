#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件管理器错误修复的脚本
"""

import sys
import os

def test_utf8_decode_fix():
    """测试UTF-8解码修复"""
    print("=" * 50)
    print("测试UTF-8解码错误修复")
    print("=" * 50)
    
    # 模拟有问题的字节数据
    test_cases = [
        b'\xcf\x80\x81',  # 原始错误中的字节
        b'\xcf\x80\x81\xe4\xb8\xad\xe6\x96\x87',  # 混合字节
        b'\xff\xfe\x4d\x00\x69\x00\x63\x00\x72\x00\x6f\x00\x73\x00\x6f\x00\x66\x00\x74\x00',  # UTF-16 BOM
        "正常的UTF-8文本".encode('utf-8'),  # 正常UTF-8
        "中文GBK编码".encode('gbk'),  # GBK编码
    ]
    
    def robust_decode(data, default_encoding='utf-8'):
        """健壮的解码函数"""
        if isinstance(data, str):
            return data, 'already_string'
        
        if not isinstance(data, bytes):
            return str(data), 'converted_to_string'
        
        # 常见编码列表
        encodings = [
            default_encoding,
            'gbk', 'gb2312',      # 中文编码
            'utf-16', 'utf-16le', 'utf-16be',  # UTF-16编码
            'latin-1', 'cp1252',  # 西文编码
            'iso-8859-1'          # 通用编码
        ]
        
        for encoding in encodings:
            try:
                decoded = data.decode(encoding)
                return decoded, encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # 最后的备选方案：使用错误处理
        try:
            return data.decode(default_encoding, errors='replace'), 'utf-8-replace'
        except:
            return data.decode('latin-1'), 'latin-1-fallback'
    
    for i, test_data in enumerate(test_cases):
        print(f"\n测试案例 {i+1}:")
        print(f"原始数据: {test_data[:20]}{'...' if len(test_data) > 20 else ''}")
        
        try:
            # 尝试原始UTF-8解码（会失败的情况）
            try:
                original_result = test_data.decode('utf-8')
                print(f"原始UTF-8解码: 成功 - {repr(original_result[:50])}")
            except UnicodeDecodeError as e:
                print(f"原始UTF-8解码: 失败 - {e}")
            
            # 使用修复后的解码方法
            fixed_result, used_encoding = robust_decode(test_data)
            print(f"修复后解码: 成功 - 编码: {used_encoding}")
            print(f"解码结果: {repr(fixed_result[:50])}")
            
        except Exception as e:
            print(f"修复方法也失败: {e}")


def test_filedialog_fix():
    """测试文件对话框修复"""
    print("\n" + "=" * 50)
    print("测试Tkinter文件对话框修复")
    print("=" * 50)
    
    # 模拟错误的参数使用
    def fixed_asksaveasfilename(**kwargs):
        """修复后的文件保存对话框"""
        # 修复常见的参数错误
        if 'initialname' in kwargs:
            print(f"检测到错误参数 'initialname': {kwargs['initialname']}")
            kwargs['initialfile'] = kwargs.pop('initialname')
            print(f"已修复为 'initialfile': {kwargs['initialfile']}")
        
        # 验证参数
        valid_params = {
            'confirmoverwrite', 'defaultextension', 'filetypes',
            'initialdir', 'initialfile', 'parent', 'title', 'typevariable'
        }
        
        invalid_params = set(kwargs.keys()) - valid_params
        if invalid_params:
            print(f"警告：检测到无效参数: {invalid_params}")
            # 过滤无效参数
            kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
        
        print(f"最终参数: {kwargs}")
        return "模拟保存路径/test_file.txt"  # 模拟返回值
    
    # 测试错误的参数使用
    print("\n测试错误参数修复:")
    try:
        result = fixed_asksaveasfilename(
            initialname="test_file.txt",  # 错误参数
            title="保存文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt")]
        )
        print(f"修复成功，返回: {result}")
    except Exception as e:
        print(f"修复失败: {e}")
    
    # 测试正确的参数使用
    print("\n测试正确参数:")
    try:
        result = fixed_asksaveasfilename(
            initialfile="test_file.txt",  # 正确参数
            title="保存文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt")]
        )
        print(f"正确参数测试成功，返回: {result}")
    except Exception as e:
        print(f"正确参数测试失败: {e}")


def create_sample_improved_file_manager():
    """创建示例的improved_file_manager.py文件结构"""
    print("\n" + "=" * 50)
    print("创建修复后的文件管理器示例代码")
    print("=" * 50)
    
    sample_code = '''
class ImprovedFileManager:
    def __init__(self):
        self.encryption_key = None
        self.file_listbox = None
        # 其他初始化代码...
    
    def on_file_double_click(self, event=None):
        """修复后的文件双击处理"""
        try:
            self.download_selected_file()
        except Exception as e:
            messagebox.showerror("错误", f"处理文件双击事件失败: {str(e)}")
    
    def download_selected_file(self):
        """修复后的文件下载方法"""
        try:
            selection = self.file_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个文件")
                return
            
            file_info = self.file_listbox.get(selection[0])
            file_name = file_info.split()[0]
            
            # 修复：使用正确的参数名
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=file_name,  # 修复：initialfile而不是initialname
                defaultextension="",
                filetypes=[("所有文件", "*.*")]
            )
            
            if save_path:
                file_data = self.get_file_content(file_name)
                
                # 安全解密和保存
                if self.encryption_key:
                    success, data, msg = self.safe_decrypt_file_data(file_data)
                    if success:
                        self.save_file_with_encoding_detection(save_path, data)
                    else:
                        messagebox.showerror("错误", msg)
                else:
                    self.save_file_with_encoding_detection(save_path, file_data)
                    
        except Exception as e:
            messagebox.showerror("错误", f"下载文件失败: {str(e)}")
    '''
    
    print("示例代码结构:")
    print(sample_code)


if __name__ == "__main__":
    print("文件管理器错误修复测试")
    print("Python版本:", sys.version)
    print("当前目录:", os.getcwd())
    
    # 运行测试
    test_utf8_decode_fix()
    test_filedialog_fix()
    create_sample_improved_file_manager()
    
    print("\n" + "=" * 50)
    print("修复总结:")
    print("1. UTF-8解码错误：使用多编码尝试和错误处理参数")
    print("2. Tkinter对话框错误：将 initialname 改为 initialfile")
    print("3. 添加了健壮的错误处理和文件类型检测")
    print("=" * 50)