# Windows 系统安装和使用指南

## 问题说明
如果您遇到 "WinError 2 系统找不到指定的文件" 错误，这通常是因为：
1. Python 未正确安装或未添加到 PATH 环境变量
2. 缺少必要的依赖包 (websockets)
3. 虚拟环境未正确设置

## 安装步骤

### 1. 检查 Python 安装
确保您已安装 Python 3.8 或更高版本：
```cmd
python --version
```
如果命令不工作，请从 https://www.python.org/downloads/ 下载并安装 Python。

### 2. 自动安装（推荐）
双击运行 `setup_windows.bat` 文件，它会自动：
- 检查 Python 安装
- 创建虚拟环境
- 安装所需依赖包

### 3. 手动安装
如果自动安装失败，请手动执行以下命令：

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 启动服务器

### 方法 1: 使用批处理文件（推荐）
双击运行 `start_server.bat`

### 方法 2: 手动启动
```cmd
# 如果有虚拟环境
venv\Scripts\python.exe start_server.py

# 或者使用系统Python
python start_server.py
```

## 故障排除

### 如果仍然遇到 WinError 2 错误：

1. **检查 Python 安装**：
   - 确保 Python 已添加到 PATH 环境变量
   - 尝试重新安装 Python 并选择 "Add to PATH" 选项

2. **检查文件路径**：
   - 确保所有文件都在同一目录下
   - 避免使用包含中文或特殊字符的路径

3. **检查权限**：
   - 以管理员身份运行命令提示符
   - 确保对项目文件夹有读写权限

4. **查看详细错误信息**：
   - 启动器界面会显示详细的调试信息
   - 查看日志区域了解具体的错误原因

### 常见解决方案：

1. **重新安装 Python**：
   - 卸载现有 Python
   - 从官网下载最新版本
   - 安装时勾选 "Add Python to PATH"

2. **使用 Python Launcher**：
   如果安装了多个 Python 版本，尝试使用：
   ```cmd
   py -3 start_server.py
   ```

3. **检查虚拟环境**：
   ```cmd
   # 删除旧的虚拟环境
   rmdir /s venv
   
   # 重新创建
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 技术支持
如果问题仍然存在，请提供以下信息：
- Windows 版本
- Python 版本 (`python --version`)
- 完整的错误消息
- 启动器日志中的详细信息