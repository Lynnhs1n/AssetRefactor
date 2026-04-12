from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class AssetType(Enum):
    IMAGE = "imgRaws"
    VIDEO = "vidRaws"


@dataclass
class Asset:
    source_path: Path
    ext: str
    asset_type: AssetType
    date_prefix: str = ""             # YYYYMMDD from filesystem modification time
    original_digits: str = ""         # last 4 digits from filename
    timestamp_epoch: float = 0.0      # for clustering comparison
    xmp_companion: Optional[Path] = None  # paired .xmp sidecar


@dataclass
class AssetGroup:
    assets: list[Asset]
    folder_name: str              # original subfolder name or "AutoSeq_N"
    is_auto_cluster: bool = False


@dataclass
class ProcessingResult:
    total_files: int = 0
    processed: int = 0
    skipped: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)  # (path, error_msg)