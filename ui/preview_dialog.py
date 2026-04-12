from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont
from pathlib import Path
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from core.exiftool import ExifTool
from utils.constants import (
    ALL_SUPPORTED_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS,
    RAW_IMAGE_EXTENSIONS, STANDARD_IMAGE_EXTENSIONS,
)
from utils.i18n import get_text


def _generate_thumbnail(filepath: str, ext: str, exiftool: ExifTool) -> bytes | None:
    """Generate thumbnail bytes for any supported file type.

    Priority:
      1. rawpy extract_thumb() — fast embedded JPEG extraction (ARW/CR3/DNG)
      2. Pillow direct open (standard images: JPG/PNG/TIF/BMP)
      3. ExifTool embedded thumbnail (fallback if available)
      4. ffmpeg video frame extraction (MP4/MOV)
      5. None — caller shows text placeholder
    """
    # 1. rawpy for RAW files — extract embedded JPEG (milliseconds, not seconds)
    if ext in RAW_IMAGE_EXTENSIONS:
        try:
            import rawpy
            with rawpy.imread(filepath) as raw:
                try:
                    thumb = raw.extract_thumb()
                    # thumb.data is JPEG bytes — return directly
                    if thumb and thumb.data:
                        return bytes(thumb.data)
                except rawpy.LibRawNoThumbnailError:
                    pass  # No embedded thumbnail, fall through to postprocess
        except Exception:
            pass
        # Fallback to minimal postprocess if extract_thumb has no thumbnail
        try:
            import rawpy
            import io
            from PIL import Image as PILImage
            with rawpy.imread(filepath) as raw:
                rgb = raw.postprocess(
                    user_flip=0, no_auto_bright=True,
                    use_camera_wb=False, use_auto_wb=False,
                    half_size=True
                )
                img = PILImage.fromarray(rgb)
                img.thumbnail((128, 128))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                return buf.getvalue()
        except Exception:
            pass

    # 2. Pillow for standard image formats
    if ext in STANDARD_IMAGE_EXTENSIONS:
        try:
            from PIL import Image
            import io
            with Image.open(filepath) as img:
                img.thumbnail((128, 128))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                return buf.getvalue()
        except Exception:
            pass

    # 3. Try ExifTool embedded thumbnail (fallback for RAW if rawpy failed)
    if exiftool._cmd:
        thumb = exiftool.extract_thumbnail(Path(filepath))
        if thumb:
            return thumb

    # 4. ffmpeg for video thumbnail (first frame)
    if ext in VIDEO_EXTENSIONS:
        try:
            import subprocess
            proc = subprocess.run(
                ["ffmpeg", "-i", filepath, "-vf", "scale=128:-1", "-vframes", "1",
                 "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if proc.returncode == 0 and len(proc.stdout) > 100:
                return proc.stdout
        except Exception:
            pass

    return None


class ThumbnailLoadWorker(QThread):
    """Background worker to load thumbnails and metadata for the preview dialog."""
    file_ready = pyqtSignal(str, bytes, str, str, str, float, str)  # path, thumb_bytes, date_str, time_str, ext, epoch, rel_path
    scan_done = pyqtSignal(int)
    finished_loading = pyqtSignal()

    def __init__(self, source_dir: str):
        super().__init__()
        self.source_dir = Path(source_dir)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        all_files = []
        for p in self.source_dir.rglob("*"):
            if self._cancelled:
                return
            if p.is_file() and p.suffix.lower() in ALL_SUPPORTED_EXTENSIONS:
                all_files.append(p)

        if not all_files:
            self.scan_done.emit(0)
            self.finished_loading.emit()
            return

        self.scan_done.emit(len(all_files))

        exiftool = ExifTool()

        # Use ThreadPoolExecutor for parallel thumbnail generation
        # max_workers=6 is a good balance for CPU and SD card IO
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            for filepath in all_files:
                if self._cancelled:
                    break

                ext_lower = filepath.suffix.lower()
                if ext_lower == ".xmp":
                    continue

                # File system modification time
                mtime = filepath.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M:%S")

                # Compute relative path from source directory
                try:
                    rel_path = str(filepath.relative_to(self.source_dir).parent)
                    if rel_path == ".":
                        rel_path = ""
                except ValueError:
                    rel_path = ""

                # Define the processing task
                def task(fp=filepath, el=ext_lower, ds=date_str, ts=time_str, mt=mtime, rp=rel_path):
                    if self._cancelled:
                        return
                    thumb_bytes = _generate_thumbnail(str(fp), el, exiftool)
                    self.file_ready.emit(str(fp), thumb_bytes or b"", ds, ts, el, mt, rp)

                futures.append(executor.submit(task))

            # Wait for all tasks to complete or cancellation
            for future in futures:
                if self._cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                future.result()

        self.finished_loading.emit()


class ImportPreviewDialog(QDialog):
    """Dialog showing files in a source directory with thumbnails, timestamps,
    and checkable selection for import."""

    def __init__(self, source_dir: str, parent=None):
        super().__init__(parent)
        self.source_dir = source_dir
        self.selected_files: list[str] = []
        self._all_file_data: dict[str, dict] = {}
        self._thumbnail_worker: Optional[ThumbnailLoadWorker] = None

        self.setWindowTitle(get_text("preview_title", dir=source_dir))
        self.resize(1000, 650)
        self._build_ui()
        self._start_loading()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.info_label = QLabel(get_text("scanning"))
        self.info_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.info_label)

        btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton(get_text("select_all"))
        self.deselect_all_btn = QPushButton(get_text("deselect_all"))
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(self.select_all_btn)
        btn_row.addWidget(self.deselect_all_btn)
        btn_row.addStretch()

        self.selected_count_label = QLabel(get_text("selected_count", count=0, total=0))
        self.selected_count_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        btn_row.addWidget(self.selected_count_label)
        layout.addLayout(btn_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            get_text("col_select"),
            get_text("col_preview"),
            get_text("col_filename"),
            get_text("col_folder"),
            get_text("col_date"),
            get_text("col_time")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setIconSize(QSize(70, 70))
        self.table.verticalHeader().setDefaultSectionSize(78)
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(False)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        action_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton(get_text("cancel"))
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(ok_btn)
        action_row.addWidget(cancel_btn)
        layout.addLayout(action_row)

    def _start_loading(self):
        self._thumbnail_worker = ThumbnailLoadWorker(self.source_dir)
        self._thumbnail_worker.file_ready.connect(self._on_file_ready)
        self._thumbnail_worker.scan_done.connect(self._on_scan_done)
        self._thumbnail_worker.finished_loading.connect(self._on_loading_finished)
        self._thumbnail_worker.start()

    def _on_scan_done(self, total: int):
        self.info_label.setText(get_text("loading_meta", count=total))

    def _on_file_ready(self, filepath: str, thumb_bytes: bytes, date_str: str,
                       time_str: str, ext: str, epoch: float, rel_path: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._all_file_data[filepath] = {"row": row, "checked": True}

        check_widget = QWidget()
        check_layout = QHBoxLayout(check_widget)
        check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_layout.setContentsMargins(0, 0, 0, 0)
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(lambda state, fp=filepath: self._on_check_changed(fp, state))
        check_layout.addWidget(checkbox)
        self.table.setCellWidget(row, 0, check_widget)

        thumb_item = QTableWidgetItem()
        pixmap = None
        if thumb_bytes:
            qimg = QImage()
            qimg.loadFromData(thumb_bytes)
            if not qimg.isNull():
                pixmap = QPixmap.fromImage(qimg).scaled(
                    70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )

        if pixmap:
            thumb_item.setIcon(QIcon(pixmap))
        else:
            if ext in VIDEO_EXTENSIONS:
                thumb_item.setText(f"🎬 {get_text('label_video')}")
            else:
                thumb_item.setText(f"📷 {get_text('label_image')}")
            thumb_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table.setItem(row, 1, thumb_item)

        p = Path(filepath)
        name_item = QTableWidgetItem(f"{p.stem}{p.suffix}")
        if ext in VIDEO_EXTENSIONS:
            name_item.setToolTip(get_text("label_video"))
        self.table.setItem(row, 2, name_item)

        # Relative path column
        folder_item = QTableWidgetItem(rel_path)
        self.table.setItem(row, 3, folder_item)

        self.table.setItem(row, 4, QTableWidgetItem(date_str))
        self.table.setItem(row, 5, QTableWidgetItem(time_str))

        self._update_selected_count()

    def _on_check_changed(self, filepath: str, state: int):
        checked = state == Qt.CheckState.Checked.value
        self._all_file_data[filepath]["checked"] = checked
        self._update_selected_count()

    def _update_selected_count(self):
        count = sum(1 for v in self._all_file_data.values() if v.get("checked", False))
        total = len(self._all_file_data)
        self.selected_count_label.setText(get_text("selected_count", count=count, total=total))

    def _select_all(self):
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb:
                    cb.setChecked(True)

    def _deselect_all(self):
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb:
                    cb.setChecked(False)

    def _on_loading_finished(self):
        self.table.setUpdatesEnabled(True)
        self.info_label.setText(get_text("loaded", count=self.table.rowCount()))

    def _on_ok(self):
        self.selected_files = [
            fp for fp, data in self._all_file_data.items() if data.get("checked", False)
        ]
        self.accept()

    def reject(self):
        if self._thumbnail_worker and self._thumbnail_worker.isRunning():
            self._thumbnail_worker.cancel()
            self._thumbnail_worker.wait(2000)
        super().reject()

    def closeEvent(self, event):
        if self._thumbnail_worker and self._thumbnail_worker.isRunning():
            self._thumbnail_worker.cancel()
            self._thumbnail_worker.wait(2000)
        super().closeEvent(event)