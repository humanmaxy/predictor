#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境设置和依赖检查脚本
解决PyAutoGUI导入和Pylance警告问题
"""

import sys
import subprocess
import importlib.util
import os
from pathlib import Path

def safe_print(text):
    """安全打印，避免编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))

def check_python_environment():
    """检查Python环境"""
    safe_print("=" * 60)
    safe_print("Python环境检查")
    safe_print("=" * 60)
    
    safe_print(f"Python版本: {sys.version}")
    safe_print(f"Python路径: {sys.executable}")
    safe_print(f"工作目录: {os.getcwd()}")
    
    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    safe_print(f"虚拟环境: {'是' if in_venv else '否'}")
    
    if in_venv:
        safe_print(f"虚拟环境路径: {sys.prefix}")

def check_and_install_dependencies():
    """检查并安装依赖"""
    safe_print("\n" + "=" * 60)
    safe_print("依赖检查和安装")
    safe_print("=" * 60)
    
    dependencies = [
        ("pillow", "PIL图像处理"),
        ("pyautogui", "鼠标键盘控制")
    ]
    
    installed = []
    failed = []
    
    for package, description in dependencies:
        safe_print(f"\n检查 {package} ({description})...")
        
        # 检查是否已安装
        spec = importlib.util.find_spec(package)
        if spec:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', '未知版本')
                safe_print(f"  [已安装] {package} {version}")
                installed.append((package, version))
                continue
            except Exception as e:
                safe_print(f"  [导入失败] {package}: {e}")
        
        # 尝试安装
        safe_print(f"  [安装中] 正在安装 {package}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                safe_print(f"  [成功] {package} 安装完成")
                installed.append((package, "新安装"))
            else:
                safe_print(f"  [失败] {package} 安装失败")
                safe_print(f"    错误: {result.stderr.strip()}")
                failed.append(package)
                
        except subprocess.TimeoutExpired:
            safe_print(f"  [超时] {package} 安装超时")
            failed.append(package)
        except Exception as e:
            safe_print(f"  [异常] {package} 安装异常: {e}")
            failed.append(package)
    
    return installed, failed

def test_pyautogui_import():
    """测试PyAutoGUI导入"""
    safe_print("\n" + "=" * 60)
    safe_print("PyAutoGUI导入测试")
    safe_print("=" * 60)
    
    # 尝试不同的导入方法
    import_methods = [
        ('pyautogui', '标准小写'),
        ('PyAutoGUI', '大写包名'),
        ('PYAUTOGUI', '全大写')
    ]
    
    successful_imports = []
    
    for module_name, description in import_methods:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', '未知')
            safe_print(f"[成功] {description} ({module_name}): 版本 {version}")
            successful_imports.append((module_name, module, version))
        except ImportError:
            safe_print(f"[失败] {description} ({module_name}): 导入失败")
        except Exception as e:
            safe_print(f"[错误] {description} ({module_name}): {e}")
    
    if successful_imports:
        # 测试基本功能
        safe_print(f"\n测试基本功能 (使用 {successful_imports[0][0]})...")
        try:
            module = successful_imports[0][1]
            
            # 测试屏幕尺寸
            size = module.size()
            safe_print(f"[成功] 屏幕尺寸: {size[0]}x{size[1]}")
            
            # 测试鼠标位置
            pos = module.position()
            safe_print(f"[成功] 鼠标位置: ({pos.x}, {pos.y})")
            
            # 禁用故障保护
            module.FAILSAFE = False
            safe_print("[成功] 故障保护已禁用")
            
            return True, successful_imports[0]
            
        except Exception as e:
            safe_print(f"[失败] 功能测试失败: {e}")
            return False, None
    else:
        safe_print("[失败] 所有导入方法都失败")
        return False, None

def create_vscode_settings():
    """创建VS Code设置文件"""
    safe_print("\n" + "=" * 60)
    safe_print("创建VS Code/Pylance配置")
    safe_print("=" * 60)
    
    try:
        # 创建.vscode目录
        vscode_dir = Path(".vscode")
        vscode_dir.mkdir(exist_ok=True)
        
        # 创建settings.json
        settings = {
            "python.analysis.extraPaths": ["./stubs"],
            "python.analysis.stubPath": "./stubs",
            "python.analysis.diagnosticMode": "workspace",
            "python.analysis.typeCheckingMode": "basic",
            "pylance.insidersChannel": "off"
        }
        
        settings_file = vscode_dir / "settings.json"
        import json
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        safe_print(f"[创建] {settings_file}")
        
        # 更新pyrightconfig.json
        pyright_config = {
            "reportMissingModuleSource": "none",
            "reportMissingImports": "warning",
            "reportOptionalMemberAccess": "none",
            "pythonVersion": "3.7",
            "stubPath": "./stubs"
        }
        
        config_file = Path("pyrightconfig.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(pyright_config, f, indent=2)
        
        safe_print(f"[更新] {config_file}")
        
        return True
        
    except Exception as e:
        safe_print(f"[失败] 配置文件创建失败: {e}")
        return False

def main():
    """主函数"""
    safe_print("远程控制环境设置工具")
    safe_print("解决PyAutoGUI导入和Pylance警告问题")
    
    # 1. 检查Python环境
    check_python_environment()
    
    # 2. 检查并安装依赖
    installed, failed = check_and_install_dependencies()
    
    # 3. 测试PyAutoGUI导入
    import_success, import_info = test_pyautogui_import()
    
    # 4. 创建VS Code配置
    vscode_success = create_vscode_settings()
    
    # 5. 总结
    safe_print("\n" + "=" * 60)
    safe_print("设置总结")
    safe_print("=" * 60)
    
    safe_print(f"已安装依赖: {len(installed)}")
    for package, version in installed:
        safe_print(f"  - {package}: {version}")
    
    if failed:
        safe_print(f"安装失败: {len(failed)}")
        for package in failed:
            safe_print(f"  - {package}")
    
    safe_print(f"PyAutoGUI导入: {'成功' if import_success else '失败'}")
    if import_success and import_info:
        safe_print(f"  使用模块: {import_info[0]} (版本: {import_info[2]})")
    
    safe_print(f"VS Code配置: {'成功' if vscode_success else '失败'}")
    
    if import_success and vscode_success:
        safe_print("\n[完成] 环境设置成功！")
        safe_print("建议:")
        safe_print("1. 重启VS Code以应用新配置")
        safe_print("2. 运行: python network_share_chat.py")
        safe_print("3. 或运行: python start_remote_assistance.py")
    else:
        safe_print("\n[警告] 环境设置部分失败")
        safe_print("请检查错误信息并手动解决问题")

if __name__ == "__main__":
    main()