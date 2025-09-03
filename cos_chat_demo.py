#!/usr/bin/env python3
"""
COS聊天功能演示脚本
模拟多用户COS聊天
"""

import json
import time
import uuid
from datetime import datetime
import threading

# 模拟COS操作（用于演示）
class MockCOSManager:
    """模拟COS管理器（用于演示）"""
    def __init__(self):
        self.messages = []  # 模拟COS中的消息文件
        self.message_id_counter = 0
    
    def send_public_message(self, user_id: str, username: str, message: str):
        """发送群聊消息"""
        self.message_id_counter += 1
        message_data = {
            "type": "public",
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "_filename": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}.json"
        }
        self.messages.append(message_data)
        print(f"📤 [{username}] 发送群聊消息: {message}")
        return True
    
    def send_private_message(self, sender_id: str, sender_name: str, target_id: str, message: str):
        """发送私聊消息"""
        self.message_id_counter += 1
        message_data = {
            "type": "private",
            "sender_id": sender_id,
            "sender_name": sender_name,
            "target_id": target_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "_filename": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sender_id}.json"
        }
        self.messages.append(message_data)
        print(f"💬 [{sender_name}] -> [{target_id}] 私聊: {message}")
        return True
    
    def get_new_messages(self):
        """获取新消息"""
        # 模拟返回最近的消息
        return self.messages[-10:] if len(self.messages) > 10 else self.messages
    
    def get_online_users(self):
        """获取在线用户"""
        # 模拟在线用户
        return [("user1", "张三"), ("user2", "李四"), ("user3", "王五")]

def simulate_user_activity(cos_manager, user_id, username):
    """模拟用户活动"""
    messages = [
        "大家好！",
        "COS聊天功能真不错",
        "消息存储在云端很方便",
        "支持私聊功能吗？",
        "当然支持！"
    ]
    
    for i, msg in enumerate(messages):
        time.sleep(2)  # 每2秒发送一条消息
        cos_manager.send_public_message(user_id, username, f"{msg} (消息{i+1})")
    
    # 发送私聊消息
    time.sleep(1)
    cos_manager.send_private_message(user_id, username, "user2", "这是一条私聊消息")

def demo_cos_chat():
    """演示COS聊天功能"""
    print("🎯 COS聊天功能演示")
    print("=" * 50)
    
    # 创建模拟COS管理器
    cos_manager = MockCOSManager()
    
    print("📋 功能特点:")
    print("✅ 聊天记录存储在腾讯云COS")
    print("✅ 支持群聊和私聊")
    print("✅ 每3秒自动同步消息")
    print("✅ 多用户实时聊天")
    print("✅ 消息持久化存储")
    print()
    
    # 模拟多个用户
    users = [
        ("user1", "张三"),
        ("user2", "李四"), 
        ("user3", "王五")
    ]
    
    print("👥 模拟用户:")
    for user_id, username in users:
        print(f"   {username} (ID: {user_id})")
    print()
    
    # 启动用户活动线程
    threads = []
    for user_id, username in users:
        thread = threading.Thread(
            target=simulate_user_activity,
            args=(cos_manager, user_id, username),
            daemon=True
        )
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # 错开启动时间
    
    # 模拟消息同步
    print("🔄 开始消息同步演示...")
    for i in range(20):  # 演示20个同步周期
        time.sleep(3)  # 3秒同步间隔
        
        new_messages = cos_manager.get_new_messages()
        online_users = cos_manager.get_online_users()
        
        print(f"\n📡 第{i+1}次同步 - {datetime.now().strftime('%H:%M:%S')}")
        print(f"📊 消息总数: {len(new_messages)}")
        print(f"👥 在线用户: {len(online_users)}")
        
        # 显示最新消息
        if new_messages:
            latest_msg = new_messages[-1]
            if latest_msg['type'] == 'public':
                print(f"💬 最新群聊: [{latest_msg['username']}] {latest_msg['message']}")
            elif latest_msg['type'] == 'private':
                print(f"🔒 最新私聊: [{latest_msg['sender_name']}] -> [{latest_msg['target_id']}] {latest_msg['message']}")
    
    print("\n✅ 演示完成！")

def show_cos_file_structure():
    """显示COS文件结构"""
    print("\n📁 COS聊天室文件结构:")
    print("chat-room/")
    print("├── public/                    # 群聊消息目录")
    print("│   ├── msg_20241201_120001_user1.json")
    print("│   ├── msg_20241201_120002_user2.json")
    print("│   └── msg_20241201_120003_user3.json")
    print("└── private/                   # 私聊消息目录")
    print("    ├── user1_user2/           # 用户1和用户2的私聊")
    print("    │   ├── msg_20241201_120004_user1.json")
    print("    │   └── msg_20241201_120005_user2.json")
    print("    └── user1_user3/           # 用户1和用户3的私聊")
    print("        └── msg_20241201_120006_user1.json")
    print()
    
    print("📝 消息文件格式示例:")
    print("群聊消息:")
    public_msg = {
        "type": "public",
        "user_id": "user1",
        "username": "张三",
        "message": "大家好！",
        "timestamp": "2024-12-01T12:00:01.123456"
    }
    print(json.dumps(public_msg, ensure_ascii=False, indent=2))
    
    print("\n私聊消息:")
    private_msg = {
        "type": "private",
        "sender_id": "user1",
        "sender_name": "张三",
        "target_id": "user2",
        "message": "你好，这是私聊消息",
        "timestamp": "2024-12-01T12:00:02.123456"
    }
    print(json.dumps(private_msg, ensure_ascii=False, indent=2))

def main():
    """主函数"""
    print("🌟 COS云端聊天系统")
    print("=" * 50)
    
    print("\n选择演示模式:")
    print("1. 查看COS文件结构说明")
    print("2. 运行聊天功能演示")
    print("3. 启动COS聊天客户端")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        show_cos_file_structure()
    
    elif choice == "2":
        demo_cos_chat()
    
    elif choice == "3":
        try:
            import subprocess
            subprocess.run([sys.executable, "cos_chat_client.py"])
        except KeyboardInterrupt:
            print("已退出COS聊天客户端")
    
    elif choice == "4":
        print("👋 退出演示")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()