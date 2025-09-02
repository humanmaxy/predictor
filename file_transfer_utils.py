#!/usr/bin/env python3
"""
文件传输工具类
支持文件和图片的上传下载
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import base64

class FileTransferManager:
    """文件传输管理器"""
    
    def __init__(self, share_path: str):
        self.share_path = Path(share_path)
        self.files_dir = self.share_path / "files"
        self.images_dir = self.share_path / "images"
        self.thumbnails_dir = self.share_path / "thumbnails"
        
        # 创建文件存储目录
        self._init_file_directories()
        
        # 支持的文件类型
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.supported_file_types = {
            '.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov'
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB限制
    
    def _init_file_directories(self):
        """初始化文件存储目录"""
        try:
            self.files_dir.mkdir(parents=True, exist_ok=True)
            self.images_dir.mkdir(parents=True, exist_ok=True)
            self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建文件目录失败: {e}")
            return False
    
    def get_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"计算文件哈希失败: {e}")
            return ""
    
    def is_supported_file(self, file_path: str) -> Tuple[bool, str]:
        """检查文件是否支持"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.supported_image_types:
            return True, "image"
        elif file_ext in self.supported_file_types:
            return True, "file"
        else:
            return False, "unsupported"
    
    def upload_file(self, local_file_path: str, user_id: str, username: str) -> Optional[Dict]:
        """上传文件到共享目录"""
        try:
            local_path = Path(local_file_path)
            
            # 检查文件是否存在
            if not local_path.exists():
                print(f"文件不存在: {local_file_path}")
                return None
            
            # 检查文件大小
            file_size = local_path.stat().st_size
            if file_size > self.max_file_size:
                print(f"文件过大: {file_size / 1024 / 1024:.1f}MB > {self.max_file_size / 1024 / 1024}MB")
                return None
            
            # 检查文件类型
            is_supported, file_type = self.is_supported_file(local_file_path)
            if not is_supported:
                print(f"不支持的文件类型: {local_path.suffix}")
                return None
            
            # 计算文件哈希
            file_hash = self.get_file_hash(local_file_path)
            if not file_hash:
                return None
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = local_path.suffix
            new_filename = f"{timestamp}_{user_id}_{file_hash[:8]}{file_ext}"
            
            # 确定存储目录
            if file_type == "image":
                target_dir = self.images_dir
            else:
                target_dir = self.files_dir
            
            target_path = target_dir / new_filename
            
            # 复制文件
            shutil.copy2(local_file_path, target_path)
            
            # 如果是图片，生成缩略图
            thumbnail_path = None
            if file_type == "image":
                thumbnail_path = self._generate_thumbnail(target_path, new_filename)
            
            # 创建文件信息
            file_info = {
                "filename": new_filename,
                "original_name": local_path.name,
                "file_type": file_type,
                "file_size": file_size,
                "file_hash": file_hash,
                "mime_type": mimetypes.guess_type(local_file_path)[0] or "application/octet-stream",
                "upload_time": datetime.now().isoformat(),
                "uploader_id": user_id,
                "uploader_name": username,
                "relative_path": str(target_path.relative_to(self.share_path)),
                "thumbnail_path": str(thumbnail_path.relative_to(self.share_path)) if thumbnail_path else None
            }
            
            print(f"文件上传成功: {local_path.name} -> {new_filename}")
            return file_info
            
        except Exception as e:
            print(f"文件上传失败: {e}")
            return None
    
    def _generate_thumbnail(self, image_path: Path, filename: str) -> Optional[Path]:
        """生成图片缩略图"""
        try:
            # 这里使用简单的复制作为缩略图
            # 实际应用中可以使用PIL库生成真正的缩略图
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = self.thumbnails_dir / thumbnail_filename
            shutil.copy2(image_path, thumbnail_path)
            return thumbnail_path
        except Exception as e:
            print(f"生成缩略图失败: {e}")
            return None
    
    def download_file(self, file_info: Dict, local_dir: str) -> bool:
        """下载文件到本地"""
        try:
            # 构建共享文件路径
            shared_file_path = self.share_path / file_info["relative_path"]
            
            if not shared_file_path.exists():
                print(f"共享文件不存在: {shared_file_path}")
                return False
            
            # 构建本地文件路径
            local_path = Path(local_dir) / file_info["original_name"]
            
            # 如果文件已存在，添加序号
            counter = 1
            while local_path.exists():
                stem = Path(file_info["original_name"]).stem
                suffix = Path(file_info["original_name"]).suffix
                local_path = Path(local_dir) / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # 复制文件
            shutil.copy2(shared_file_path, local_path)
            
            print(f"文件下载成功: {file_info['original_name']} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"文件下载失败: {e}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """获取文件信息"""
        try:
            # 在files和images目录中查找
            for directory in [self.files_dir, self.images_dir]:
                file_path = directory / filename
                if file_path.exists():
                    stat = file_path.stat()
                    return {
                        "filename": filename,
                        "file_size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "relative_path": str(file_path.relative_to(self.share_path))
                    }
            return None
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return None
    
    def cleanup_old_files(self, days_to_keep: int = 7) -> int:
        """清理旧文件"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            # 清理files目录
            for file_path in self.files_dir.glob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            # 清理images目录
            for file_path in self.images_dir.glob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            # 清理thumbnails目录
            for file_path in self.thumbnails_dir.glob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            print(f"清理了 {deleted_count} 个旧文件")
            return deleted_count
            
        except Exception as e:
            print(f"清理文件失败: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict:
        """获取存储统计信息"""
        try:
            stats = {
                "files_count": 0,
                "images_count": 0,
                "thumbnails_count": 0,
                "total_size": 0
            }
            
            # 统计files目录
            if self.files_dir.exists():
                for file_path in self.files_dir.glob("*"):
                    if file_path.is_file():
                        stats["files_count"] += 1
                        stats["total_size"] += file_path.stat().st_size
            
            # 统计images目录
            if self.images_dir.exists():
                for file_path in self.images_dir.glob("*"):
                    if file_path.is_file():
                        stats["images_count"] += 1
                        stats["total_size"] += file_path.stat().st_size
            
            # 统计thumbnails目录
            if self.thumbnails_dir.exists():
                for file_path in self.thumbnails_dir.glob("*"):
                    if file_path.is_file():
                        stats["thumbnails_count"] += 1
                        stats["total_size"] += file_path.stat().st_size
            
            return stats
            
        except Exception as e:
            print(f"获取存储统计失败: {e}")
            return {}

def test_file_transfer():
    """测试文件传输功能"""
    import tempfile
    
    print("📁 测试文件传输功能")
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建文件传输管理器
        file_manager = FileTransferManager(temp_dir)
        
        # 创建测试文件
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("这是一个测试文件", encoding='utf-8')
        
        print(f"创建测试文件: {test_file}")
        
        # 测试文件上传
        file_info = file_manager.upload_file(str(test_file), "user1", "张三")
        
        if file_info:
            print("✅ 文件上传成功")
            print(f"文件信息: {file_info['filename']}")
            
            # 测试存储统计
            stats = file_manager.get_storage_stats()
            print(f"存储统计: {stats}")
            
            print("✅ 文件传输测试通过！")
        else:
            print("❌ 文件上传失败")

if __name__ == "__main__":
    test_file_transfer()