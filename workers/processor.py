from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QEventLoop
from PyQt6.QtWidgets import QMessageBox

from core.models import ProcessingResult
from core.pipeline import ProcessingPipeline
from core.rename_engine import RenameEngine
from core.clustering import ClusteringEngine
from core.fileops import FileOperations
from utils.constants import HASH_ALGORITHMS


class ProcessorWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished_result = pyqtSignal(object)  # ProcessingResult
    error = pyqtSignal(str)
    duplicate_found = pyqtSignal(str)   # dest_path, main thread should show dialog
    dup_registry_found = pyqtSignal(list) # list of file paths that are duplicates in registry

    _duplicate_choice: str | None = None  # None = skip, "overwrite" = overwrite, "rename" = rename
    _duplicate_loop: QEventLoop | None = None
    _registry_continue: bool = False

    def __init__(
        self,
        source: str,
        dest: str,
        project_code: str,
        sub_topic: str,
        hash_display_name: str = "SHA-256",
        auto_cluster: bool = True,
        cluster_time_sec: float = 3.0,
        selected_files: list[str] | None = None,
        write_exif: bool = False,
        detect_duplicates: bool = False,
    ):
        super().__init__()
        self.source = Path(source)
        self.dest = Path(dest)
        self.project_code = project_code
        self.sub_topic = sub_topic
        self.hash_algorithm = HASH_ALGORITHMS.get(hash_display_name)
        self.auto_cluster = auto_cluster
        self.cluster_time_sec = cluster_time_sec
        self.selected_files = [Path(f) for f in selected_files] if selected_files else None
        self.write_exif = write_exif
        self.detect_duplicates = detect_duplicates

    def set_duplicate_choice(self, choice: str | None):
        self._duplicate_choice = choice
        if self._duplicate_loop is not None:
            self._duplicate_loop.quit()

    def set_registry_continue(self, continue_import: bool):
        self._registry_continue = continue_import
        if self._duplicate_loop is not None:
            self._duplicate_loop.quit()

    def cancel(self):
        if self._duplicate_loop is not None:
            self._duplicate_loop.quit()
        self.set_duplicate_choice(None)
        self.set_registry_continue(False)

    def run(self):
        try:
            rename_engine = RenameEngine(self.project_code, self.sub_topic)
            clustering_engine = ClusteringEngine(self.cluster_time_sec)
            file_ops = FileOperations()

            pipeline = ProcessingPipeline(
                source=self.source,
                dest=self.dest,
                project_code=self.project_code,
                sub_topic=self.sub_topic,
                rename_engine=rename_engine,
                clustering_engine=clustering_engine,
                file_ops=file_ops,
                hash_algorithm=self.hash_algorithm,
                auto_cluster=self.auto_cluster,
                selected_files=self.selected_files,
                write_exif=self.write_exif,
                detect_duplicates=self.detect_duplicates,
            )

            result = pipeline.execute(
                progress_callback=self._on_progress,
                log_callback=self._on_log,
                duplicate_callback=self._on_duplicate,
                registry_callback=self._on_registry_check,
            )
            self.finished_result.emit(result)

        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current: int, total: int):
        self.progress.emit(current, total)

    def _on_log(self, message: str):
        self.log.emit(message)

    def _on_duplicate(self, dest_path: str) -> str | None:
        self._duplicate_choice = None
        self._duplicate_loop = QEventLoop()

        # Emit signal to main thread to show dialog
        self.duplicate_found.emit(dest_path)

        # Block this worker thread until main thread responds
        self._duplicate_loop.exec()

        choice = self._duplicate_choice
        self._duplicate_loop = None
        self._duplicate_choice = None

        if choice == "overwrite":
            return None  # pipeline interprets None stem as "proceed with original name"
        elif choice == "rename":
            # Return a new stem with _dup suffix
            from pathlib import Path
            p = Path(dest_path)
            return p.stem + "_dup1"
        else:
            return "__SKIP__"

    def _on_registry_check(self, dup_files: list[str]) -> bool:
        self._registry_continue = False
        self._duplicate_loop = QEventLoop()

        # Emit signal to main thread to show dialog
        self.dup_registry_found.emit(dup_files)

        # Block this worker thread until main thread responds
        self._duplicate_loop.exec()

        result = self._registry_continue
        self._duplicate_loop = None
        return result
