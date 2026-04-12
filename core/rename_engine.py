import re
from core.models import Asset
from utils.constants import DIGITS_PATTERN


class RenameEngine:
    def __init__(self, project_code: str, sub_topic: str):
        self.project = project_code
        self.topic = sub_topic

    def build_root_dir_name(self, date_prefix: str) -> str:
        return f"{date_prefix}_{self.project}_{self.topic}"

    def build_filename_formula_a(self, asset: Asset, subfolder_name: str) -> str:
        name = f"{asset.date_prefix}_{self.project}_{self.topic}_{subfolder_name}_{asset.original_digits}{asset.ext}"
        return name

    def build_filename_formula_b(self, asset: Asset) -> str:
        name = f"{asset.date_prefix}_{self.project}_{self.topic}_{asset.original_digits}{asset.ext}"
        return name

    @staticmethod
    def extract_last_4_digits(filename: str) -> str:
        # Matches the last 4 contiguous digits in filename
        # DIGITS_PATTERN = re.compile(r'(\d{4})(?=\D*$)')
        match = DIGITS_PATTERN.search(filename)
        return match.group(1) if match else "0000"
