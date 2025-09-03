#!/usr/bin/env python3
"""
测试网络共享目录聊天功能
"""

import os
import json
import time
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# 导入聊天管理器
from network_share_chat import NetworkShareChatManager

def test_network_share_chat():
    """测试网络共享聊天功能"""
    print("🧪 测试网络共享目录聊天功能")
    print("=" * 50)
    
    # 创建临时测试目录（模拟网络共享目录）
    test_dir = Path(tempfile.mkdtemp(prefix="test_chat_"))
    print(f"📁 测试目录: {test_dir}")
    
    try:
        # 创建聊天管理器
        chat_manager = NetworkShareChatManager(str(test_dir))
        
        print("\n✅ 1. 测试目录初始化...")
        assert chat_manager.check_access(), "目录访问测试失败"
        print("   目录访问正常")
        
        print("\n✅ 2. 测试群聊消息...")
        # 发送群聊消息
        assert chat_manager.send_public_message("user1", "张三", "大家好！"), "发送群聊消息失败"
        assert chat_manager.send_public_message("user2", "李四", "你好张三！"), "发送群聊消息失败"
        print("   群聊消息发送成功")
        
        print("\n✅ 3. 测试私聊消息...")
        # 发送私聊消息
        assert chat_manager.send_private_message("user1", "张三", "user2", "这是私聊消息"), "发送私聊消息失败"
        assert chat_manager.send_private_message("user2", "李四", "user1", "收到你的私聊"), "发送私聊消息失败"
        print("   私聊消息发送成功")
        
        print("\n✅ 4. 测试心跳功能...")
        # 更新心跳
        assert chat_manager.update_user_heartbeat("user1", "张三"), "心跳更新失败"
        assert chat_manager.update_user_heartbeat("user2", "李四"), "心跳更新失败"
        print("   心跳更新成功")
        
        print("\n✅ 5. 测试消息获取...")
        # 获取消息
        messages_user1 = chat_manager.get_new_messages("user1")
        messages_user2 = chat_manager.get_new_messages("user2")
        
        print(f"   用户1获取到 {len(messages_user1)} 条消息")
        print(f"   用户2获取到 {len(messages_user2)} 条消息")
        
        # 显示消息内容
        for msg in messages_user1:
            if msg['type'] == 'public':
                print(f"   群聊: [{msg['username']}] {msg['message']}")
            elif msg['type'] == 'private':
                print(f"   私聊: [{msg['sender_name']}] -> [{msg['target_id']}] {msg['message']}")
        
        print("\n✅ 6. 测试在线用户...")
        online_users = chat_manager.get_online_users()
        print(f"   在线用户: {online_users}")
        
        print("\n✅ 7. 测试存储统计...")
        stats = chat_manager.get_storage_info()
        print(f"   存储统计: {stats}")
        
        print("\n✅ 8. 测试清理功能...")
        # 等待一秒确保文件时间戳不同
        time.sleep(1)
        deleted_count = chat_manager.cleanup_old_messages(days_to_keep=0)  # 清理所有消息
        print(f"   清理了 {deleted_count} 个文件")
        
        print("\n🎉 所有测试通过！")
        
        # 显示目录结构
        print(f"\n📁 测试目录结构:")
        for root, dirs, files in os.walk(test_dir):
            level = root.replace(str(test_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
        
    finally:
        # 清理测试目录
        try:
            shutil.rmtree(test_dir)
            print(f"\n🧹 已清理测试目录: {test_dir}")
        except:
            pass

def test_message_format():
    """测试消息格式"""
    print("\n📝 消息格式示例:")
    
    # 群聊消息格式
    public_msg = {
        "type": "public",
        "user_id": "user1",
        "username": "张三",
        "message": "大家好！",
        "timestamp": datetime.now().isoformat()
    }
    print("群聊消息:")
    print(json.dumps(public_msg, ensure_ascii=False, indent=2))
    
    # 私聊消息格式
    private_msg = {
        "type": "private",
        "sender_id": "user1",
        "sender_name": "张三",
        "target_id": "user2",
        "message": "你好，这是私聊消息",
        "timestamp": datetime.now().isoformat()
    }
    print("\n私聊消息:")
    print(json.dumps(private_msg, ensure_ascii=False, indent=2))
    
    # 心跳文件格式
    heartbeat = {
        "user_id": "user1",
        "username": "张三",
        "last_active": datetime.now().isoformat(),
        "status": "online"
    }
    print("\n心跳文件:")
    print(json.dumps(heartbeat, ensure_ascii=False, indent=2))

def main():
    """主函数"""
    print("🧪 网络共享聊天功能测试工具")
    print("=" * 50)
    
    print("\n选择测试项目:")
    print("1. 完整功能测试")
    print("2. 查看消息格式")
    print("3. 启动网络共享聊天客户端")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        test_network_share_chat()
    
    elif choice == "2":
        test_message_format()
    
    elif choice == "3":
        try:
            import subprocess
            import sys
            subprocess.run([sys.executable, "network_share_chat.py"])
        except KeyboardInterrupt:
            print("已退出网络共享聊天客户端")
    
    elif choice == "4":
        print("👋 退出测试")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()