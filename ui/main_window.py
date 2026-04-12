from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QFormLayout, QCheckBox, QDoubleSpinBox, QComboBox,
    QTextEdit, QProgressBar, QStatusBar, QFileDialog, QMessageBox,
    QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.style import get_app_stylesheet
from ui.preview_dialog import ImportPreviewDialog
from workers.processor import ProcessorWorker
from utils.validators import validate_inputs
from utils.constants import HASH_ALGORITHMS
from utils.i18n import get_text, set_language, get_language, LANGUAGES


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: ProcessorWorker | None = None
        self._pending_duplicate_path: str | None = None
        self._duplicate_dialog_loop = None
        self._selected_source_files: list[str] = []  # files selected via preview dialog
        self._setup_ui()
        self._connect_signals()
        self._retranslate_ui()

    # ── UI Setup ──

    def _setup_ui(self):
        self.setWindowTitle("AssetRefactor")
        self.resize(900, 700)
        self.setStyleSheet(get_app_stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title_label = QLabel("AssetRefactor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Source & Destination
        self.sd_group = QGroupBox("Source & Destination")
        sd_layout = QVBoxLayout(self.sd_group)

        source_row = QHBoxLayout()
        self._src_label = QLabel("Source:")
        source_row.addWidget(self._src_label)
        self.source_edit = QLineEdit()
        self.source_edit.setReadOnly(True)
        source_row.addWidget(self.source_edit)
        self.source_btn = QPushButton("Browse...")
        source_row.addWidget(self.source_btn)
        self.preview_btn = QPushButton("Preview...")
        self.preview_btn.setEnabled(False)
        source_row.addWidget(self.preview_btn)
        sd_layout.addLayout(source_row)

        dest_row = QHBoxLayout()
        self._dest_label = QLabel("Destination:")
        dest_row.addWidget(self._dest_label)
        self.dest_edit = QLineEdit()
        self.dest_edit.setReadOnly(True)
        dest_row.addWidget(self.dest_edit)
        self.dest_btn = QPushButton("Browse...")
        dest_row.addWidget(self.dest_btn)
        sd_layout.addLayout(dest_row)
        main_layout.addWidget(self.sd_group)

        # Project Info
        self.pi_group = QGroupBox("Project Info")
        pi_layout = QFormLayout(self.pi_group)
        self.project_code_edit = QLineEdit()
        self._pc_label = QLabel("Project Code:")
        pi_layout.addRow(self._pc_label, self.project_code_edit)
        self.sub_topic_edit = QLineEdit()
        self._st_label = QLabel("Sub Topic:")
        pi_layout.addRow(self._st_label, self.sub_topic_edit)
        main_layout.addWidget(self.pi_group)

        # Options
        self.opt_group = QGroupBox("Options")
        opt_layout = QVBoxLayout(self.opt_group)

        # Row 1: auto-cluster + time interval + hash + language
        opt_row1 = QHBoxLayout()
        self.cluster_check = QCheckBox("Auto-cluster scattered files")
        self.cluster_check.setChecked(True)
        opt_row1.addWidget(self.cluster_check)

        opt_row1.addWidget(QLabel("Time interval (sec):"))
        self.cluster_time_spin = QDoubleSpinBox()
        self.cluster_time_spin.setRange(0.5, 60.0)
        self.cluster_time_spin.setValue(3.0)
        self.cluster_time_spin.setDecimals(1)
        opt_row1.addWidget(self.cluster_time_spin)

        opt_row1.addStretch()

        opt_row1.addWidget(QLabel("Hash:"))
        self.hash_combo = QComboBox()
        self.hash_combo.addItems(["SHA-256", "MD5", "不校验"])
        self.hash_combo.setCurrentText("SHA-256")
        opt_row1.addWidget(self.hash_combo)

        opt_row1.addSpacing(16)
        opt_row1.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(LANGUAGES.values()))
        self.lang_combo.setCurrentText(LANGUAGES.get(get_language(), "中文"))
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        opt_row1.addWidget(self.lang_combo)
        opt_layout.addLayout(opt_row1)

        # Row 2: EXIF writing + duplicate detection
        opt_row2 = QHBoxLayout()
        self.write_exif_check = QCheckBox("Write project info to file EXIF metadata")
        opt_row2.addWidget(self.write_exif_check)

        self.detect_duplicates_check = QCheckBox("Detect duplicate files (previously imported)")
        opt_row2.addWidget(self.detect_duplicates_check)

        opt_row2.addStretch()
        opt_layout.addLayout(opt_row2)

        main_layout.addWidget(self.opt_group)

        # Log
        self.log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(self.log_group)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)
        main_layout.addWidget(self.log_group)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary")
        btn_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel")
        self.cancel_btn.hide()
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        # Status Bar / MIT License
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.license_label = QLabel("MIT License")
        self.license_label.setObjectName("license")
        status_bar.addPermanentWidget(self.license_label)

    def _retranslate_ui(self):
        """Update all user-visible strings to the current language."""
        # Group boxes
        self.sd_group.setTitle(get_text("source_dest"))
        self.pi_group.setTitle(get_text("project_info"))
        self.opt_group.setTitle(get_text("options"))
        self.log_group.setTitle(get_text("log"))

        # Labels
        self._src_label.setText(get_text("source_label"))
        self._dest_label.setText(get_text("dest_label"))
        self._pc_label.setText(get_text("project_code_label"))
        self._st_label.setText(get_text("sub_topic_label"))

        # Buttons
        self.source_btn.setText(get_text("browse"))
        self.dest_btn.setText(get_text("browse"))
        self.preview_btn.setText(get_text("preview"))
        self.start_btn.setText(get_text("start"))
        self.cancel_btn.setText(get_text("cancel"))

        # Checkboxes
        self.cluster_check.setText(get_text("auto_cluster"))

        # Options row labels
        # Time interval label needs to be found
        for i in range(self.opt_group.layout().count()):
            item = self.opt_group.layout().itemAt(i)
            if item and item.layout():
                for j in range(item.layout().count()):
                    sub = item.layout().itemAt(j)
                    if sub and isinstance(sub.widget(), QLabel):
                        lbl = sub.widget()
                        if "interval" in lbl.text().lower() or "时间" in lbl.text():
                            lbl.setText(get_text("time_interval"))
                        elif "hash" in lbl.text().lower() or "哈希" in lbl.text():
                            lbl.setText(get_text("hash_label"))
                        elif "language" in lbl.text().lower() or "语言" in lbl.text():
                            lbl.setText(get_text("language_label"))

        self.write_exif_check.setText(get_text("write_exif_label"))
        self.detect_duplicates_check.setText(get_text("detect_duplicates_label"))

        # Hash combo
        current_hash = self.hash_combo.currentText()
        self.hash_combo.clear()
        hash_items_en = ["SHA-256", "MD5"]
        hash_items = hash_items_en + [get_text("hash_no_verify")]
        self.hash_combo.addItems(hash_items)
        if current_hash in hash_items_en:
            self.hash_combo.setCurrentText(current_hash)
        else:
            self.hash_combo.setCurrentText(get_text("hash_no_verify"))

        # License
        self.license_label.setText(get_text("license"))

    # ── Signals ──

    def _connect_signals(self):
        self.source_btn.clicked.connect(self._browse_source)
        self.preview_btn.clicked.connect(self._open_preview)
        self.dest_btn.clicked.connect(self._browse_dest)
        self.start_btn.clicked.connect(self._on_start)
        self.cancel_btn.clicked.connect(self._on_cancel)

    def _on_language_changed(self, _index: int):
        lang_code = list(LANGUAGES.keys())[_index]
        set_language(lang_code)
        self._retranslate_ui()

    # ── Browse handlers ──

    def _browse_source(self):
        directory = QFileDialog.getExistingDirectory(self, get_text("select_source"))
        if directory:
            self.source_edit.setText(directory)
            self._selected_source_files = []
            self.preview_btn.setEnabled(True)
            self._open_preview()

    def _open_preview(self):
        source = self.source_edit.text()
        if not source:
            return
        dialog = ImportPreviewDialog(source, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._selected_source_files = dialog.selected_files
            if self._selected_source_files:
                self._log(get_text("select_files_log", count=len(self._selected_source_files)))
            else:
                self._log(get_text("no_files_selected"))

    def _browse_dest(self):
        directory = QFileDialog.getExistingDirectory(self, get_text("select_dest"))
        if directory:
            self.dest_edit.setText(directory)

    # ── Processing ──

    def _on_start(self):
        source = self.source_edit.text()
        dest = self.dest_edit.text()
        project_code = self.project_code_edit.text()
        sub_topic = self.sub_topic_edit.text()

        errors = validate_inputs(source, dest, project_code, sub_topic)
        if errors:
            QMessageBox.critical(self, get_text("validation_error"), "\n".join(errors))
            return

        self._set_ui_enabled(False)
        self.cancel_btn.show()
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.log_edit.clear()
        self._log(get_text("starting_log"))

        hash_display = self.hash_combo.currentText()
        selected = self._selected_source_files if self._selected_source_files else None
        self.worker = ProcessorWorker(
            source=source,
            dest=dest,
            project_code=project_code,
            sub_topic=sub_topic,
            hash_display_name=hash_display,
            auto_cluster=self.cluster_check.isChecked(),
            cluster_time_sec=self.cluster_time_spin.value(),
            selected_files=selected,
            write_exif=self.write_exif_check.isChecked(),
            detect_duplicates=self.detect_duplicates_check.isChecked(),
        )
        self.worker.log.connect(self._log)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_result.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.duplicate_found.connect(self._on_duplicate_found)
        self.worker.dup_registry_found.connect(self._on_dup_registry_found)
        self.worker.start()

    def _on_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self._log(get_text("cancelling_log"))

    def _on_progress(self, current: int, total: int):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

    def _on_finished(self, result):
        self._set_ui_enabled(True)
        self.cancel_btn.hide()
        self.progress_bar.hide()

        if result.errors:
            error_msgs = [f"{path}: {msg}" for path, msg in result.errors]
            QMessageBox.warning(
                self, get_text("completed_errors"),
                f"Processed: {result.processed}\nSkipped: {result.skipped}\nErrors: {len(result.errors)}\n\n"
                + "\n".join(error_msgs[:10]) + ("\n..." if len(result.errors) > 10 else "")
            )
        else:
            QMessageBox.information(
                self, get_text("completed_success"),
                f"Processed: {result.processed}\nSkipped: {result.skipped}"
            )

    def _on_error(self, error_msg: str):
        self._set_ui_enabled(True)
        self.cancel_btn.hide()
        self.progress_bar.hide()
        self._log(get_text("fatal_error") + f": {error_msg}")
        QMessageBox.critical(self, get_text("fatal_error"), error_msg)

    def _on_duplicate_found(self, dest_path: str):
        self._pending_duplicate_path = dest_path
        reply = QMessageBox.question(
            self, get_text("duplicate_found_title"),
            get_text("duplicate_found_msg", path=dest_path),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.worker.set_duplicate_choice("overwrite")
        elif reply == QMessageBox.StandardButton.No:
            self.worker.set_duplicate_choice("rename")
        else:
            self.worker.set_duplicate_choice(None)

    def _on_dup_registry_found(self, dup_files: list[str]):
        file_list = "\n".join(f"  - {Path(f).name}" for f in dup_files[:20])
        if len(dup_files) > 20:
            file_list += f"\n  ... and {len(dup_files) - 20} more"
        reply = QMessageBox.question(
            self, get_text("duplicate_detected_title"),
            get_text("duplicate_detected_msg", count=len(dup_files), files=file_list),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        from pathlib import Path
        if self.worker:
            self.worker.set_registry_continue(reply == QMessageBox.StandardButton.Yes)

    def _set_ui_enabled(self, enabled: bool):
        self.source_edit.setEnabled(enabled)
        self.source_btn.setEnabled(enabled)
        self.dest_edit.setEnabled(enabled)
        self.dest_btn.setEnabled(enabled)
        self.project_code_edit.setEnabled(enabled)
        self.sub_topic_edit.setEnabled(enabled)
        self.cluster_check.setEnabled(enabled)
        self.cluster_time_spin.setEnabled(enabled)
        self.hash_combo.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.write_exif_check.setEnabled(enabled)
        self.detect_duplicates_check.setEnabled(enabled)
        self.lang_combo.setEnabled(enabled)

    def _log(self, message: str):
        self.log_edit.append(message)