import sys
import os
import random
from pathlib import Path
from typing import Optional, List, Tuple

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QThread, QStringListModel
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
    QSplitter,
    QListView,
    QAbstractItemView,
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


class FolderScanWorker(QThread):
    scanned = pyqtSignal(list, str)  # (paths, root)

    def __init__(self, root_dir: str, max_depth: int = 3):
        super().__init__()
        self.root_dir = root_dir
        self.max_depth = max_depth

    def run(self):
        results: List[str] = []
        root = Path(self.root_dir)
        try:
            def scan_dir(path: Path, depth: int):
                try:
                    with os.scandir(path) as it:
                        for entry in it:
                            try:
                                if entry.is_dir(follow_symlinks=False):
                                    if depth < self.max_depth:
                                        scan_dir(Path(entry.path), depth + 1)
                                elif entry.is_file(follow_symlinks=False):
                                    ext = os.path.splitext(entry.name)[1].lower()
                                    if ext in SUPPORTED_EXTS:
                                        results.append(entry.path)
                            except PermissionError:
                                continue
                except Exception:
                    return
            scan_dir(root, 0)
            results.sort()
        except Exception:
            results = []
        self.scanned.emit(results, str(root))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大图像预览与选区裁剪")
        self.resize(1280, 840)

        # Central splitter: left list, right view
        self.view = ImageGraphicsView(self)
        self.list_view = QListView(self)
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_view.setUniformItemSizes(True)
        self.list_view.clicked.connect(self.on_list_clicked)
        self.model = QStringListModel(self)
        self.list_view.setModel(self.model)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.list_view)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 960])
        self.setCentralWidget(splitter)

        self._status_label = QLabel("")
        self.statusBar().addPermanentWidget(self._status_label)

        self._create_actions()
        self._create_toolbar()
        self._connect_signals()

        # State
        self.image_paths: List[str] = []
        self.display_names: List[str] = []
        self.current_index: int = -1
        self.current_path: str = ""
        self.root_dir: str = ""

        self._loader: Optional[ImageLoaderWorker] = None
        self._pending_path: str = ""
        self._scan_worker: Optional[FolderScanWorker] = None

        self._update_action_states()

    def _create_actions(self) -> None:
        self.open_act = QAction("打开文件夹", self)
        self.open_act.setShortcut("Ctrl+O")
        self.open_act.triggered.connect(self.on_open_folder)

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

        # Folder path input
        toolbar.addSeparator()
        self.path_edit = QLineEdit(self)
        self.path_edit.setPlaceholderText("输入文件夹路径后按回车")
        self.path_edit.returnPressed.connect(self.on_open_folder_from_edit)
        self.path_edit.setFixedWidth(420)
        toolbar.addWidget(QLabel(" 文件夹:"))
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
    def _collect_display_names(self, paths: List[str], root: str) -> List[str]:
        names: List[str] = []
        root_path = Path(root)
        for p in paths:
            try:
                rel = str(Path(p).relative_to(root_path))
            except Exception:
                rel = os.path.basename(p)
            names.append(rel)
        return names

    def _select_index(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.image_paths):
            return
        self.current_index = idx
        self.current_path = self.image_paths[idx]
        index = self.model.index(idx)
        self.list_view.setCurrentIndex(index)
        self.list_view.scrollTo(index)

    def _navigate(self, step: int) -> None:
        if not self.image_paths:
            return
        if self.current_index < 0:
            return
        new_index = (self.current_index + step) % len(self.image_paths)
        self._select_index(new_index)
        self.open_image(self.image_paths[new_index])

    # Folder operations
    def on_open_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if not dir_path:
            return
        self.open_folder(dir_path)

    def on_open_folder_from_edit(self):
        text = self.path_edit.text().strip()
        if not text:
            return
        self.open_folder(text)

    def open_folder(self, folder_path: str) -> None:
        p = Path(folder_path)
        if not p.exists() or not p.is_dir():
            QMessageBox.warning(self, "无效路径", "请输入有效的文件夹路径。")
            return
        self.root_dir = str(p)
        self.path_edit.setText(self.root_dir)
        self.statusBar().showMessage("扫描文件中...")
        self.model.setStringList([])
        self.image_paths = []
        self.display_names = []
        if self._scan_worker is not None and self._scan_worker.isRunning():
            # Let it finish; new scan will override when emits
            pass
        worker = FolderScanWorker(self.root_dir, max_depth=3)
        worker.scanned.connect(self._on_scanned)
        self._scan_worker = worker
        worker.start()

    def _on_scanned(self, paths: List[str], root: str) -> None:
        if root != self.root_dir:
            return
        self.image_paths = paths
        self.display_names = self._collect_display_names(paths, root)
        self.model.setStringList(self.display_names)
        self.statusBar().showMessage(f"已扫描 {len(paths)} 个图像。", 2000)
        if self.image_paths:
            self._select_index(0)
            self.open_image(self.image_paths[0])
        else:
            self.current_index = -1
            self.current_path = ""
        self._update_action_states()

    # Open/Load operations
    def open_image(self, path: str) -> None:
        # Start async load only; list state handled elsewhere
        self._pending_path = path
        if self._loader is not None and self._loader.isRunning():
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
        if 0 <= self.current_index < len(self.image_paths):
            self._select_index(self.current_index)
        self.setWindowTitle(f"大图像预览与选区裁剪 - {Path(path).name}")
        self.statusBar().showMessage("已加载图像。", 1500)
        self._update_action_states()

    def _on_failed(self, path: str, error: str) -> None:
        if path != self._pending_path:
            return
        QMessageBox.warning(self, "打开失败", f"无法打开该图像文件。\n{error}")
        self.statusBar().clearMessage()

    # List interactions
    def on_list_clicked(self, index):
        row = index.row()
        if 0 <= row < len(self.image_paths):
            self._select_index(row)
            self.open_image(self.image_paths[row])

    # Save / Selection
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

    # Support opening image or folder via CLI arg
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isdir(arg):
            win.open_folder(arg)
        else:
            # Open file: set folder then load file
            p = Path(arg)
            if p.exists():
                win.open_folder(str(p.parent))
                # when scanning done, it will auto open first; we try to open specific file once list ready
                # Quick path: if file exists, open directly now (list may update later and sync selection)
                win.open_image(str(p))

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()