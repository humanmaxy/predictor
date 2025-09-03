#!/usr/bin/env python3
"""
PyAutoGUI问题诊断和修复工具
"""

import sys
import subprocess
import importlib.util
import os
from pathlib import Path

def safe_print(text):
    """安全的打印函数，避免编码错误"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果有编码问题，使用ASCII安全版本
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

def get_python_info():
    """获取Python环境信息"""
    safe_print("[Python] Python环境信息:")
    safe_print(f"  版本: {sys.version}")
    safe_print(f"  可执行文件: {sys.executable}")
    safe_print(f"  路径: {sys.path[:3]}...")  # 只显示前3个路径
    safe_print("")

def check_pip():
    """检查pip是否可用"""
    try:
        import pip
        safe_print("[成功] pip可用")
        return True
    except ImportError:
        safe_print("[失败] pip不可用")
        return False

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"🔄 {description}...")
    print(f"   命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ {description}成功")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
        else:
            print(f"❌ {description}失败")
            print(f"   错误: {result.stderr.strip()}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description}超时")
        return False
    except Exception as e:
        print(f"❌ {description}异常: {e}")
        return False

def check_package_detailed(package_name):
    """详细检查包的安装状态"""
    print(f"🔍 详细检查 {package_name}:")
    
    # 方法1: importlib检查
    spec = importlib.util.find_spec(package_name)
    if spec:
        print(f"  ✅ importlib找到包: {spec.origin}")
    else:
        print(f"  ❌ importlib未找到包")
    
    # 方法2: 直接导入测试
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', '未知版本')
        print(f"  ✅ 直接导入成功，版本: {version}")
        return True, version
    except ImportError as e:
        print(f"  ❌ 直接导入失败: {e}")
        return False, None
    except Exception as e:
        print(f"  ❌ 导入异常: {e}")
        return False, None

def list_installed_packages():
    """列出已安装的相关包"""
    print("📦 检查已安装的相关包:")
    
    packages_to_check = ['pyautogui', 'pillow', 'pil', 'pygetwindow', 'pymsgbox', 'pytweening', 'pyscreeze']
    
    for package in packages_to_check:
        success, version = check_package_detailed(package)
        if success:
            print(f"  ✅ {package}: {version}")
        else:
            print(f"  ❌ {package}: 未安装")
    print()

def fix_pyautogui():
    """修复PyAutoGUI安装问题"""
    print("🔧 开始修复PyAutoGUI安装...")
    
    # 步骤1: 卸载可能冲突的包
    print("\n步骤1: 清理可能冲突的包")
    packages_to_uninstall = ['pyautogui', 'pyscreeze', 'pygetwindow', 'pymsgbox', 'pytweening']
    
    for package in packages_to_uninstall:
        run_command([sys.executable, "-m", "pip", "uninstall", package, "-y"], 
                   f"卸载 {package}")
    
    # 步骤2: 升级pip
    print("\n步骤2: 升级pip")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
               "升级pip")
    
    # 步骤3: 安装依赖包
    print("\n步骤3: 安装依赖包")
    dependencies = [
        "pillow>=9.0.0",
        "pytweening>=1.0.4",
        "pyscreeze>=0.1.28",
        "pygetwindow>=0.0.9",
        "pymsgbox>=1.0.9"
    ]
    
    for dep in dependencies:
        run_command([sys.executable, "-m", "pip", "install", dep], 
                   f"安装 {dep}")
    
    # 步骤4: 安装PyAutoGUI
    print("\n步骤4: 安装PyAutoGUI")
    success = run_command([sys.executable, "-m", "pip", "install", "pyautogui>=0.9.54"], 
                         "安装PyAutoGUI")
    
    if not success:
        print("尝试从源码安装...")
        run_command([sys.executable, "-m", "pip", "install", "--no-cache-dir", "pyautogui"], 
                   "从源码安装PyAutoGUI")
    
    return success

def test_pyautogui_functionality():
    """测试PyAutoGUI功能"""
    print("🧪 测试PyAutoGUI功能:")
    
    try:
        import pyautogui
        print(f"✅ 导入成功，版本: {pyautogui.__version__}")
        
        # 测试基本功能
        try:
            size = pyautogui.size()
            print(f"✅ 屏幕尺寸: {size}")
        except Exception as e:
            print(f"❌ 获取屏幕尺寸失败: {e}")
        
        try:
            pos = pyautogui.position()
            print(f"✅ 鼠标位置: {pos}")
        except Exception as e:
            print(f"❌ 获取鼠标位置失败: {e}")
        
        # 禁用故障保护
        pyautogui.FAILSAFE = False
        print("✅ 故障保护已禁用")
        
        return True
        
    except ImportError as e:
        print(f"❌ PyAutoGUI导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ PyAutoGUI测试失败: {e}")
        return False

def create_test_script():
    """创建测试脚本"""
    test_script = """
import sys
try:
    import pyautogui
    print(f"SUCCESS: PyAutoGUI {pyautogui.__version__} imported successfully")
    print(f"Screen size: {pyautogui.size()}")
    print(f"Mouse position: {pyautogui.position()}")
except ImportError as e:
    print(f"FAILED: PyAutoGUI import failed - {e}")
except Exception as e:
    print(f"ERROR: {e}")
"""
    
    script_path = Path("test_pyautogui_simple.py")
    script_path.write_text(test_script)
    print(f"✅ 创建测试脚本: {script_path}")
    
    # 运行测试脚本
    result = subprocess.run([sys.executable, str(script_path)], 
                           capture_output=True, text=True)
    
    print("🧪 测试脚本结果:")
    print(result.stdout)
    if result.stderr:
        print("错误:", result.stderr)
    
    return "SUCCESS" in result.stdout

def main():
    """主修复流程"""
    print("🔧 PyAutoGUI问题诊断和修复工具")
    print("=" * 60)
    
    # 1. 显示环境信息
    get_python_info()
    
    # 2. 检查pip
    if not check_pip():
        print("❌ pip不可用，无法继续")
        return
    
    # 3. 列出当前安装的包
    list_installed_packages()
    
    # 4. 测试当前PyAutoGUI状态
    print("🧪 测试当前PyAutoGUI状态:")
    if test_pyautogui_functionality():
        print("✅ PyAutoGUI已正常工作，无需修复")
        return
    
    # 5. 询问是否进行修复
    try:
        choice = input("\n是否尝试修复PyAutoGUI安装? (y/n): ").lower().strip()
        if choice != 'y':
            print("用户取消修复")
            return
    except KeyboardInterrupt:
        print("\n用户中断")
        return
    
    # 6. 执行修复
    print("\n" + "=" * 60)
    print("开始修复流程...")
    
    if fix_pyautogui():
        print("\n" + "=" * 60)
        print("修复完成，重新测试...")
        
        if test_pyautogui_functionality():
            print("🎉 修复成功！PyAutoGUI现在可以正常使用了")
            
            # 创建并运行简单测试
            if create_test_script():
                print("✅ 功能测试通过")
            else:
                print("⚠️ 功能测试未完全通过，但基本导入成功")
        else:
            print("❌ 修复后仍然有问题，可能需要手动处理")
    else:
        print("❌ 修复失败")
    
    print("\n" + "=" * 60)
    print("建议:")
    print("1. 重新启动Python环境")
    print("2. 如果问题持续，尝试在虚拟环境中安装")
    print("3. 检查系统权限设置（特别是macOS的辅助功能权限）")

if __name__ == "__main__":
    main()