#!/usr/bin/env python3
"""
生成自签名SSL证书的辅助脚本
仅用于开发和测试环境
"""

import subprocess
import os
import sys

def generate_ssl_certificate(cert_file="server.crt", key_file="server.key"):
    """生成自签名SSL证书"""
    
    # 检查是否已存在证书文件
    if os.path.exists(cert_file) or os.path.exists(key_file):
        response = input(f"证书文件已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return False
    
    print("正在生成SSL证书...")
    
    # OpenSSL命令
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-keyout", key_file, "-out", cert_file,
        "-days", "365", "-nodes",
        "-subj", "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    ]
    
    try:
        # 执行OpenSSL命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SSL证书生成成功！")
            print(f"   证书文件: {cert_file}")
            print(f"   私钥文件: {key_file}")
            print(f"   有效期: 365天")
            print(f"\n⚠️  注意：这是自签名证书，仅用于开发测试！")
            return True
        else:
            print(f"❌ 生成证书失败:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ 错误：未找到openssl命令")
        print("请安装OpenSSL:")
        print("  Ubuntu/Debian: sudo apt-get install openssl")
        print("  CentOS/RHEL: sudo yum install openssl")
        print("  macOS: brew install openssl")
        print("  Windows: 下载并安装OpenSSL")
        return False
    except Exception as e:
        print(f"❌ 生成证书时发生错误: {e}")
        return False

def generate_pem_certificate():
    """生成PEM格式的SSL证书"""
    cert_file = "publicKey.pem"
    key_file = "privateKey.pem"
    
    # 检查是否已存在证书文件
    if os.path.exists(cert_file) or os.path.exists(key_file):
        response = input(f"PEM证书文件已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return False
    
    print("正在生成PEM格式SSL证书...")
    
    # OpenSSL命令生成PEM格式
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", key_file, "-out", cert_file,
        "-days", "365", "-nodes",
        "-subj", "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ PEM格式SSL证书生成成功！")
            print(f"   证书文件: {cert_file}")
            print(f"   私钥文件: {key_file}")
            print(f"   有效期: 365天")
            print(f"\n现在可以使用HTTPS模式启动服务器:")
            print(f"python3 chat_server.py --ssl --cert {cert_file} --key {key_file}")
            return True
        else:
            print(f"❌ 生成PEM证书失败:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ 错误：未找到openssl命令")
        print("请安装OpenSSL")
        return False
    except Exception as e:
        print(f"❌ 生成PEM证书时发生错误: {e}")
        return False

def main():
    print("SSL证书生成工具")
    print("=" * 30)
    
    print("\n选择证书格式:")
    print("1. 生成标准SSL证书 (server.crt + server.key)")
    print("2. 生成PEM格式证书 (publicKey.pem + privateKey.pem)")
    print("3. 退出")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        if generate_ssl_certificate():
            print("\n现在您可以使用HTTPS模式启动服务器:")
            print("python3 chat_server.py --ssl --cert server.crt --key server.key")
        else:
            print("\n证书生成失败，您仍可以使用HTTP模式:")
            print("python3 chat_server.py")
    
    elif choice == "2":
        generate_pem_certificate()
    
    elif choice == "3":
        print("退出")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()