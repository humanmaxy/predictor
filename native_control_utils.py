#!/usr/bin/env python3
"""
原生控制工具类
使用系统原生方法替代PyAutoGUI，避免依赖问题
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
import subprocess
import platform

class NativeScreenCapture:
    """原生屏幕捕获类"""
    
    def __init__(self):
        self.capturing = False
        self.capture_thread = None
        self.capture_callback = None
        self.capture_interval = 0.1  # 100ms间隔
        self.image_quality = 70  # JPEG质量
        self.scale_factor = 0.5  # 缩放因子，减少传输数据量
        
        # 检测操作系统
        self.system = platform.system().lower()
        print(f"✅ 屏幕捕获初始化完成 (系统: {self.system})")
    
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
                # 使用PIL的ImageGrab进行屏幕截图
                try:
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
                        
                except Exception as e:
                    print(f"屏幕捕获失败: {e}")
                
                time.sleep(self.capture_interval)
                
        except Exception as e:
            print(f"屏幕捕获循环错误: {e}")
        finally:
            self.capturing = False

class NativeController:
    """原生控制类，使用系统命令替代PyAutoGUI"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.enabled = self._check_system_support()
        
        if self.enabled:
            print(f"✅ 原生控制器初始化成功 (系统: {self.system})")
        else:
            print(f"❌ 当前系统 ({self.system}) 暂不支持原生控制")
    
    def _check_system_support(self):
        """检查系统支持"""
        if self.system == 'windows':
            return self._check_windows_support()
        elif self.system == 'darwin':  # macOS
            return self._check_macos_support()
        elif self.system == 'linux':
            return self._check_linux_support()
        else:
            return False
    
    def _check_windows_support(self):
        """检查Windows支持"""
        try:
            import ctypes
            from ctypes import wintypes
            return True
        except ImportError:
            print("Windows ctypes不可用")
            return False
    
    def _check_macos_support(self):
        """检查macOS支持"""
        try:
            # 检查是否有osascript命令
            result = subprocess.run(['which', 'osascript'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_linux_support(self):
        """检查Linux支持"""
        try:
            # 检查是否有xdotool
            result = subprocess.run(['which', 'xdotool'], capture_output=True)
            if result.returncode == 0:
                return True
            
            # 检查是否有xinput
            result = subprocess.run(['which', 'xinput'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def get_screen_size(self):
        """获取屏幕尺寸"""
        try:
            if self.system == 'windows':
                return self._get_screen_size_windows()
            elif self.system == 'darwin':
                return self._get_screen_size_macos()
            elif self.system == 'linux':
                return self._get_screen_size_linux()
        except Exception as e:
            print(f"获取屏幕尺寸失败: {e}")
            return (1920, 1080)  # 默认值
    
    def _get_screen_size_windows(self):
        """Windows获取屏幕尺寸"""
        import ctypes
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return (width, height)
    
    def _get_screen_size_macos(self):
        """macOS获取屏幕尺寸"""
        try:
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "Finder" to get bounds of window of desktop'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # 解析输出，格式类似: "0, 0, 1920, 1080"
                bounds = result.stdout.strip().split(', ')
                width = int(bounds[2])
                height = int(bounds[3])
                return (width, height)
        except:
            pass
        return (1920, 1080)
    
    def _get_screen_size_linux(self):
        """Linux获取屏幕尺寸"""
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ' connected primary' in line or ' connected' in line:
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and '+' in part:
                                resolution = part.split('+')[0]
                                width, height = map(int, resolution.split('x'))
                                return (width, height)
        except:
            pass
        return (1920, 1080)
    
    # 鼠标操作已移除 - 仅保留键盘和命令行控制
    
    # 所有鼠标相关功能已移除
    
    def press_key(self, key: str):
        """按下按键"""
        if not self.enabled:
            return False
        
        try:
            if self.system == 'windows':
                return self._press_key_windows(key)
            elif self.system == 'darwin':
                return self._press_key_macos(key)
            elif self.system == 'linux':
                return self._press_key_linux(key)
                
        except Exception as e:
            print(f"按键失败: {e}")
            return False
    
    def _press_key_windows(self, key: str):
        """Windows按键"""
        import ctypes
        
        # 简单的按键映射
        key_codes = {
            'enter': 0x0D, 'return': 0x0D,
            'backspace': 0x08, 'tab': 0x09,
            'esc': 0x1B, 'escape': 0x1B,
            'space': 0x20, 'up': 0x26, 'down': 0x28,
            'left': 0x25, 'right': 0x27
        }
        
        if key.lower() in key_codes:
            vk_code = key_codes[key.lower()]
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)  # key down
            ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)  # key up
            return True
        elif len(key) == 1:
            # 单个字符
            vk_code = ord(key.upper())
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)
            return True
        
        return False
    
    def _press_key_macos(self, key: str):
        """macOS按键"""
        try:
            # 按键映射
            key_mapping = {
                'enter': 'return', 'return': 'return',
                'backspace': 'delete', 'tab': 'tab',
                'esc': 'escape', 'escape': 'escape',
                'space': 'space', 'up': 'up arrow',
                'down': 'down arrow', 'left': 'left arrow',
                'right': 'right arrow'
            }
            
            mapped_key = key_mapping.get(key.lower(), key)
            
            subprocess.run([
                'osascript', '-e', 
                f'tell application "System Events" to key code (key code of "{mapped_key}")'
            ], check=True)
            return True
        except:
            return False
    
    def _press_key_linux(self, key: str):
        """Linux按键"""
        try:
            subprocess.run(['xdotool', 'key', key], check=True)
            return True
        except:
            return False
    
    def type_text(self, text: str):
        """输入文本"""
        if not self.enabled:
            return False
        
        try:
            if self.system == 'windows':
                return self._type_text_windows(text)
            elif self.system == 'darwin':
                return self._type_text_macos(text)
            elif self.system == 'linux':
                return self._type_text_linux(text)
                
        except Exception as e:
            print(f"输入文本失败: {e}")
            return False
    
    def execute_command(self, command: str, shell: bool = True) -> Dict:
        """执行命令行命令"""
        if not self.enabled:
            return {"success": False, "error": "控制器未启用"}
        
        try:
            print(f"执行命令: {command}")
            result = subprocess.run(
                command if isinstance(command, list) else command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "命令执行超时",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def _type_text_windows(self, text: str):
        """Windows输入文本"""
        # 简单实现：逐字符输入
        for char in text:
            if not self.press_key(char):
                return False
            time.sleep(0.01)  # 小延迟
        return True
    
    def _type_text_macos(self, text: str):
        """macOS输入文本"""
        try:
            # 转义特殊字符
            escaped_text = text.replace('"', '\\"')
            subprocess.run([
                'osascript', '-e', 
                f'tell application "System Events" to keystroke "{escaped_text}"'
            ], check=True)
            return True
        except:
            return False
    
    def _type_text_linux(self, text: str):
        """Linux输入文本"""
        try:
            subprocess.run(['xdotool', 'type', text], check=True)
            return True
        except:
            return False

class NativeRemoteControlManager:
    """原生远程控制管理器"""
    
    def __init__(self, share_path: str):
        self.share_path = Path(share_path)
        self.remote_dir = self.share_path / "remote_control"
        self.screen_dir = self.remote_dir / "screens"
        self.control_dir = self.remote_dir / "controls"
        
        # 创建目录
        self._init_directories()
        
        # 组件
        self.screen_capture = NativeScreenCapture()
        self.controller = NativeController()
        
        # 状态
        self.is_sharing = False
        self.is_controlling = False
        self.user_id = None
        
        # 屏幕共享相关
        self.screen_file_counter = 0
        self.max_screen_files = 10
        
        # 控制命令监听
        self.control_monitor_thread = None
        self.monitoring = False
        
        print("✅ 原生远程控制管理器初始化完成")
    
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
                    "image_quality": 70,
                    "control_method": "native"
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
            print("远程控制监听已在运行")
            return False
        
        print(f"开始监听远程控制命令，用户ID: {user_id}")
        self.user_id = user_id
        self.is_controlling = True
        self.monitoring = True
        
        self.control_monitor_thread = threading.Thread(
            target=self._monitor_control_commands, daemon=True
        )
        self.control_monitor_thread.start()
        
        print("远程控制监听线程已启动")
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
            
            print(f"发送控制命令: {command['type']} -> {command_file.name}")
            
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
        print("开始监听控制命令循环...")
        try:
            processed_commands = set()
            loop_count = 0
            
            while self.monitoring:
                loop_count += 1
                command_files = list(self.control_dir.glob("cmd_*.json"))
                
                if loop_count % 200 == 0:  # 每10秒打印一次状态
                    print(f"监听循环运行中... 发现 {len(command_files)} 个命令文件")
                
                for cmd_file in command_files:
                    if cmd_file.name in processed_commands:
                        continue
                    
                    print(f"处理命令文件: {cmd_file.name}")
                    
                    try:
                        with open(cmd_file, 'r', encoding='utf-8') as f:
                            command_data = json.load(f)
                        
                        print(f"读取命令数据: {command_data['command']['type']}")
                        
                        # 执行命令
                        self._execute_control_command(command_data['command'])
                        
                        # 标记为已处理
                        processed_commands.add(cmd_file.name)
                        
                        # 删除命令文件
                        cmd_file.unlink()
                        print(f"命令文件已删除: {cmd_file.name}")
                        
                    except Exception as e:
                        print(f"处理控制命令失败: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 清理过期的处理记录
                if len(processed_commands) > 100:
                    processed_commands.clear()
                    print("清理过期的处理记录")
                
                time.sleep(0.05)  # 50ms检查间隔
                
        except Exception as e:
            print(f"监听控制命令失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("监听控制命令循环结束")
    
    def _execute_control_command(self, command: Dict):
        """执行控制命令"""
        try:
            cmd_type = command.get('type')
            print(f"执行控制命令: {cmd_type}")
            
            if cmd_type == 'mouse_move':
                result = self.controller.move_mouse(
                    command['x'], command['y'], 
                    command.get('screen_size')
                )
                print(f"鼠标移动结果: {'成功' if result else '失败'}")
            elif cmd_type == 'mouse_click':
                result = self.controller.click_mouse(
                    command['x'], command['y'], 
                    command.get('button', 'left'),
                    command.get('screen_size')
                )
                print(f"鼠标点击结果: {'成功' if result else '失败'} at ({command['x']}, {command['y']})")
            elif cmd_type == 'mouse_scroll':
                result = self.controller.scroll_mouse(
                    command['x'], command['y'],
                    command['delta'],
                    command.get('screen_size')
                )
                print(f"鼠标滚动结果: {'成功' if result else '失败'}")
            elif cmd_type == 'key_press':
                result = self.controller.press_key(command['key'])
                print(f"按键结果: {'成功' if result else '失败'} key={command['key']}")
            elif cmd_type == 'type_text':
                result = self.controller.type_text(command['text'])
                print(f"文本输入结果: {'成功' if result else '失败'} text={command['text']}")
            else:
                print(f"未知命令类型: {cmd_type}")
            
        except Exception as e:
            print(f"执行控制命令失败: {e}")
            import traceback
            traceback.print_exc()

def test_native_control():
    """测试原生控制功能"""
    import tempfile
    
    print("🧪 测试原生远程控制功能")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = NativeRemoteControlManager(temp_dir)
        
        print("✅ 原生远程控制管理器创建成功")
        
        # 测试控制器
        controller = manager.controller
        if controller.enabled:
            print("✅ 原生控制器可用")
            
            # 测试获取屏幕尺寸
            size = controller.get_screen_size()
            print(f"✅ 屏幕尺寸: {size[0]}x{size[1]}")
        else:
            print("❌ 原生控制器不可用")
        
        # 测试屏幕共享
        if manager.start_screen_sharing("test_user"):
            print("✅ 屏幕共享启动成功")
            time.sleep(2)
            
            screen_data = manager.get_latest_screen()
            if screen_data:
                print(f"✅ 获取屏幕截图成功，大小: {len(screen_data)} 字节")
            
            manager.stop_screen_sharing()
            print("✅ 屏幕共享停止成功")
        
        print("✅ 原生远程控制功能测试完成！")

if __name__ == "__main__":
    test_native_control()