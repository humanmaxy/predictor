#!/usr/bin/env python3
"""
使用cryptography库生成SSL证书
适用于已安装cryptography库的环境
"""

import os
from datetime import datetime, timedelta
import ipaddress

def generate_ssl_certificate_cryptography():
    """使用cryptography库生成SSL证书"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        print("❌ 未安装cryptography库")
        print("请安装: pip install cryptography")
        return False
    
    cert_file = "publicKey.pem"
    key_file = "privateKey.pem"
    
    # 检查是否已存在证书文件
    if os.path.exists(cert_file) or os.path.exists(key_file):
        response = input(f"证书文件已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return False
    
    print("使用cryptography库生成SSL证书...")
    
    try:
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
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

        # 保存私钥
        with open(key_file, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # 保存证书
        with open(cert_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("✅ SSL证书生成成功！")
        print(f"   证书文件: {cert_file}")
        print(f"   私钥文件: {key_file}")
        print(f"   有效期: 365天")
        print(f"\n现在可以使用HTTPS模式启动服务器:")
        print(f"python3 chat_server.py --ssl --cert {cert_file} --key {key_file}")
        return True
        
    except Exception as e:
        print(f"❌ 生成SSL证书失败: {e}")
        return False

def main():
    print("SSL证书生成工具 (cryptography版本)")
    print("=" * 40)
    
    if generate_ssl_certificate_cryptography():
        print("\n✅ 证书生成完成！")
    else:
        print("\n❌ 证书生成失败")
        print("建议使用HTTP模式: python3 chat_server.py --host 0.0.0.0 --port 11900")