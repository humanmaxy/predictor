#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查PyAutoGUI大小写问题
"""

import sys
import subprocess
import importlib.util

def safe_print(text):
    """安全的打印函数"""
    try:
        print(text)
    except UnicodeEncodeError:
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

def check_installed_packages():
    """检查已安装的包"""
    safe_print("[检查] 已安装的PyAutoGUI相关包:")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        pyautogui_packages = []
        
        for line in lines:
            if 'pyautogui' in line.lower() or 'PyAutoGUI' in line:
                pyautogui_packages.append(line.strip())
                safe_print(f"  发现包: {line.strip()}")
        
        if not pyautogui_packages:
            safe_print("  [警告] 未找到PyAutoGUI包")
        
        return pyautogui_packages
        
    except Exception as e:
        safe_print(f"[错误] 检查包列表失败: {e}")
        return []

def test_different_import_methods():
    """测试不同的导入方法"""
    safe_print("\n[测试] 尝试不同的导入方法:")
    
    import_methods = [
        ("pyautogui", "标准小写导入"),
        ("PyAutoGUI", "大写包名导入"),
        ("PYAUTOGUI", "全大写导入"),
    ]
    
    successful_imports = []
    
    for module_name, description in import_methods:
        try:
            # 方法1: 直接导入
            try:
                exec(f"import {module_name}")
                module = sys.modules[module_name]
                version = getattr(module, '__version__', '未知')
                safe_print(f"  [成功] {description}: 版本 {version}")
                successful_imports.append((module_name, module))
            except ImportError:
                safe_print(f"  [失败] {description}: 导入失败")
            
        except Exception as e:
            safe_print(f"  [错误] {description}: {e}")
    
    return successful_imports

def test_importlib_method():
    """使用importlib测试导入"""
    safe_print("\n[测试] 使用importlib查找模块:")
    
    module_names = ['pyautogui', 'PyAutoGUI', 'PYAUTOGUI']
    
    for name in module_names:
        try:
            spec = importlib.util.find_spec(name)
            if spec:
                safe_print(f"  [找到] {name}: {spec.origin}")
                
                # 尝试加载模块
                try:
                    module = importlib.import_module(name)
                    version = getattr(module, '__version__', '未知')
                    safe_print(f"    版本: {version}")
                    return name, module
                except Exception as e:
                    safe_print(f"    [错误] 加载失败: {e}")
            else:
                safe_print(f"  [未找到] {name}")
        except Exception as e:
            safe_print(f"  [错误] 查找 {name} 失败: {e}")
    
    return None, None

def fix_case_issue():
    """修复大小写问题"""
    safe_print("\n[修复] 尝试修复大小写问题:")
    
    # 检查是否安装了大写版本
    packages = check_installed_packages()
    has_uppercase = any('PyAutoGUI' in pkg for pkg in packages)
    
    if has_uppercase:
        safe_print("[发现] 检测到大写的PyAutoGUI包")
        safe_print("[建议] 卸载大写版本并重新安装小写版本")
        
        choice = input("是否执行修复? (y/n): ").lower().strip()
        if choice == 'y':
            try:
                # 卸载可能的所有版本
                safe_print("[执行] 卸载所有PyAutoGUI版本...")
                for pkg_name in ['PyAutoGUI', 'pyautogui', 'PYAUTOGUI']:
                    subprocess.run([sys.executable, "-m", "pip", "uninstall", pkg_name, "-y"], 
                                 capture_output=True)
                
                # 重新安装标准版本
                safe_print("[执行] 重新安装pyautogui...")
                result = subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui"], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    safe_print("[成功] PyAutoGUI重新安装完成")
                    return True
                else:
                    safe_print(f"[失败] 安装失败: {result.stderr}")
                    return False
                    
            except Exception as e:
                safe_print(f"[错误] 修复过程失败: {e}")
                return False
    
    return False

def main():
    """主函数"""
    safe_print("PyAutoGUI 大小写问题检查工具")
    safe_print("=" * 50)
    
    # 1. 检查已安装的包
    packages = check_installed_packages()
    
    # 2. 测试不同的导入方法
    successful_imports = test_different_import_methods()
    
    # 3. 使用importlib测试
    found_name, found_module = test_importlib_method()
    
    # 4. 总结结果
    safe_print("\n[结果] 检查总结:")
    
    if successful_imports:
        safe_print("[成功] 找到可用的导入方法:")
        for name, module in successful_imports:
            version = getattr(module, '__version__', '未知')
            safe_print(f"  - {name} (版本: {version})")
        
        # 测试基本功能
        safe_print("\n[测试] 测试基本功能:")
        try:
            # 使用第一个成功的导入
            name, module = successful_imports[0]
            
            # 测试屏幕尺寸
            size = module.size()
            safe_print(f"[成功] 屏幕尺寸: {size}")
            
            # 测试鼠标位置
            pos = module.position()
            safe_print(f"[成功] 鼠标位置: {pos}")
            
            # 禁用故障保护
            module.FAILSAFE = False
            safe_print("[成功] 故障保护已禁用")
            
            safe_print("\n[结论] PyAutoGUI功能正常！")
            
        except Exception as e:
            safe_print(f"[失败] 功能测试失败: {e}")
    else:
        safe_print("[失败] 未找到可用的PyAutoGUI导入方法")
        
        # 尝试修复
        if fix_case_issue():
            safe_print("\n[重新测试] 修复后重新测试...")
            test_different_import_methods()

if __name__ == "__main__":
    main()