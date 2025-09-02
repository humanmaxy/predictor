#!/usr/bin/env python3
"""
将cryptography库生成的密钥转换为SSL证书
"""

import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import ipaddress

def load_private_key(key_file):
    """加载私钥文件"""
    try:
        with open(key_file, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )
        return private_key
    except Exception as e:
        print(f"加载私钥失败: {e}")
        return None

def generate_ssl_certificate_from_key(private_key, cert_file="server.crt"):
    """从私钥生成SSL证书"""
    try:
        # 创建证书主题
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Chat Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        # 创建证书
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())

        # 保存证书
        with open(cert_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        return True
    except Exception as e:
        print(f"生成证书失败: {e}")
        return False

def convert_crypto_keys():
    """转换cryptography密钥为SSL证书"""
    private_key_file = "privateKey.pem"
    public_key_file = "publicKey.pem"
    cert_file = "server.crt"
    key_file = "server.key"
    
    print("转换cryptography密钥为SSL证书...")
    
    # 检查原始密钥文件
    if not os.path.exists(private_key_file):
        print(f"❌ 私钥文件不存在: {private_key_file}")
        return False
    
    # 加载私钥
    private_key = load_private_key(private_key_file)
    if not private_key:
        return False
    
    # 生成SSL证书
    if generate_ssl_certificate_from_key(private_key, cert_file):
        # 复制私钥文件为server.key格式
        try:
            with open(private_key_file, 'rb') as src, open(key_file, 'wb') as dst:
                dst.write(src.read())
            
            print("✅ SSL证书转换成功！")
            print(f"   证书文件: {cert_file}")
            print(f"   私钥文件: {key_file}")
            print("\n现在可以使用HTTPS模式启动服务器:")
            print(f"python3 chat_server.py --ssl --cert {cert_file} --key {key_file}")
            return True
        except Exception as e:
            print(f"❌ 复制私钥文件失败: {e}")
            return False
    
    return False

def generate_new_ssl_certificate():
    """生成新的SSL证书和私钥"""
    cert_file = "server.crt"
    key_file = "server.key"
    
    print("生成新的SSL证书...")
    
    try:
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # 生成证书
        if generate_ssl_certificate_from_key(private_key, cert_file):
            # 保存私钥
            with open(key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            print("✅ 新SSL证书生成成功！")
            print(f"   证书文件: {cert_file}")
            print(f"   私钥文件: {key_file}")
            return True
    except Exception as e:
        print(f"❌ 生成新证书失败: {e}")
        return False
    
    return False

def main():
    print("SSL证书修复工具")
    print("=" * 40)
    
    print("\n选择解决方案:")
    print("1. 使用HTTP模式（推荐，无需证书）")
    print("2. 从现有cryptography密钥生成SSL证书")
    print("3. 生成全新的SSL证书")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        print("\n✅ 推荐使用HTTP模式启动服务器:")
        print("python3 chat_server.py --host 0.0.0.0 --port 11900")
        print("\n客户端连接时选择HTTP协议即可")
    
    elif choice == "2":
        convert_crypto_keys()
    
    elif choice == "3":
        generate_new_ssl_certificate()
    
    elif choice == "4":
        print("退出")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()