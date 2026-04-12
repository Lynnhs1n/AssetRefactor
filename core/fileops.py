import hashlib
import shutil
import os
from pathlib import Path


class FileOperations:
    @staticmethod
    def create_directory_tree(dest_root: Path, has_video: bool = False) -> dict[str, Path]:
        dirs = {}
        dirs["imgRaws"] = dest_root / "imgRaws"
        dirs["Masters"] = dest_root / "Masters"
        dirs["Exports"] = dest_root / "Exports"
        dirs["Exports/Web"] = dest_root / "Exports" / "Web"
        dirs["Exports/Stock_Getty"] = dest_root / "Exports" / "Stock_Getty"
        if has_video:
            dirs["vidRaws"] = dest_root / "vidRaws"

        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    @staticmethod
    def copy_with_verify(
        src: Path,
        dst: Path,
        algorithm: str | None = None,
        chunk_size: int = 4 * 1024 * 1024,  # Increased to 4MB for better throughput
    ) -> tuple[bool, str]:
        try:
            # Copy file
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Using copy2 for metadata preservation
            # shutil.copy2 handles large files efficiently
            shutil.copy2(str(src), str(dst))
        except Exception as e:
            return False, str(e)

        if algorithm is None:
            return True, "Copied (no hash verification)"

        try:
            # Compute hashes
            src_hash = FileOperations.compute_hash(src, algorithm, chunk_size)
            dst_hash = FileOperations.compute_hash(dst, algorithm, chunk_size)
        except Exception as e:
            return False, str(e)

        if src_hash != dst_hash:
            try:
                dst.unlink(missing_ok=True)
            except:
                pass
            return False, f"Hash mismatch: source={src_hash} dest={dst_hash}"

        return True, src_hash

    @staticmethod
    def compute_hash(filepath: Path, algorithm: str = "sha256", chunk_size: int = 4 * 1024 * 1024) -> str:
        if algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "md5":
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        with open(filepath, "rb", buffering=chunk_size) as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
