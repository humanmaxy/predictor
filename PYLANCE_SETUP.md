# Pylance警告解决方案

## 问题说明

如果您在VS Code中看到以下Pylance警告：
```
Import "pyautogui" could not be resolved from source
```

这是因为Pylance无法找到PyAutoGUI模块的源码，通常有以下原因：

## 解决方案

### 方法1：自动环境设置（推荐）
```bash
python setup_environment.py
```
这个脚本会：
- 检查Python环境
- 自动安装缺失的依赖
- 测试PyAutoGUI导入
- 创建VS Code/Pylance配置文件
- 解决大小写问题

### 方法2：手动配置

#### 1. 确保PyAutoGUI已正确安装
```bash
# 检查安装状态
python -c "import pyautogui; print(pyautogui.__version__)"

# 如果失败，重新安装
pip uninstall PyAutoGUI pyautogui -y
pip install pyautogui
```

#### 2. 配置VS Code设置
创建或编辑 `.vscode/settings.json`：
```json
{
  "python.analysis.extraPaths": ["./stubs"],
  "python.analysis.stubPath": "./stubs",
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.typeCheckingMode": "basic",
  "pylance.insidersChannel": "off"
}
```

#### 3. 配置Pyright
创建或编辑 `pyrightconfig.json`：
```json
{
  "reportMissingModuleSource": "none",
  "reportMissingImports": "warning",
  "reportOptionalMemberAccess": "none",
  "pythonVersion": "3.7",
  "stubPath": "./stubs"
}
```

### 方法3：检查特定问题

#### 大小写问题
```bash
python check_pyautogui_case.py
```

#### Unicode编码问题（Windows）
```bash
python test_pyautogui_win.py
```

## 验证修复

运行以下命令验证修复是否成功：

```bash
# 测试导入
python -c "
try:
    import pyautogui
    print(f'成功: PyAutoGUI {pyautogui.__version__}')
    print(f'屏幕尺寸: {pyautogui.size()}')
except Exception as e:
    print(f'失败: {e}')
"

# 启动程序
python network_share_chat.py
```

## 常见问题

### Q: 为什么会有Pylance警告？
A: Pylance进行静态分析时无法找到PyAutoGUI的源码，这可能是因为：
- 包未正确安装
- 虚拟环境配置问题
- 大小写不匹配
- 动态导入方式

### Q: 警告是否影响功能？
A: 不影响。这只是编辑器的类型检查警告，程序运行时会正常工作。

### Q: 如何彻底解决？
A: 运行 `python setup_environment.py`，它会自动处理所有问题。

## 项目文件说明

- `pyrightconfig.json` - Pyright/Pylance配置
- `.vscode/settings.json` - VS Code设置
- `stubs/pyautogui/__init__.pyi` - PyAutoGUI类型提示文件
- `setup_environment.py` - 自动环境设置脚本

## 重启建议

完成配置后，建议：
1. 重启VS Code
2. 重新加载Python解释器
3. 清除Pylance缓存（Ctrl+Shift+P -> "Python: Clear Cache and Reload Window")