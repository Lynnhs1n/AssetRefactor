import subprocess
import shutil
from pathlib import Path

from utils.constants import EXIF_DATE_TAG_FALLBACK


class ExifToolNotFoundError(Exception):
    pass


class ExifTool:
    """ExifTool wrapper — now only used for thumbnail extraction.
    Date extraction was replaced by filesystem timestamps."""

    def __init__(self, exiftool_path: str | None = None):
        if exiftool_path:
            self._cmd = str(exiftool_path)
        else:
            self._cmd = self._find_exiftool()

    @staticmethod
    def _find_exiftool() -> str:
        result = shutil.which("exiftool")
        if result:
            return result
        return ""

    @classmethod
    def is_available(cls, exiftool_path: str | None = None) -> bool:
        if exiftool_path:
            return Path(exiftool_path).is_file()
        return shutil.which("exiftool") is not None

    def extract_thumbnail(self, filepath: Path) -> bytes | None:
        """Extract embedded JPEG thumbnail from file using exiftool -b."""
        if not self._cmd:
            return None
        try:
            for tag in ("ThumbnailImage", "PreviewImage", "JpgFromRaw"):
                proc = subprocess.run(
                    [self._cmd, "-b", f"-{tag}", str(filepath)],
                    capture_output=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if proc.returncode == 0 and proc.stdout and len(proc.stdout) > 100:
                    return proc.stdout
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def write_exif_metadata(self, filepath: Path, project_code: str, sub_topic: str) -> tuple[bool, str]:
        """Write ProjectCode and SubTopic to EXIF metadata using exiftool."""
        if not self._cmd:
            return False, "exiftool not available"
        try:
            proc = subprocess.run(
                [self._cmd,
                 "-overwrite_original",
                 f"-XMP-photoshop:City={sub_topic}",
                 f"-XMP-dc:Subject={project_code}",
                 str(filepath)],
                capture_output=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if proc.returncode == 0:
                return True, "Metadata written"
            return False, proc.stderr.decode(errors="replace")
        except subprocess.TimeoutExpired:
            return False, "exiftool timed out"
        except Exception as e:
            return False, str(e)