#!/usr/bin/env python3
"""
网络共享目录聊天清理服务
模拟每天凌晨2点清理旧数据
"""

import os
import json
import time
import schedule
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NetworkShareCleaner:
    """网络共享目录清理器"""
    def __init__(self, share_path: str):
        self.share_path = Path(share_path)
        self.public_dir = self.share_path / "public"
        self.private_dir = self.share_path / "private"
        self.users_dir = self.share_path / "users"
        self.logs_dir = self.share_path / "logs"
        
        # 确保日志目录存在
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_old_data(self, days_to_keep=1):
        """清理旧数据"""
        logger.info("开始执行每日清理任务...")
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        total_deleted = 0
        
        try:
            # 清理群聊消息
            public_deleted = self._cleanup_directory(self.public_dir, cutoff_time)
            total_deleted += public_deleted
            logger.info(f"清理群聊消息: {public_deleted} 个文件")
            
            # 清理私聊消息
            private_deleted = self._cleanup_private_messages(cutoff_time)
            total_deleted += private_deleted
            logger.info(f"清理私聊消息: {private_deleted} 个文件")
            
            # 清理过期心跳文件
            heartbeat_deleted = self._cleanup_heartbeat_files(cutoff_time)
            total_deleted += heartbeat_deleted
            logger.info(f"清理心跳文件: {heartbeat_deleted} 个文件")
            
            # 记录清理统计
            self._log_cleanup_stats(total_deleted, days_to_keep)
            
            logger.info(f"清理完成，总共删除 {total_deleted} 个文件")
            return total_deleted
            
        except Exception as e:
            logger.error(f"清理过程中发生错误: {e}")
            return 0
    
    def _cleanup_directory(self, directory: Path, cutoff_time: datetime):
        """清理指定目录"""
        deleted_count = 0
        
        try:
            if not directory.exists():
                return 0
            
            for file_path in directory.glob("*.json"):
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"删除文件: {file_path}")
                    
        except Exception as e:
            logger.error(f"清理目录失败 {directory}: {e}")
        
        return deleted_count
    
    def _cleanup_private_messages(self, cutoff_time: datetime):
        """清理私聊消息"""
        deleted_count = 0
        
        try:
            if not self.private_dir.exists():
                return 0
            
            for private_chat_dir in self.private_dir.iterdir():
                if private_chat_dir.is_dir():
                    # 清理私聊目录中的消息文件
                    dir_deleted = self._cleanup_directory(private_chat_dir, cutoff_time)
                    deleted_count += dir_deleted
                    
                    # 如果目录为空，删除目录
                    if not any(private_chat_dir.iterdir()):
                        private_chat_dir.rmdir()
                        logger.debug(f"删除空目录: {private_chat_dir}")
                        
        except Exception as e:
            logger.error(f"清理私聊消息失败: {e}")
        
        return deleted_count
    
    def _cleanup_heartbeat_files(self, cutoff_time: datetime):
        """清理心跳文件"""
        deleted_count = 0
        
        try:
            if not self.users_dir.exists():
                return 0
            
            for heartbeat_file in self.users_dir.glob("*_heartbeat.json"):
                file_mtime = datetime.fromtimestamp(heartbeat_file.stat().st_mtime)
                if file_mtime < cutoff_time:
                    heartbeat_file.unlink()
                    deleted_count += 1
                    logger.debug(f"删除心跳文件: {heartbeat_file}")
                    
        except Exception as e:
            logger.error(f"清理心跳文件失败: {e}")
        
        return deleted_count
    
    def _log_cleanup_stats(self, deleted_count: int, days_kept: int):
        """记录清理统计"""
        stats_file = self.logs_dir / "cleanup_stats.json"
        
        stats_data = {
            "cleanup_time": datetime.now().isoformat(),
            "deleted_files": deleted_count,
            "days_kept": days_kept,
            "share_path": str(self.share_path)
        }
        
        try:
            # 读取现有统计
            all_stats = []
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    all_stats = json.load(f)
            
            # 添加新统计
            all_stats.append(stats_data)
            
            # 只保留最近30天的统计
            if len(all_stats) > 30:
                all_stats = all_stats[-30:]
            
            # 保存统计
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"记录清理统计失败: {e}")
    
    def get_storage_info(self):
        """获取存储信息"""
        try:
            public_count = len(list(self.public_dir.glob("*.json"))) if self.public_dir.exists() else 0
            private_count = 0
            
            if self.private_dir.exists():
                for private_chat_dir in self.private_dir.iterdir():
                    if private_chat_dir.is_dir():
                        private_count += len(list(private_chat_dir.glob("*.json")))
            
            users_count = len(list(self.users_dir.glob("*_heartbeat.json"))) if self.users_dir.exists() else 0
            
            return {
                "public_messages": public_count,
                "private_messages": private_count,
                "active_users": users_count,
                "total_files": public_count + private_count + users_count
            }
            
        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            return {"error": str(e)}

def run_cleanup_service(share_path: str):
    """运行清理服务"""
    cleaner = NetworkShareCleaner(share_path)
    
    # 设置每天凌晨2点执行清理
    schedule.every().day.at("02:00").do(cleaner.cleanup_old_data)
    
    logger.info("清理服务已启动，每天凌晨2点执行清理任务")
    logger.info(f"监控目录: {share_path}")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("清理服务已停止")

def manual_cleanup(share_path: str, days_to_keep=1):
    """手动执行清理"""
    cleaner = NetworkShareCleaner(share_path)
    
    print(f"🧹 手动清理网络共享目录: {share_path}")
    print(f"📅 保留天数: {days_to_keep} 天")
    
    # 显示清理前的统计
    before_stats = cleaner.get_storage_info()
    print(f"📊 清理前统计: {before_stats}")
    
    # 执行清理
    deleted_count = cleaner.cleanup_old_data(days_to_keep)
    
    # 显示清理后的统计
    after_stats = cleaner.get_storage_info()
    print(f"📊 清理后统计: {after_stats}")
    print(f"✅ 清理完成，删除了 {deleted_count} 个文件")

def show_storage_stats(share_path: str):
    """显示存储统计"""
    cleaner = NetworkShareCleaner(share_path)
    stats = cleaner.get_storage_info()
    
    print("📊 网络共享聊天室存储统计")
    print("=" * 40)
    print(f"📁 共享路径: {share_path}")
    print(f"💬 群聊消息: {stats.get('public_messages', 0)} 条")
    print(f"🔒 私聊消息: {stats.get('private_messages', 0)} 条")
    print(f"👥 活跃用户: {stats.get('active_users', 0)} 人")
    print(f"📄 总文件数: {stats.get('total_files', 0)} 个")

def main():
    """主函数"""
    share_path = r"\\catl-tfile\Temp1day每天凌晨两点清理数据01\imdmmm"
    
    print("🧹 网络共享聊天室清理工具")
    print("=" * 50)
    
    print(f"📁 目标路径: {share_path}")
    print()
    
    print("选择操作:")
    print("1. 查看存储统计")
    print("2. 手动清理（保留1天）")
    print("3. 手动清理（保留3天）")
    print("4. 启动清理服务（每天凌晨2点自动清理）")
    print("5. 测试目录访问")
    print("6. 退出")
    
    choice = input("\n请选择 (1-6): ").strip()
    
    if choice == "1":
        show_storage_stats(share_path)
    
    elif choice == "2":
        manual_cleanup(share_path, days_to_keep=1)
    
    elif choice == "3":
        manual_cleanup(share_path, days_to_keep=3)
    
    elif choice == "4":
        print("🕐 启动清理服务...")
        run_cleanup_service(share_path)
    
    elif choice == "5":
        try:
            cleaner = NetworkShareCleaner(share_path)
            if cleaner.check_access():
                print("✅ 目录访问测试成功")
            else:
                print("❌ 目录访问测试失败")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    elif choice == "6":
        print("👋 退出")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    # 检查是否需要安装schedule库
    try:
        import schedule
    except ImportError:
        print("❌ 缺少schedule库，请安装: pip install schedule")
        print("或者使用手动清理功能")
        
    main()