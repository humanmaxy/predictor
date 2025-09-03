#!/usr/bin/env python3
"""
原生远程控制GUI组件
使用系统原生方法，无需PyAutoGUI依赖
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk
import io

from native_control_utils import NativeRemoteControlManager

class NativeScreenShareWindow:
    """原生屏幕共享窗口"""
    
    def __init__(self, parent, remote_manager: NativeRemoteControlManager, user_id: str):
        self.parent = parent
        self.remote_manager = remote_manager
        self.user_id = user_id
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("屏幕共享 (原生控制)")
        self.window.geometry("800x600")
        self.window.minsize(400, 300)
        
        # 状态
        self.is_sharing = False
        self.is_viewing = False
        self.update_thread = None
        self.updating = False
        
        # 远程屏幕信息
        self.remote_screen_size = None
        self.current_image = None
        
        self._create_widgets()
        self._setup_events()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板 (原生控制)", padding=5)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 共享控制
        share_frame = ttk.Frame(control_frame)
        share_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(share_frame, text="屏幕共享:").pack(side=tk.LEFT)
        
        self.share_button = ttk.Button(share_frame, text="开始共享", command=self.toggle_sharing)
        self.share_button.pack(side=tk.LEFT, padx=(10, 0))
        
        self.share_status = ttk.Label(share_frame, text="未共享", foreground="gray")
        self.share_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # 查看控制
        view_frame = ttk.Frame(control_frame)
        view_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(view_frame, text="查看他人:").pack(side=tk.LEFT)
        
        self.view_button = ttk.Button(view_frame, text="开始查看", command=self.toggle_viewing)
        self.view_button.pack(side=tk.LEFT, padx=(10, 0))
        
        self.view_status = ttk.Label(view_frame, text="未查看", foreground="gray")
        self.view_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # 远程控制开关
        control_frame2 = ttk.Frame(control_frame)
        control_frame2.pack(fill=tk.X, pady=2)
        
        ttk.Label(control_frame2, text="远程控制:").pack(side=tk.LEFT)
        
        self.control_var = tk.BooleanVar()
        self.control_checkbox = ttk.Checkbutton(
            control_frame2, text="允许他人控制我的屏幕", 
            variable=self.control_var, command=self.toggle_remote_control
        )
        self.control_checkbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # 控制方法显示
        method_frame = ttk.Frame(control_frame)
        method_frame.pack(fill=tk.X, pady=2)
        
        controller_enabled = self.remote_manager.controller.enabled
        controller_system = self.remote_manager.controller.system
        
        if controller_enabled:
            method_text = f"✅ 原生控制可用 (系统: {controller_system})"
            method_color = "green"
        else:
            method_text = f"❌ 原生控制不可用 (系统: {controller_system})"
            method_color = "red"
        
        ttk.Label(method_frame, text="控制方法:", font=("Arial", 8)).pack(side=tk.LEFT)
        ttk.Label(method_frame, text=method_text, font=("Arial", 8), 
                 foreground=method_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # 屏幕显示区域
        screen_frame = ttk.LabelFrame(main_frame, text="屏幕显示", padding=5)
        screen_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        canvas_frame = ttk.Frame(screen_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='black')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(screen_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪 - 使用原生控制", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.fps_label = ttk.Label(status_frame, text="FPS: 0", relief=tk.SUNKEN, width=10)
        self.fps_label.pack(side=tk.RIGHT)
    
    def _setup_events(self):
        """设置事件绑定"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 鼠标和键盘事件（用于远程控制）
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<Button-3>", self.on_mouse_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Key>", self.on_key_press)
        self.canvas.focus_set()
    
    def toggle_sharing(self):
        """切换屏幕共享状态"""
        if not self.is_sharing:
            if self.remote_manager.start_screen_sharing(self.user_id):
                self.is_sharing = True
                self.share_button.config(text="停止共享")
                self.share_status.config(text="正在共享", foreground="green")
                self.update_status("屏幕共享已开始 (原生)")
            else:
                messagebox.showerror("错误", "无法启动屏幕共享")
        else:
            self.remote_manager.stop_screen_sharing()
            self.is_sharing = False
            self.share_button.config(text="开始共享")
            self.share_status.config(text="未共享", foreground="gray")
            self.update_status("屏幕共享已停止")
    
    def toggle_viewing(self):
        """切换查看他人屏幕状态"""
        if not self.is_viewing:
            self.is_viewing = True
            self.view_button.config(text="停止查看")
            self.view_status.config(text="正在查看", foreground="blue")
            self.start_screen_update()
            self.update_status("开始查看远程屏幕")
        else:
            self.is_viewing = False
            self.view_button.config(text="开始查看")
            self.view_status.config(text="未查看", foreground="gray")
            self.stop_screen_update()
            self.canvas.delete("all")
            self.update_status("停止查看远程屏幕")
    
    def toggle_remote_control(self):
        """切换远程控制权限"""
        if self.control_var.get():
            if self.remote_manager.start_remote_control_listening(self.user_id):
                self.update_status("已允许原生远程控制")
            else:
                self.control_var.set(False)
                messagebox.showerror("错误", "无法启动远程控制监听")
        else:
            self.remote_manager.stop_remote_control_listening()
            self.update_status("已禁止远程控制")
    
    def start_screen_update(self):
        """开始屏幕更新"""
        if self.updating:
            return
        
        self.updating = True
        self.update_thread = threading.Thread(target=self._screen_update_loop, daemon=True)
        self.update_thread.start()
    
    def stop_screen_update(self):
        """停止屏幕更新"""
        self.updating = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def _screen_update_loop(self):
        """屏幕更新循环"""
        fps_counter = 0
        last_fps_time = time.time()
        
        try:
            while self.updating and self.is_viewing:
                start_time = time.time()
                
                # 获取最新屏幕数据
                screen_data = self.remote_manager.get_latest_screen()
                if screen_data:
                    try:
                        # 解析图像
                        image = Image.open(io.BytesIO(screen_data))
                        self.remote_screen_size = image.size
                        
                        # 转换为Tkinter格式
                        photo = ImageTk.PhotoImage(image)
                        
                        # 在主线程中更新显示
                        self.window.after(0, lambda: self._update_canvas(photo, image.size))
                        
                        fps_counter += 1
                        
                    except Exception as e:
                        print(f"处理屏幕数据失败: {e}")
                
                # 计算FPS
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    self.window.after(0, lambda: self.fps_label.config(text=f"FPS: {fps_counter}"))
                    fps_counter = 0
                    last_fps_time = current_time
                
                # 控制帧率
                elapsed = time.time() - start_time
                sleep_time = max(0, 1/30 - elapsed)  # 30 FPS
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            print(f"屏幕更新循环错误: {e}")
        finally:
            self.updating = False
    
    def _update_canvas(self, photo, image_size):
        """更新画布显示"""
        try:
            self.canvas.delete("all")
            self.current_image = photo  # 保持引用
            
            # 在画布中央显示图像
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            
            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            print(f"更新画布失败: {e}")
    
    def on_mouse_click(self, event):
        """鼠标点击事件"""
        if not self.is_viewing or not self.remote_screen_size:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        command = {
            'type': 'mouse_click',
            'x': int(canvas_x),
            'y': int(canvas_y),
            'button': 'left',
            'screen_size': self.remote_screen_size
        }
        
        self.remote_manager.send_control_command(command)
    
    def on_mouse_right_click(self, event):
        """鼠标右键点击事件"""
        if not self.is_viewing or not self.remote_screen_size:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        command = {
            'type': 'mouse_click',
            'x': int(canvas_x),
            'y': int(canvas_y),
            'button': 'right',
            'screen_size': self.remote_screen_size
        }
        
        self.remote_manager.send_control_command(command)
    
    def on_mouse_move(self, event):
        """鼠标移动事件"""
        if not self.is_viewing or not self.remote_screen_size:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        command = {
            'type': 'mouse_move',
            'x': int(canvas_x),
            'y': int(canvas_y),
            'screen_size': self.remote_screen_size
        }
        
        self.remote_manager.send_control_command(command)
    
    def on_mouse_wheel(self, event):
        """鼠标滚轮事件"""
        if not self.is_viewing or not self.remote_screen_size:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        command = {
            'type': 'mouse_scroll',
            'x': int(canvas_x),
            'y': int(canvas_y),
            'delta': event.delta,
            'screen_size': self.remote_screen_size
        }
        
        self.remote_manager.send_control_command(command)
    
    def on_key_press(self, event):
        """按键事件"""
        if not self.is_viewing:
            return
        
        # 处理特殊按键
        key_map = {
            'Return': 'enter',
            'BackSpace': 'backspace',
            'Tab': 'tab',
            'Escape': 'esc',
            'Delete': 'delete',
            'Insert': 'insert',
            'Home': 'home',
            'End': 'end',
            'Page_Up': 'pageup',
            'Page_Down': 'pagedown',
            'Up': 'up',
            'Down': 'down',
            'Left': 'left',
            'Right': 'right',
            'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
            'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
            'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12'
        }
        
        key = event.keysym
        if key in key_map:
            command = {
                'type': 'key_press',
                'key': key_map[key]
            }
        elif len(key) == 1:
            # 普通字符
            command = {
                'type': 'type_text',
                'text': key
            }
        else:
            return
        
        self.remote_manager.send_control_command(command)
    
    def update_status(self, message: str):
        """更新状态栏"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"[{timestamp}] {message}")
    
    def on_closing(self):
        """窗口关闭事件"""
        # 停止所有活动
        if self.is_sharing:
            self.remote_manager.stop_screen_sharing()
        
        if self.is_viewing:
            self.stop_screen_update()
        
        if self.control_var.get():
            self.remote_manager.stop_remote_control_listening()
        
        self.window.destroy()

class NativeRemoteControlPanel:
    """原生远程控制面板（嵌入到主聊天窗口）"""
    
    def __init__(self, parent_frame, remote_manager: NativeRemoteControlManager, user_id: str):
        self.parent_frame = parent_frame
        self.remote_manager = remote_manager
        self.user_id = user_id
        
        # 屏幕共享窗口
        self.screen_window = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建远程控制面板"""
        # 远程控制框架
        self.remote_frame = ttk.LabelFrame(self.parent_frame, text="远程控制 (原生)", padding=5)
        self.remote_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(self.remote_frame)
        button_frame.pack(fill=tk.X)
        
        # 屏幕共享按钮
        self.screen_share_btn = ttk.Button(
            button_frame, text="📺 屏幕共享", 
            command=self.open_screen_share_window
        )
        self.screen_share_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态显示
        controller_enabled = self.remote_manager.controller.enabled
        if controller_enabled:
            status_text = f"原生控制就绪 ({self.remote_manager.controller.system})"
            status_color = "green"
        else:
            status_text = f"原生控制不可用 ({self.remote_manager.controller.system})"
            status_color = "red"
        
        self.status_var = tk.StringVar(value=status_text)
        self.status_label = ttk.Label(button_frame, textvariable=self.status_var, 
                                    font=("Arial", 8), foreground=status_color)
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 快速控制选项
        options_frame = ttk.Frame(self.remote_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 允许被控制
        self.allow_control_var = tk.BooleanVar()
        self.allow_control_cb = ttk.Checkbutton(
            options_frame, text="允许他人控制我的电脑 (原生)",
            variable=self.allow_control_var,
            command=self.toggle_allow_control
        )
        self.allow_control_cb.pack(side=tk.LEFT)
        
        # 自动共享屏幕
        self.auto_share_var = tk.BooleanVar()
        self.auto_share_cb = ttk.Checkbutton(
            options_frame, text="自动共享屏幕",
            variable=self.auto_share_var,
            command=self.toggle_auto_share
        )
        self.auto_share_cb.pack(side=tk.LEFT, padx=(20, 0))
        
        # 如果原生控制不可用，禁用控制选项
        if not controller_enabled:
            self.allow_control_cb.config(state='disabled')
            self.auto_share_cb.config(state='disabled')
    
    def open_screen_share_window(self):
        """打开屏幕共享窗口"""
        if self.screen_window is None or not self.screen_window.window.winfo_exists():
            self.screen_window = NativeScreenShareWindow(
                self.parent_frame.winfo_toplevel(), 
                self.remote_manager, 
                self.user_id
            )
        else:
            self.screen_window.window.lift()
            self.screen_window.window.focus_set()
    
    def toggle_allow_control(self):
        """切换允许控制状态"""
        if not self.remote_manager.controller.enabled:
            messagebox.showwarning("功能不可用", "当前系统不支持原生远程控制")
            self.allow_control_var.set(False)
            return
        
        if self.allow_control_var.get():
            if self.remote_manager.start_remote_control_listening(self.user_id):
                self.status_var.set("允许原生远程控制中...")
            else:
                self.allow_control_var.set(False)
                messagebox.showerror("错误", "无法启动远程控制监听")
        else:
            self.remote_manager.stop_remote_control_listening()
            controller_enabled = self.remote_manager.controller.enabled
            if controller_enabled:
                self.status_var.set(f"原生控制就绪 ({self.remote_manager.controller.system})")
    
    def toggle_auto_share(self):
        """切换自动共享状态"""
        if self.auto_share_var.get():
            if self.remote_manager.start_screen_sharing(self.user_id):
                self.status_var.set("自动共享屏幕中...")
            else:
                self.auto_share_var.set(False)
                messagebox.showerror("错误", "无法启动屏幕共享")
        else:
            self.remote_manager.stop_screen_sharing()
            if not self.allow_control_var.get():
                controller_enabled = self.remote_manager.controller.enabled
                if controller_enabled:
                    self.status_var.set(f"原生控制就绪 ({self.remote_manager.controller.system})")

def test_native_remote_control_gui():
    """测试原生远程控制GUI"""
    import tempfile
    
    root = tk.Tk()
    root.title("原生远程控制GUI测试")
    root.geometry("600x400")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        remote_manager = NativeRemoteControlManager(temp_dir)
        
        # 创建远程控制面板
        panel = NativeRemoteControlPanel(root, remote_manager, "test_user")
        
        root.mainloop()

if __name__ == "__main__":
    test_native_remote_control_gui()