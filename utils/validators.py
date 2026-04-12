import os
from pathlib import Path

from utils.i18n import get_text


def validate_inputs(source: str, dest: str, project_code: str, sub_topic: str) -> list[str]:
    errors = []
    if not source or not Path(source).is_dir():
        errors.append(get_text("err_source"))
    if not dest or not Path(dest).is_dir():
        errors.append(get_text("err_dest"))
    if not project_code.strip():
        errors.append(get_text("err_project_code"))
    if not sub_topic.strip():
        errors.append(get_text("err_sub_topic"))
    return errors