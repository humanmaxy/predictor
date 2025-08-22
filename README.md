# 大图像选取裁剪工具（PyQt5）

## 功能
- 载入大图像并在 `QGraphicsView` 中预览
- 鼠标滚轮缩放，按住中键拖拽平移
- 左键拖动绘制矩形选区（半透明覆盖显示、细绿边框）
- 保存当前选区到文件（PNG/JPEG/BMP/TIFF/WEBP）

## 运行
系统已安装依赖（通过 apt：`python3-pyqt5`、`python3-pil`）。

- 启动：
```bash
python3 /workspace/main.py
```
- 也可在启动时直接带图像路径：
```bash
python3 /workspace/main.py /absolute/path/to/your_image.jpg
```

## 使用方法
- 打开：工具栏“打开”或 `Ctrl+O`
- 缩放：鼠标滚轮；`Ctrl+=` 放大、`Ctrl+-` 缩小、`Ctrl+0` 重置
- 平移：按住中键拖拽
- 适配窗口：`F`
- 选区：在图像上用左键按下拖动，松开结束
- 清除选区：工具栏“清除选区”或 `Esc`
- 保存选区：工具栏“保存选区”或 `Ctrl+S`

状态栏会显示当前选区的 x、y、w、h，方便精确截取。

## 备注
- 选区会自动裁剪到图像范围内，避免越界。
- 如需使用虚拟环境或 pip 安装，请自建 venv 并执行 `pip install -r requirements.txt`（本环境已通过 apt 安装系统包，可直接运行）。