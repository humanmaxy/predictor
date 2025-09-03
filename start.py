#!/usr/bin/env python3
"""
Coinglass数字货币分析系统启动脚本
自动检查依赖和配置，提供友好的启动体验
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查必要的依赖包"""
    required_packages = {
        'requests': 'requests',
        'pandas': 'pandas', 
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'openai': 'openai',
        'dotenv': 'python-dotenv'
    }
    
    missing_packages = []
    
    for package_name, pip_name in required_packages.items():
        try:
            importlib.import_module(package_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (缺失)")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\n📦 需要安装以下依赖包:")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n或者运行: pip install -r requirements.txt")
        return False
    
    return True

def check_config_files():
    """检查配置文件"""
    config_status = {}
    
    # 检查.env文件
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env配置文件存在")
        config_status['env'] = True
        
        # 检查API密钥配置
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'COINGLASS_API_KEY=' in content and len(content.split('COINGLASS_API_KEY=')[1].split('\n')[0].strip()) > 10:
            print("✅ Coinglass API密钥已配置")
            config_status['coinglass'] = True
        else:
            print("⚠️  Coinglass API密钥未配置或无效")
            config_status['coinglass'] = False
            
        if 'DEEPSEEK_API_KEY=' in content and len(content.split('DEEPSEEK_API_KEY=')[1].split('\n')[0].strip()) > 10:
            print("✅ DeepSeek API密钥已配置")
            config_status['deepseek'] = True
        else:
            print("⚠️  DeepSeek API密钥未配置或无效")
            config_status['deepseek'] = False
    else:
        print("❌ .env配置文件不存在")
        print("💡 请复制.env.example到.env并配置API密钥")
        config_status['env'] = False
    
    return config_status

def setup_environment():
    """设置环境"""
    print("🔧 环境配置检查...")
    
    # 检查并创建.env文件
    if not Path('.env').exists():
        if Path('.env.example').exists():
            try:
                import shutil
                shutil.copy('.env.example', '.env')
                print("✅ 已创建.env配置文件")
                print("💡 请编辑.env文件，添加您的API密钥")
            except Exception as e:
                print(f"❌ 创建.env文件失败: {e}")
        else:
            # 创建基础.env文件
            env_content = """# Coinglass API配置
COINGLASS_API_KEY=your_coinglass_api_key_here

# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
"""
            with open('.env', 'w') as f:
                f.write(env_content)
            print("✅ 已创建基础.env配置文件")

def show_startup_guide():
    """显示启动指南"""
    print("\n" + "=" * 60)
    print("📚 使用指南")
    print("=" * 60)
    print("""
🔑 API密钥获取:
  • Coinglass API: https://www.coinglass.com/zh/pro/api
  • DeepSeek API: https://platform.deepseek.com

🚀 快速开始:
  1. 在.env文件中配置API密钥
  2. 运行程序后在界面中也可以配置密钥
  3. 选择币种和时间框架
  4. 点击"获取数据"→"技术分析"→"AI预测"

📊 功能特色:
  • 实时K线数据获取
  • 完整技术指标分析 (RSI/KDJ/MACD/BOLL/VOL)
  • 斐波那契回调位分析
  • AI智能趋势预测
  • 小时级和日级别双时间框架
  • 多币种批量对比分析

⚠️  风险提示:
  本工具仅供学习研究使用，不构成投资建议
  数字货币投资风险极高，请理性投资
""")

def main():
    """主启动函数"""
    print("🚀 Coinglass数字货币技术分析与AI预测系统")
    print("=" * 60)
    
    # 1. 检查Python版本
    if not check_python_version():
        return
    
    print("\n📦 检查依赖包...")
    # 2. 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装必要的依赖包")
        return
    
    print("\n⚙️  检查配置...")
    # 3. 检查配置
    setup_environment()
    config_status = check_config_files()
    
    # 4. 显示启动指南
    show_startup_guide()
    
    # 5. 询问启动方式
    print("\n🎮 选择启动方式:")
    print("1. 启动GUI程序 (推荐)")
    print("2. 运行功能测试")
    print("3. 查看帮助信息")
    print("4. 退出")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 启动GUI程序...")
            if not config_status.get('env', False):
                print("⚠️  提醒: 请在程序界面中配置API密钥")
            
            # 启动GUI程序
            try:
                from coinglass_analyzer import main as gui_main
                gui_main()
            except ImportError as e:
                print(f"❌ 导入GUI模块失败: {e}")
                print("请确保所有文件都在正确位置")
            except Exception as e:
                print(f"❌ 启动GUI失败: {e}")
                
        elif choice == "2":
            print("\n🧪 运行功能测试...")
            try:
                import test_coinglass
                test_coinglass.main()
            except ImportError as e:
                print(f"❌ 导入测试模块失败: {e}")
            except Exception as e:
                print(f"❌ 测试运行失败: {e}")
                
        elif choice == "3":
            print("\n📖 帮助信息:")
            print("详细使用说明请查看 README.md 文件")
            print("或访问项目文档了解更多信息")
            
        elif choice == "4":
            print("👋 再见！")
            
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 用户取消，程序退出")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()