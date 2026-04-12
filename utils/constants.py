import re

# Supported file extensions (lowercase for comparison)
IMAGE_EXTENSIONS = {".arw", ".cr3", ".dng", ".xmp", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}
ALL_SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
RAW_IMAGE_EXTENSIONS = {".arw", ".cr3", ".dng"} # Standard RAW formats
STANDARD_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# Regex for extracting last 4 consecutive digits from filename
DIGITS_PATTERN = re.compile(r'(\d{4})(?=\D*$)')

# Default auto-cluster time threshold in seconds
DEFAULT_CLUSTER_TIME_SEC = 3.0

# Hash algorithm choices
HASH_ALGORITHMS = {
    "SHA-256": "sha256",
    "MD5": "md5",
    "不校验": None,
}

# ExifTool date tags in fallback order
EXIF_DATE_TAG_FALLBACK = ["DateTimeOriginal", "CreateDate", "FileModifyDate"]