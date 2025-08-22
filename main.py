import sys
from typing import Optional

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
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
)


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大图像预览与选区裁剪")
        self.resize(1200, 800)

        self.view = ImageGraphicsView(self)
        self.setCentralWidget(self.view)

        self._status_label = QLabel("")
        self.statusBar().addPermanentWidget(self._status_label)

        self._create_actions()
        self._create_toolbar()
        self._connect_signals()
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
        ok = self.view.load_image(path)
        if not ok:
            QMessageBox.warning(self, "打开失败", "无法打开该图像文件。")

    def on_save_selection(self):
        if not self.view.has_image():
            return
        rect = self.view.get_selection_rect()
        if rect.isEmpty():
            QMessageBox.information(self, "无选区", "请先在图像上拖动选择一个区域。")
            return

        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存裁剪图像",
            "crop.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tif *.tiff);;WEBP (*.webp)",
        )
        if not target_path:
            return

        pixmap: QPixmap = self.view._image_item.pixmap()  # type: ignore
        crop = pixmap.copy(rect.toRect())
        if crop.isNull():
            QMessageBox.warning(self, "保存失败", "裁剪区域无效或超出范围。")
            return
        ok = crop.save(target_path)
        if not ok:
            QMessageBox.warning(self, "保存失败", "无法写入目标文件。")

    def on_clear_selection(self):
        self.view.clear_selection()

    def on_selection_changed(self, rect: QRectF):
        if rect.isEmpty():
            self._status_label.setText("提示：左键拖动绘制选区；中键拖拽平移；滚轮缩放；F 适配窗口。")
        else:
            self._status_label.setText(
                f"选区：x={int(rect.x())}, y={int(rect.y())}, w={int(rect.width())}, h={int(rect.height())}"
            )
        self._update_action_states()

    def on_image_changed(self, has_image: bool):
        if has_image:
            self.statusBar().showMessage("已加载图像。", 3000)
        self._update_action_states()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    # Support opening image via CLI arg
    if len(sys.argv) > 1:
        win.view.load_image(sys.argv[1])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()