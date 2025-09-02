#!/usr/bin/env python3
"""
加密工具类
提供base64加密解密功能
"""

import base64
import json
import hashlib
from typing import Dict, Any

class ChatEncryption:
    """聊天加密工具"""
    
    # 硬编码的密钥（实际应用中可以更复杂）
    SECRET_KEY = "ChatRoom2024SecretKey!@#NetworkShare"
    
    @classmethod
    def _get_key_hash(cls):
        """获取密钥的哈希值用于验证"""
        return hashlib.md5(cls.SECRET_KEY.encode()).hexdigest()[:16]
    
    @classmethod
    def encrypt_message(cls, message_data: Dict[Any, Any]) -> str:
        """加密消息数据"""
        try:
            # 添加验证标识
            message_data['_encrypted'] = True
            message_data['_key_hash'] = cls._get_key_hash()
            
            # 转换为JSON字符串
            json_str = json.dumps(message_data, ensure_ascii=False)
            
            # Base64编码
            encoded_bytes = base64.b64encode(json_str.encode('utf-8'))
            
            # 再次Base64编码（双重编码增加安全性）
            double_encoded = base64.b64encode(encoded_bytes)
            
            return double_encoded.decode('utf-8')
            
        except Exception as e:
            print(f"加密失败: {e}")
            return ""
    
    @classmethod
    def decrypt_message(cls, encrypted_data: str) -> Dict[Any, Any]:
        """解密消息数据"""
        try:
            # 第一次Base64解码
            first_decode = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # 第二次Base64解码
            second_decode = base64.b64decode(first_decode)
            
            # 转换为JSON
            json_str = second_decode.decode('utf-8')
            message_data = json.loads(json_str)
            
            # 验证密钥
            if message_data.get('_key_hash') != cls._get_key_hash():
                raise ValueError("密钥验证失败")
            
            # 移除加密标识
            message_data.pop('_encrypted', None)
            message_data.pop('_key_hash', None)
            
            return message_data
            
        except Exception as e:
            print(f"解密失败: {e}")
            return {}
    
    @classmethod
    def encrypt_file_info(cls, file_info: Dict[Any, Any]) -> str:
        """加密文件信息"""
        return cls.encrypt_message(file_info)
    
    @classmethod
    def decrypt_file_info(cls, encrypted_info: str) -> Dict[Any, Any]:
        """解密文件信息"""
        return cls.decrypt_message(encrypted_info)
    
    @classmethod
    def is_encrypted_data(cls, data: str) -> bool:
        """检查数据是否已加密"""
        try:
            # 尝试解密来验证
            decrypted = cls.decrypt_message(data)
            return bool(decrypted)
        except:
            return False

def test_encryption():
    """测试加密功能"""
    print("🔐 测试聊天加密功能")
    
    # 测试消息加密
    test_message = {
        "type": "public",
        "user_id": "user1",
        "username": "张三",
        "message": "这是一条测试消息",
        "timestamp": "2024-12-01T12:00:00"
    }
    
    print("原始消息:")
    print(json.dumps(test_message, ensure_ascii=False, indent=2))
    
    # 加密
    encrypted = ChatEncryption.encrypt_message(test_message)
    print(f"\n加密后: {encrypted[:50]}...")
    
    # 解密
    decrypted = ChatEncryption.decrypt_message(encrypted)
    print("\n解密后:")
    print(json.dumps(decrypted, ensure_ascii=False, indent=2))
    
    # 验证
    assert decrypted['message'] == test_message['message']
    print("\n✅ 加密解密测试通过！")

if __name__ == "__main__":
    test_encryption()