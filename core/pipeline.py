from pathlib import Path
from datetime import datetime
from typing import Callable
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.models import Asset, AssetGroup, ProcessingResult, AssetType
from core.rename_engine import RenameEngine
from core.clustering import ClusteringEngine
from core.fileops import FileOperations
from core.file_registry import FileRegistry
from core.exiftool import ExifTool
from utils.constants import ALL_SUPPORTED_EXTENSIONS, RAW_IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, IMAGE_EXTENSIONS
from utils.i18n import get_text


def _scan_dir_fast(root: Path, extensions: set[str]) -> list[Path]:
    """Fast directory scan using os.scandir (5-10x faster than rglob on large dirs)."""
    result = []
    ext_lower = {e.lower() for e in extensions}
    stack = [str(root)]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        suffix = os.path.splitext(entry.name)[1].lower()
                        if suffix in ext_lower:
                            result.append(Path(entry.path))
        except PermissionError:
            pass
    return result


class ProcessingPipeline:
    def __init__(
        self,
        source: Path,
        dest: Path,
        project_code: str,
        sub_topic: str,
        rename_engine: RenameEngine,
        clustering_engine: ClusteringEngine,
        file_ops: FileOperations,
        hash_algorithm: str | None = None,
        auto_cluster: bool = True,
        selected_files: list[Path] | None = None,
        max_workers: int = 8,
        write_exif: bool = False,
        detect_duplicates: bool = False,
    ):
        self.source = source
        self.dest = dest
        self.project_code = project_code
        self.sub_topic = sub_topic
        self.rename_engine = rename_engine
        self.clustering_engine = clustering_engine
        self.file_ops = file_ops
        self.hash_algorithm = hash_algorithm
        self.auto_cluster = auto_cluster
        self.selected_files = selected_files
        self.max_workers = max_workers
        self.write_exif = write_exif
        self.detect_duplicates = detect_duplicates
        self._cancelled = False
        self._exiftool = ExifTool()
        self._file_registry = FileRegistry()

    def set_cancel(self):
        self._cancelled = True

    def execute(
        self,
        progress_callback: Callable[[int, int], None],
        log_callback: Callable[[str], None],
        duplicate_callback: Callable[[str], str | None],
        registry_callback: Callable[[list[str]], bool] | None = None,
    ) -> ProcessingResult:
        result = ProcessingResult()

        # Step 1: Scan (use fast scandir)
        if self.selected_files:
            log_callback(get_text("log_using_selected", count=len(self.selected_files)))
            all_files = [Path(f) for f in self.selected_files if Path(f).is_file()]
        else:
            log_callback(get_text("log_scanning"))
            all_files = _scan_dir_fast(self.source, ALL_SUPPORTED_EXTENSIONS)
        result.total_files = len(all_files)
        if self.selected_files:
            log_callback(get_text("log_found", count=len(all_files)))
        else:
            log_callback(get_text("log_found", count=len(all_files)))

        if result.total_files == 0:
            log_callback(get_text("log_no_files"))
            return result

        # Step 1b: Duplicate registry check
        if self.detect_duplicates and registry_callback:
            dup_files = self._file_registry.find_duplicates(all_files)
            if dup_files:
                log_callback(get_text("log_duplicates_found", count=len(dup_files)))
                dup_paths = [str(p) for p in dup_files]
                should_continue = registry_callback(dup_paths)
                if not should_continue:
                    log_callback(get_text("log_cancelled"))
                    return result

        # Step 2: Detect mode (sequence vs scattered)
        has_subfolders = self._has_subfolders_with_files(all_files)

        # Step 3: Classify assets
        log_callback(get_text("log_classifying"))
        assets = self._classify_assets(all_files, log_callback)
        progress_callback(0, result.total_files)

        # Step 4: Group
        log_callback(get_text("log_grouping"))
        if has_subfolders:
            asset_groups = self._group_sequence_folders(all_files, assets, log_callback)
        elif self.auto_cluster:
            asset_groups = self.clustering_engine.cluster_scattered_assets(assets)
        else:
            asset_groups = []
            for asset in assets:
                asset_groups.append(AssetGroup(assets=[asset], folder_name="", is_auto_cluster=False))

        has_video = any(a.asset_type == AssetType.VIDEO for a in assets)
        log_callback(get_text("log_created_groups", count=len(asset_groups)))

        # Step 5: Create destination structure
        log_callback(get_text("log_creating_dirs"))
        first_date = ""
        for asset in assets:
            if asset.date_prefix:
                first_date = asset.date_prefix
                break
        root_name = self.rename_engine.build_root_dir_name(first_date) if first_date else self.sub_topic
        root_dir = self.dest / root_name
        dirs = self.file_ops.create_directory_tree(root_dir, has_video=has_video)
        log_callback(get_text("log_dest_root", path=str(root_dir)))

        # Step 6: Parallel Copy + Verify
        # Flatten all assets into a task list
        tasks: list[tuple[Asset, str, dict[str, Path]]] = []
        for group in asset_groups:
            for asset in group.assets:
                tasks.append((asset, group.folder_name, dirs))

        log_callback(get_text("log_starting_transfer", count=self.max_workers))

        result_lock = threading.Lock()
        processed_count = 0
        last_progress_time = [0.0]  # mutable for closure
        successful_source_paths = []

        def _process_task(asset: Asset, folder_name: str, dirs: dict[str, Path]):
            nonlocal processed_count

            if self._cancelled:
                return

            dest_dir = self._get_dest_dir(asset, dirs, folder_name)
            filename = self._build_filename(asset, folder_name)
            dest_path = dest_dir / filename

            if dest_path.exists():
                new_stem = duplicate_callback(str(dest_path))
                if new_stem == "__SKIP__":
                    with result_lock:
                        result.skipped += 1
                        processed_count += 1
                        log_callback(get_text("log_skipped", name=dest_path.name))
                        # Throttle progress updates to reduce UI load
                        now = time.monotonic()
                        if now - last_progress_time[0] > 0.05:
                            last_progress_time[0] = now
                            progress_callback(processed_count, result.total_files)
                    return
                elif new_stem is not None:
                    filename = new_stem + asset.ext
                    dest_path = dest_dir / filename
                else:
                    log_callback(get_text("log_overwriting", name=dest_path.name))

            success, msg = self.file_ops.copy_with_verify(
                asset.source_path, dest_path, self.hash_algorithm
            )

            if success and self.write_exif:
                # Write metadata back to the destination file
                self._exiftool.write_exif_metadata(dest_path, self.project_code, self.sub_topic)

            with result_lock:
                if success:
                    result.processed += 1
                    successful_source_paths.append(asset.source_path)
                    if asset.xmp_companion:
                        successful_source_paths.append(asset.xmp_companion)
                else:
                    result.errors.append((str(asset.source_path), msg))
                    log_callback(get_text("log_error", name=asset.source_path.name, msg=msg))

                processed_count += 1
                # Throttle progress: emit at most every 50ms
                now = time.monotonic()
                if now - last_progress_time[0] > 0.05:
                    last_progress_time[0] = now
                    progress_callback(processed_count, result.total_files)
        # Execute parallel copy using thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for asset, folder_name, d in tasks:
                if self._cancelled:
                    break
                futures.append(executor.submit(_process_task, asset, folder_name, d))

            # Wait for all submitted tasks to complete
            for future in as_completed(futures):
                if self._cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                # Exceptions inside _process_task are caught; this just waits

        # Final progress update to ensure 100%
        progress_callback(processed_count, result.total_files)

        # Step 6b: EXIF write-back summary
        if self.write_exif:
            exif_count = min(len(successful_source_paths), result.processed)
            if exif_count > 0:
                log_callback(get_text("log_exif_written", count=exif_count))
            else:
                log_callback(get_text("log_exif_failed", count=0, msg="exiftool not available"))
        else:
            log_callback(get_text("log_exif_skipped"))

        # Step 7: Register imported files
        if self.detect_duplicates and successful_source_paths:
            log_callback(get_text("log_registering"))
            self._file_registry.register_files(successful_source_paths)

        # Step 8: Report
        log_callback(
            get_text("log_done",
                     processed=result.processed,
                     skipped=result.skipped,
                     errors=len(result.errors))
        )
        return result

    def _has_subfolders_with_files(self, all_files: list[Path]) -> bool:
        source_children = set()
        for p in all_files:
            try:
                rel = p.relative_to(self.source)
                parts = list(rel.parts)
                if len(parts) > 1:
                    source_children.add(self.source / parts[0])
            except ValueError:
                pass
        return len(source_children) > 0

    def _classify_assets(self, all_files: list[Path], log_callback: Callable[[str], None]) -> list[Asset]:
        assets: list[Asset] = []
        xmp_map: dict[str, Path] = {}

        raw_files = []
        for p in all_files:
            if p.suffix.lower() == ".xmp":
                xmp_map[p.stem] = p
            else:
                raw_files.append(p)

        for p in raw_files:
            ext_lower = p.suffix.lower()
            asset_type = AssetType.IMAGE if ext_lower in IMAGE_EXTENSIONS else AssetType.VIDEO

            stat = p.stat()
            timestamp_epoch = stat.st_mtime
            dt = datetime.fromtimestamp(timestamp_epoch)
            date_prefix = dt.strftime("%Y%m%d")

            original_digits = self.rename_engine.extract_last_4_digits(p.stem)

            xmp_companion = xmp_map.get(p.stem)

            asset = Asset(
                source_path=p,
                ext=ext_lower,
                asset_type=asset_type,
                date_prefix=date_prefix,
                original_digits=original_digits,
                timestamp_epoch=timestamp_epoch,
                xmp_companion=xmp_companion,
            )
            assets.append(asset)

        return assets

    def _group_sequence_folders(
        self,
        all_files: list[Path],
        assets: list[Asset],
        log_callback: Callable[[str], None],
    ) -> list[AssetGroup]:
        asset_map = {a.source_path: a for a in assets}
        folder_assets: dict[str, list[Asset]] = {}
        for p in all_files:
            try:
                rel = p.relative_to(self.source)
                if len(rel.parts) > 1:
                    folder_name = rel.parts[0]
                    if p in asset_map:
                        folder_assets.setdefault(folder_name, []).append(asset_map[p])
            except ValueError:
                pass

        groups = []
        for folder_name, folder_asset_list in sorted(folder_assets.items()):
            groups.append(AssetGroup(
                assets=folder_asset_list,
                folder_name=folder_name,
                is_auto_cluster=False,
            ))
        return groups

    def _get_dest_dir(self, asset: Asset, dirs: dict[str, Path], folder_name: str) -> Path:
        if asset.asset_type == AssetType.IMAGE:
            if folder_name:
                return dirs["imgRaws"] / folder_name
            return dirs["imgRaws"]
        elif asset.asset_type == AssetType.VIDEO:
            return dirs.get("vidRaws", dirs["imgRaws"])
        return dirs["imgRaws"]

    def _build_filename(self, asset: Asset, folder_name: str) -> str:
        if folder_name:
            return self.rename_engine.build_filename_formula_a(asset, folder_name)
        return self.rename_engine.build_filename_formula_b(asset)