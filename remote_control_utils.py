#!/usr/bin/env python3
"""
远程控制工具类
支持屏幕捕获、屏幕共享和远程控制功能
"""

import os
import sys
import time
import json
import threading
import io
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple, Callable
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageGrab
import socket
import struct

# 尝试导入鼠标键盘控制库
PYAUTOGUI_AVAILABLE = False
pyautogui = None

def try_import_pyautogui():
    """尝试导入PyAutoGUI"""
    global PYAUTOGUI_AVAILABLE, pyautogui
    
    try:
        import pyautogui as pg
        pyautogui = pg
        PYAUTOGUI_AVAILABLE = True
        # 禁用pyautogui的故障保护
        pyautogui.FAILSAFE = False
        print(f"✅ PyAutoGUI已加载，版本: {getattr(pyautogui, '__version__', '未知')}")
        return True
    except ImportError as e:
        print(f"❌ PyAutoGUI导入失败: {e}")
        print("解决方案:")
        print("  1. 运行: python fix_pyautogui.py")
        print("  2. 或手动安装: pip install pyautogui")
        print("  3. 屏幕共享功能仍可使用，但远程控制功能将受限")
        return False
    except Exception as e:
        print(f"❌ PyAutoGUI初始化失败: {e}")
        print("可能的原因:")
        print("  - 缺少系统权限（macOS需要辅助功能权限）")
        print("  - X11显示问题（Linux）")
        print("  - 运行: python fix_pyautogui.py 进行诊断")
        return False

# 初始导入尝试
try_import_pyautogui()

class ScreenCapture:
    """屏幕捕获类"""
    
    def __init__(self):
        self.capturing = False
        self.capture_thread = None
        self.capture_callback = None
        self.capture_interval = 0.1  # 100ms间隔
        self.image_quality = 70  # JPEG质量
        self.scale_factor = 0.5  # 缩放因子，减少传输数据量
    
    def start_capture(self, callback: Callable[[bytes], None]):
        """开始屏幕捕获"""
        if self.capturing:
            return False
        
        self.capture_callback = callback
        self.capturing = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        return True
    
    def stop_capture(self):
        """停止屏幕捕获"""
        self.capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
    
    def _capture_loop(self):
        """屏幕捕获循环"""
        try:
            while self.capturing:
                # 捕获屏幕
                screenshot = ImageGrab.grab()
                
                # 缩放图像以减少数据量
                if self.scale_factor != 1.0:
                    new_size = (
                        int(screenshot.width * self.scale_factor),
                        int(screenshot.height * self.scale_factor)
                    )
                    screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
                
                # 转换为JPEG格式
                buffer = io.BytesIO()
                screenshot.save(buffer, format='JPEG', quality=self.image_quality)
                image_data = buffer.getvalue()
                
                # 调用回调函数
                if self.capture_callback:
                    self.capture_callback(image_data)
                
                time.sleep(self.capture_interval)
                
        except Exception as e:
            print(f"屏幕捕获错误: {e}")
        finally:
            self.capturing = False

class RemoteController:
    """远程控制类"""
    
    def __init__(self):
        self.enabled = PYAUTOGUI_AVAILABLE
        if not self.enabled:
            print("远程控制功能不可用：缺少pyautogui库")
            print("运行 'python fix_pyautogui.py' 进行修复")
    
    def retry_import(self):
        """重新尝试导入PyAutoGUI"""
        global PYAUTOGUI_AVAILABLE
        if try_import_pyautogui():
            self.enabled = True
            print("✅ PyAutoGUI重新导入成功，远程控制功能已启用")
            return True
        return False
    
    def move_mouse(self, x: int, y: int, screen_size: Tuple[int, int] = None):
        """移动鼠标"""
        if not self.enabled:
            return False
        
        try:
            # 如果提供了屏幕尺寸，进行坐标转换
            if screen_size:
                current_size = pyautogui.size()
                x = int(x * current_size[0] / screen_size[0])
                y = int(y * current_size[1] / screen_size[1])
            
            pyautogui.moveTo(x, y)
            return True
        except Exception as e:
            print(f"移动鼠标失败: {e}")
            return False
    
    def click_mouse(self, x: int, y: int, button: str = 'left', screen_size: Tuple[int, int] = None):
        """点击鼠标"""
        if not self.enabled:
            return False
        
        try:
            # 坐标转换
            if screen_size:
                current_size = pyautogui.size()
                x = int(x * current_size[0] / screen_size[0])
                y = int(y * current_size[1] / screen_size[1])
            
            pyautogui.click(x, y, button=button)
            return True
        except Exception as e:
            print(f"点击鼠标失败: {e}")
            return False
    
    def scroll_mouse(self, x: int, y: int, delta: int, screen_size: Tuple[int, int] = None):
        """滚动鼠标"""
        if not self.enabled:
            return False
        
        try:
            # 坐标转换
            if screen_size:
                current_size = pyautogui.size()
                x = int(x * current_size[0] / screen_size[0])
                y = int(y * current_size[1] / screen_size[1])
            
            pyautogui.scroll(delta, x=x, y=y)
            return True
        except Exception as e:
            print(f"滚动鼠标失败: {e}")
            return False
    
    def press_key(self, key: str):
        """按下按键"""
        if not self.enabled:
            return False
        
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            print(f"按键失败: {e}")
            return False
    
    def type_text(self, text: str):
        """输入文本"""
        if not self.enabled:
            return False
        
        try:
            pyautogui.write(text)
            return True
        except Exception as e:
            print(f"输入文本失败: {e}")
            return False

class RemoteControlManager:
    """远程控制管理器"""
    
    def __init__(self, share_path: str):
        self.share_path = Path(share_path)
        self.remote_dir = self.share_path / "remote_control"
        self.screen_dir = self.remote_dir / "screens"
        self.control_dir = self.remote_dir / "controls"
        
        # 创建目录
        self._init_directories()
        
        # 组件
        self.screen_capture = ScreenCapture()
        self.remote_controller = RemoteController()
        
        # 状态
        self.is_sharing = False
        self.is_controlling = False
        self.user_id = None
        
        # 屏幕共享相关
        self.screen_file_counter = 0
        self.max_screen_files = 10  # 最多保留10个屏幕文件
        
        # 控制命令监听
        self.control_monitor_thread = None
        self.monitoring = False
    
    def _init_directories(self):
        """初始化目录结构"""
        try:
            self.remote_dir.mkdir(parents=True, exist_ok=True)
            self.screen_dir.mkdir(exist_ok=True)
            self.control_dir.mkdir(exist_ok=True)
            
            # 创建配置文件
            config_file = self.remote_dir / "config.json"
            if not config_file.exists():
                config = {
                    "screen_share_enabled": False,
                    "remote_control_enabled": False,
                    "max_screen_files": 10,
                    "capture_interval": 0.1,
                    "image_quality": 70
                }
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"初始化远程控制目录失败: {e}")
            return False
    
    def start_screen_sharing(self, user_id: str) -> bool:
        """开始屏幕共享"""
        if self.is_sharing:
            return False
        
        self.user_id = user_id
        self.is_sharing = True
        
        def screen_callback(image_data: bytes):
            self._save_screen_data(image_data)
        
        success = self.screen_capture.start_capture(screen_callback)
        if not success:
            self.is_sharing = False
        
        return success
    
    def stop_screen_sharing(self):
        """停止屏幕共享"""
        if not self.is_sharing:
            return
        
        self.is_sharing = False
        self.screen_capture.stop_capture()
        
        # 清理屏幕文件
        self._cleanup_screen_files()
    
    def start_remote_control_listening(self, user_id: str) -> bool:
        """开始监听远程控制命令"""
        if self.is_controlling:
            return False
        
        self.user_id = user_id
        self.is_controlling = True
        self.monitoring = True
        
        self.control_monitor_thread = threading.Thread(
            target=self._monitor_control_commands, daemon=True
        )
        self.control_monitor_thread.start()
        
        return True
    
    def stop_remote_control_listening(self):
        """停止监听远程控制命令"""
        if not self.is_controlling:
            return
        
        self.is_controlling = False
        self.monitoring = False
        
        if self.control_monitor_thread:
            self.control_monitor_thread.join(timeout=1.0)
    
    def send_control_command(self, command: Dict) -> bool:
        """发送控制命令"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            command_file = self.control_dir / f"cmd_{timestamp}_{self.user_id}.json"
            
            command_data = {
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "command": command
            }
            
            with open(command_file, 'w', encoding='utf-8') as f:
                json.dump(command_data, f, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"发送控制命令失败: {e}")
            return False
    
    def get_latest_screen(self) -> Optional[bytes]:
        """获取最新的屏幕截图"""
        try:
            screen_files = list(self.screen_dir.glob("screen_*.jpg"))
            if not screen_files:
                return None
            
            # 按修改时间排序，获取最新的
            latest_file = max(screen_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'rb') as f:
                return f.read()
                
        except Exception as e:
            print(f"获取屏幕截图失败: {e}")
            return None
    
    def _save_screen_data(self, image_data: bytes):
        """保存屏幕数据"""
        try:
            self.screen_file_counter += 1
            filename = f"screen_{self.screen_file_counter:06d}_{self.user_id}.jpg"
            filepath = self.screen_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # 清理旧文件
            if self.screen_file_counter % self.max_screen_files == 0:
                self._cleanup_old_screen_files()
                
        except Exception as e:
            print(f"保存屏幕数据失败: {e}")
    
    def _cleanup_old_screen_files(self):
        """清理旧的屏幕文件"""
        try:
            screen_files = list(self.screen_dir.glob("screen_*.jpg"))
            if len(screen_files) > self.max_screen_files:
                # 按修改时间排序，删除最旧的文件
                screen_files.sort(key=lambda f: f.stat().st_mtime)
                for old_file in screen_files[:-self.max_screen_files]:
                    old_file.unlink()
        except Exception as e:
            print(f"清理屏幕文件失败: {e}")
    
    def _cleanup_screen_files(self):
        """清理所有屏幕文件"""
        try:
            for screen_file in self.screen_dir.glob("screen_*.jpg"):
                screen_file.unlink()
        except Exception as e:
            print(f"清理屏幕文件失败: {e}")
    
    def _monitor_control_commands(self):
        """监听控制命令"""
        try:
            processed_commands = set()
            
            while self.monitoring:
                # 检查控制命令文件
                command_files = list(self.control_dir.glob("cmd_*.json"))
                
                for cmd_file in command_files:
                    if cmd_file.name in processed_commands:
                        continue
                    
                    try:
                        with open(cmd_file, 'r', encoding='utf-8') as f:
                            command_data = json.load(f)
                        
                        # 执行命令
                        self._execute_control_command(command_data['command'])
                        
                        # 标记为已处理
                        processed_commands.add(cmd_file.name)
                        
                        # 删除命令文件
                        cmd_file.unlink()
                        
                    except Exception as e:
                        print(f"处理控制命令失败: {e}")
                
                # 清理过期的处理记录
                if len(processed_commands) > 100:
                    processed_commands.clear()
                
                time.sleep(0.05)  # 50ms检查间隔
                
        except Exception as e:
            print(f"监听控制命令失败: {e}")
    
    def _execute_control_command(self, command: Dict):
        """执行控制命令"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'mouse_move':
                self.remote_controller.move_mouse(
                    command['x'], command['y'], 
                    command.get('screen_size')
                )
            elif cmd_type == 'mouse_click':
                self.remote_controller.click_mouse(
                    command['x'], command['y'], 
                    command.get('button', 'left'),
                    command.get('screen_size')
                )
            elif cmd_type == 'mouse_scroll':
                self.remote_controller.scroll_mouse(
                    command['x'], command['y'],
                    command['delta'],
                    command.get('screen_size')
                )
            elif cmd_type == 'key_press':
                self.remote_controller.press_key(command['key'])
            elif cmd_type == 'type_text':
                self.remote_controller.type_text(command['text'])
            
        except Exception as e:
            print(f"执行控制命令失败: {e}")

def test_remote_control():
    """测试远程控制功能"""
    import tempfile
    
    print("📺 测试远程控制功能")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = RemoteControlManager(temp_dir)
        
        print("✅ 远程控制管理器创建成功")
        
        # 测试屏幕共享
        if manager.start_screen_sharing("test_user"):
            print("✅ 屏幕共享启动成功")
            time.sleep(2)  # 等待捕获一些屏幕
            
            screen_data = manager.get_latest_screen()
            if screen_data:
                print(f"✅ 获取屏幕截图成功，大小: {len(screen_data)} 字节")
            
            manager.stop_screen_sharing()
            print("✅ 屏幕共享停止成功")
        
        # 测试远程控制监听
        if manager.start_remote_control_listening("test_user"):
            print("✅ 远程控制监听启动成功")
            
            # 测试发送控制命令
            test_command = {
                'type': 'mouse_move',
                'x': 100,
                'y': 100
            }
            
            if manager.send_control_command(test_command):
                print("✅ 发送控制命令成功")
            
            time.sleep(1)
            manager.stop_remote_control_listening()
            print("✅ 远程控制监听停止成功")
        
        print("✅ 远程控制功能测试完成！")

if __name__ == "__main__":
    test_remote_control()