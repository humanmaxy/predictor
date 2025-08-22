import sys
import os
import random
from pathlib import Path
from typing import Optional, List, Tuple

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage, QImageReader
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QToolBar,
    QAction,
    QMessageBox,
    QLabel,
    QLineEdit,
    QPushButton,
)


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


class ImageGraphicsView(QGraphicsView):
    selection_changed = pyqtSignal(QRectF)
    image_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._image_item: Optional[QGraphicsPixmapItem] = None
        self._selection_item: Optional[QGraphicsRectItem] = None
        self._is_selecting: bool = False
        self._selection_origin_scene: Optional[QPointF] = None

        self._is_panning: bool = False
        self._last_pan_pos = None

        self._current_zoom: float = 1.0

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(self.palette().brush(self.backgroundRole()))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setMouseTracking(True)

    # Public API
    def load_image(self, file_path: str) -> bool:
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        self._apply_pixmap(pixmap)
        return True

    def set_qimage(self, image: QImage) -> bool:
        if image.isNull():
            return False
        pixmap = QPixmap.fromImage(image)
        self._apply_pixmap(pixmap)
        return True

    def set_pixmap(self, pixmap: QPixmap) -> bool:
        if pixmap.isNull():
            return False
        self._apply_pixmap(pixmap)
        return True

    def has_image(self) -> bool:
        return self._image_item is not None

    def get_image_rect(self) -> QRectF:
        if not self._image_item:
            return QRectF()
        return QRectF(self._image_item.pixmap().rect())

    def clear_selection(self) -> None:
        if self._selection_item is not None:
            self._scene.removeItem(self._selection_item)
            self._selection_item = None
        self._is_selecting = False
        self._selection_origin_scene = None
        self.selection_changed.emit(QRectF())

    def get_selection_rect(self) -> QRectF:
        if self._selection_item is None:
            return QRectF()
        rect = self._selection_item.rect().normalized()
        image_rect = self.get_image_rect()
        return rect.intersected(image_rect)

    def fit_to_image(self) -> None:
        if not self._image_item:
            return
        # Temporarily reset transform so fitInView works from identity
        self.reset_transform_only()
        self.fitInView(self._image_item, Qt.KeepAspectRatio)
        self._current_zoom = 1.0

    def zoom_in(self) -> None:
        self.scale_view(1.25)

    def zoom_out(self) -> None:
        self.scale_view(0.8)

    def reset_zoom(self) -> None:
        self.reset_transform_only()
        self._current_zoom = 1.0

    # Event handlers
    def wheelEvent(self, event):
        if not self._image_item:
            return super().wheelEvent(event)
        angle = event.angleDelta().y()
        factor = 1.25 if angle > 0 else 0.8
        self.scale_view(factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._image_item:
            # Begin new selection
            self._is_selecting = True
            self._selection_origin_scene = self.mapToScene(event.pos())
            if self._selection_item is not None:
                self._scene.removeItem(self._selection_item)
                self._selection_item = None
            self._selection_item = QGraphicsRectItem()
            self._selection_item.setZValue(10)
            pen = QPen(QColor(0, 180, 0))
            pen.setWidthF(1.5)
            pen.setCosmetic(True)  # Keep constant width regardless of zoom
            self._selection_item.setPen(pen)
            self._selection_item.setBrush(QColor(0, 200, 0, 60))
            self._scene.addItem(self._selection_item)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning and self._last_pan_pos is not None:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        if self._is_selecting and self._selection_origin_scene is not None and self._selection_item is not None:
            current_scene = self.mapToScene(event.pos())
            rect = QRectF(self._selection_origin_scene, current_scene).normalized()
            rect = rect.intersected(self.get_image_rect())
            self._selection_item.setRect(rect)
            self.selection_changed.emit(rect)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._is_panning:
            self._is_panning = False
            self._last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._is_selecting:
            self._is_selecting = False
            if self._selection_item is not None:
                rect = self._selection_item.rect().normalized()
                if rect.width() < 2 or rect.height() < 2:
                    self.clear_selection()
                else:
                    self.selection_changed.emit(self.get_selection_rect())
            event.accept()
            return

        super().mouseReleaseEvent(event)

    # Helpers
    def reset_transform_only(self) -> None:
        self.setTransform(self.transform().fromScale(1.0, 1.0).inverted()[0])

    def scale_view(self, factor: float) -> None:
        if not self._image_item:
            return
        self.scale(factor, factor)
        self._current_zoom *= factor

    def _apply_pixmap(self, pixmap: QPixmap) -> None:
        self._scene.clear()
        self._image_item = QGraphicsPixmapItem(pixmap)
        self._image_item.setZValue(0)
        self._scene.addItem(self._image_item)
        self._scene.setSceneRect(QRectF(pixmap.rect()))

        self._selection_item = None
        self._is_selecting = False
        self._selection_origin_scene = None

        self.reset_zoom()
        self.fit_to_image()
        self.image_changed.emit(True)
        self.selection_changed.emit(QRectF())


class ImageLoaderWorker(QThread):
    loaded = pyqtSignal(QImage, str)
    failed = pyqtSignal(str, str)  # (path, error)

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def run(self):
        reader = QImageReader(self._path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            self.failed.emit(self._path, reader.errorString() or "读取失败")
        else:
            self.loaded.emit(image, self._path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大图像预览与选区裁剪")
        self.resize(1280, 840)

        self.view = ImageGraphicsView(self)
        self.setCentralWidget(self.view)

        self._status_label = QLabel("")
        self.statusBar().addPermanentWidget(self._status_label)

        self._create_actions()
        self._create_toolbar()
        self._connect_signals()

        self.image_paths: List[str] = []
        self.current_index: int = -1
        self.current_path: str = ""

        self._loader: Optional[ImageLoaderWorker] = None
        self._pending_path: str = ""

        self._update_action_states()

    def _create_actions(self) -> None:
        self.open_act = QAction("打开", self)
        self.open_act.setShortcut("Ctrl+O")
        self.open_act.triggered.connect(self.on_open)

        self.save_sel_act = QAction("保存选区", self)
        self.save_sel_act.setShortcut("Ctrl+S")
        self.save_sel_act.triggered.connect(self.on_save_selection)

        self.clear_sel_act = QAction("清除选区", self)
        self.clear_sel_act.setShortcut("Esc")
        self.clear_sel_act.triggered.connect(self.on_clear_selection)

        self.fit_act = QAction("适配窗口", self)
        self.fit_act.setShortcut("F")
        self.fit_act.triggered.connect(self.view.fit_to_image)

        self.zoom_in_act = QAction("放大", self)
        self.zoom_in_act.setShortcut("Ctrl+=")
        self.zoom_in_act.triggered.connect(self.view.zoom_in)

        self.zoom_out_act = QAction("缩小", self)
        self.zoom_out_act.setShortcut("Ctrl+-")
        self.zoom_out_act.triggered.connect(self.view.zoom_out)

        self.zoom_reset_act = QAction("重置缩放", self)
        self.zoom_reset_act.setShortcut("Ctrl+0")
        self.zoom_reset_act.triggered.connect(self.view.reset_zoom)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("工具")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self.open_act)
        toolbar.addSeparator()
        toolbar.addAction(self.save_sel_act)
        toolbar.addAction(self.clear_sel_act)
        toolbar.addSeparator()
        toolbar.addAction(self.fit_act)
        toolbar.addAction(self.zoom_in_act)
        toolbar.addAction(self.zoom_out_act)
        toolbar.addAction(self.zoom_reset_act)

        # Path input to open by typing
        toolbar.addSeparator()
        self.path_edit = QLineEdit(self)
        self.path_edit.setPlaceholderText("输入图像文件路径后按回车")
        self.path_edit.returnPressed.connect(self.on_open_from_edit)
        self.path_edit.setFixedWidth(420)
        toolbar.addWidget(QLabel(" 路径:"))
        toolbar.addWidget(self.path_edit)

        # Three quick-save directories + buttons
        toolbar.addSeparator()
        self.dir1_edit = QLineEdit(self)
        self.dir1_edit.setPlaceholderText("保存目录1")
        self.dir1_edit.setFixedWidth(220)
        self.save1_btn = QPushButton("保存到路径1", self)
        self.save1_btn.clicked.connect(lambda: self.on_save_to_dir(self.dir1_edit.text()))

        self.dir2_edit = QLineEdit(self)
        self.dir2_edit.setPlaceholderText("保存目录2")
        self.dir2_edit.setFixedWidth(220)
        self.save2_btn = QPushButton("保存到路径2", self)
        self.save2_btn.clicked.connect(lambda: self.on_save_to_dir(self.dir2_edit.text()))

        self.dir3_edit = QLineEdit(self)
        self.dir3_edit.setPlaceholderText("保存目录3")
        self.dir3_edit.setFixedWidth(220)
        self.save3_btn = QPushButton("保存到路径3", self)
        self.save3_btn.clicked.connect(lambda: self.on_save_to_dir(self.dir3_edit.text()))

        toolbar.addWidget(QLabel("  快速保存:"))
        toolbar.addWidget(self.dir1_edit)
        toolbar.addWidget(self.save1_btn)
        toolbar.addWidget(self.dir2_edit)
        toolbar.addWidget(self.save2_btn)
        toolbar.addWidget(self.dir3_edit)
        toolbar.addWidget(self.save3_btn)

    def _connect_signals(self) -> None:
        self.view.selection_changed.connect(self.on_selection_changed)
        self.view.image_changed.connect(self.on_image_changed)

    def _update_action_states(self) -> None:
        has_image = self.view.has_image()
        sel = self.view.get_selection_rect()
        has_sel = has_image and not sel.isEmpty() and sel.width() >= 1 and sel.height() >= 1
        self.save_sel_act.setEnabled(has_sel)
        self.clear_sel_act.setEnabled(has_image and (self.view._selection_item is not None))
        self.fit_act.setEnabled(has_image)
        self.zoom_in_act.setEnabled(has_image)
        self.zoom_out_act.setEnabled(has_image)
        self.zoom_reset_act.setEnabled(has_image)

        can_quicksave1 = has_sel and bool(self.dir1_edit.text().strip())
        can_quicksave2 = has_sel and bool(self.dir2_edit.text().strip())
        can_quicksave3 = has_sel and bool(self.dir3_edit.text().strip())
        self.save1_btn.setEnabled(can_quicksave1)
        self.save2_btn.setEnabled(can_quicksave2)
        self.save3_btn.setEnabled(can_quicksave3)

    # Navigation helpers
    def _collect_images_in_dir(self, dir_path: Path) -> List[str]:
        try:
            items = sorted(dir_path.iterdir())
        except Exception:
            return []
        results: List[str] = []
        for p in items:
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                results.append(str(p))
        return results

    def _set_current_path_and_list(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            return
        dir_path = p.parent
        self.image_paths = self._collect_images_in_dir(dir_path)
        try:
            self.current_index = self.image_paths.index(str(p))
        except ValueError:
            # 若未列出（大小写或链接问题），插入到列表
            self.image_paths.append(str(p))
            self.image_paths.sort()
            self.current_index = self.image_paths.index(str(p))
        self.current_path = str(p)
        self.path_edit.setText(self.current_path)

    def _navigate(self, step: int) -> None:
        if not self.image_paths:
            return
        if self.current_index < 0:
            return
        new_index = (self.current_index + step) % len(self.image_paths)
        self.open_image(self.image_paths[new_index])

    # Open/Load operations
    def open_image(self, path: str) -> None:
        self._set_current_path_and_list(path)
        self._start_async_load(self.current_path)

    def _start_async_load(self, path: str) -> None:
        # Stop previous loader if running (let it finish silently; we guard by path match)
        self._pending_path = path
        if self._loader is not None and self._loader.isRunning():
            # Let the previous loader finish; we'll ignore its result if outdated
            pass
        self.statusBar().showMessage("加载中...")
        loader = ImageLoaderWorker(path)
        loader.loaded.connect(self._on_loaded)
        loader.failed.connect(self._on_failed)
        self._loader = loader
        loader.start()

    def _on_loaded(self, image: QImage, path: str) -> None:
        if path != self._pending_path:
            return
        self.view.set_qimage(image)
        self.current_path = path
        try:
            self.current_index = self.image_paths.index(path)
        except ValueError:
            pass
        self.setWindowTitle(f"大图像预览与选区裁剪 - {Path(path).name}")
        self.statusBar().showMessage("已加载图像。", 1500)
        self._update_action_states()

    def _on_failed(self, path: str, error: str) -> None:
        if path != self._pending_path:
            return
        QMessageBox.warning(self, "打开失败", f"无法打开该图像文件。\n{error}")
        self.statusBar().clearMessage()

    # Slots
    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像文件",
            "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;所有文件 (*.*)",
        )
        if not path:
            return
        self.open_image(path)

    def on_open_from_edit(self):
        text = self.path_edit.text().strip()
        if not text:
            return
        self.open_image(text)

    def on_save_selection(self):
        if not self.view.has_image():
            return
        rect = self.view.get_selection_rect()
        if rect.isEmpty():
            QMessageBox.information(self, "无选区", "请先在图像上拖动选择一个区域。")
            return

        default_name, default_dir, default_ext, initial_filter = self._default_save_info()
        filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tif *.tiff);;WEBP (*.webp)"
        initial_path = str(default_dir / default_name)
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存裁剪图像",
            initial_path,
            filters,
            initial_filter,
        )
        if not target_path:
            return
        save_path = self._ensure_extension(Path(target_path), default_ext)
        self._save_crop_to_path(save_path)

    def on_save_to_dir(self, dir_path_text: str):
        if not self.view.has_image():
            return
        rect = self.view.get_selection_rect()
        if rect.isEmpty():
            QMessageBox.information(self, "无选区", "请先在图像上拖动选择一个区域。")
            return
        dir_path = Path(dir_path_text.strip())
        if not str(dir_path):
            QMessageBox.information(self, "无效目录", "请先在对应输入框中填写保存目录。")
            return
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "目录错误", f"无法创建目录：{e}")
            return
        default_name, _, default_ext, _ = self._default_save_info()
        save_path = dir_path / default_name
        save_path = self._ensure_extension(save_path, default_ext)
        ok = self._save_crop_to_path(save_path)
        if ok:
            self.statusBar().showMessage(f"已保存到：{save_path}", 2000)

    def _default_save_info(self) -> Tuple[str, Path, str, str]:
        p = Path(self.current_path) if self.current_path else None
        base = (p.stem if p else "crop")
        ext = (p.suffix.lower() if p and p.suffix.lower() in SUPPORTED_EXTS else ".png")
        rand = random.randint(100000, 999999)
        name = f"{base}_{rand}{ext}"
        directory = (p.parent if p else Path.home())
        # initial filter based on ext
        if ext == ".png":
            init_filter = "PNG (*.png)"
        elif ext in {".jpg", ".jpeg"}:
            init_filter = "JPEG (*.jpg *.jpeg)"
        elif ext == ".bmp":
            init_filter = "BMP (*.bmp)"
        elif ext in {".tif", ".tiff"}:
            init_filter = "TIFF (*.tif *.tiff)"
        elif ext == ".webp":
            init_filter = "WEBP (*.webp)"
        else:
            init_filter = "PNG (*.png)"
        return name, directory, ext, init_filter

    def _ensure_extension(self, path: Path, ext: str) -> Path:
        if not path.suffix:
            return path.with_suffix(ext)
        return path

    def _save_crop_to_path(self, path: Path) -> bool:
        rect = self.view.get_selection_rect()
        pixmap: QPixmap = self.view._image_item.pixmap()  # type: ignore
        crop = pixmap.copy(rect.toRect())
        if crop.isNull():
            QMessageBox.warning(self, "保存失败", "裁剪区域无效或超出范围。")
            return False
        ok = crop.save(str(path))
        if not ok:
            QMessageBox.warning(self, "保存失败", "无法写入目标文件。")
        return ok

    def on_clear_selection(self):
        self.view.clear_selection()

    def on_selection_changed(self, rect: QRectF):
        if rect.isEmpty():
            self._status_label.setText("提示：左键拖动绘制选区；中键拖拽平移；滚轮缩放；F 适配窗口；左右键切换图像。")
        else:
            self._status_label.setText(
                f"选区：x={int(rect.x())}, y={int(rect.y())}, w={int(rect.width())}, h={int(rect.height())}"
            )
        self._update_action_states()

    def on_image_changed(self, has_image: bool):
        if has_image:
            self.statusBar().showMessage("已加载图像。", 1500)
        self._update_action_states()

    # Keyboard navigation
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self._navigate(1)
            event.accept()
            return
        if event.key() == Qt.Key_Left:
            self._navigate(-1)
            event.accept()
            return
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    # Support opening image via CLI arg
    if len(sys.argv) > 1:
        win.open_image(sys.argv[1])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()