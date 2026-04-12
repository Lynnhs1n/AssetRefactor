"""Internationalization (i18n) support for AssetRefactor."""

_current_lang = "zh_CN"

LANGUAGES = {
    "zh_CN": "中文",
    "en_US": "English",
}

STRINGS = {
    "zh_CN": {
        # UI labels
        "source_dest": "源路径与目标路径",
        "source_label": "源目录:",
        "dest_label": "目标目录:",
        "browse": "浏览...",
        "preview": "预览...",
        "project_info": "作品项目信息",
        "project_code_label": "作品集名称:",
        "sub_topic_label": "作品集子名称:",
        "options": "选项",
        "auto_cluster": "自动聚类散碎文件",
        "time_interval": "时间间隔（秒）:",
        "hash_label": "哈希校验:",
        "hash_no_verify": "不校验",
        "log": "日志",
        "start": "开始",
        "cancel": "取消",
        "license": "MIT License",
        "language_label": "语言:",
        # Checkboxes
        "write_exif_label": "将作品集信息写入文件 EXIF 元数据",
        "detect_duplicates_label": "检测重复文件（已导入过的文件）",
        # Dialogs
        "select_source": "选择源目录",
        "select_dest": "选择目标目录",
        "validation_error": "输入验证错误",
        "completed_errors": "完成但有错误",
        "completed_success": "成功完成",
        "fatal_error": "致命错误",
        "duplicate_found_title": "发现重复文件",
        "duplicate_found_msg": "文件已存在:\n{path}\n\n你想如何处理?",
        "overwrite": "覆盖",
        "rename": "重命名",
        "skip": "跳过",
        "duplicate_detected_title": "检测到重复文件",
        "duplicate_detected_msg": "以下 {count} 个文件已在之前的导入中记录:\n{files}\n\n是否继续导入?",
        # Preview dialog
        "preview_title": "预览 — {dir}",
        "scanning": "正在扫描文件...",
        "loading_meta": "找到 {count} 个支持的文件。正在加载元数据和缩略图...",
        "loaded": "已加载 {count} 个文件。勾选/取消勾选要导入的文件，然后点击确定。",
        "select_all": "全选",
        "deselect_all": "全不选",
        "selected_count": "已选: {count} / {total}",
        "col_select": "选择",
        "col_preview": "预览",
        "col_filename": "文件名",
        "col_folder": "文件夹",
        "col_date": "日期",
        "col_time": "时间",
        "label_video": "视频",
        "label_image": "图片",
        # Validator errors
        "err_source": "源目录不存在或无法访问。",
        "err_dest": "目标目录不存在或无法访问。",
        "err_project_code": "作品集名称不能为空。",
        "err_sub_topic": "作品集子名称不能为空。",
        # Pipeline logs
        "log_using_selected": "使用 {count} 个用户选择的文件...",
        "log_scanning": "正在扫描源目录...",
        "log_found": "找到 {count} 个支持的文件。",
        "log_no_files": "未找到支持的文件。中止。",
        "log_classifying": "正在分类资产...",
        "log_grouping": "正在分组资产...",
        "log_created_groups": "创建了 {count} 个组。",
        "log_creating_dirs": "正在创建目录结构...",
        "log_dest_root": "目标根目录: {path}",
        "log_starting_transfer": "开始并行文件传输 ({count} 个工作线程)...",
        "log_skipped": "已跳过（用户选择）: {name}",
        "log_overwriting": "正在覆盖: {name}",
        "log_copied": "已复制: {src} -> {dst}",
        "log_error": "错误: {name} - {msg}",
        "log_cancelled": "用户已取消处理。",
        "log_done": "完成！处理: {processed}, 跳过: {skipped}, 错误: {errors}",
        "log_exif_written": "已将元数据写入 {count} 个文件。",
        "log_exif_failed": "元数据写入失败 ({count} 个文件): {msg}",
        "log_exif_skipped": "未启用 EXIF 写入，跳过。",
        "log_duplicates_found": "检测到 {count} 个重复文件，已在之前的导入中记录。",
        "log_registering": "正在注册已导入的文件到数据库...",
    },
    "en_US": {
        # UI labels
        "source_dest": "Source & Destination",
        "source_label": "Source:",
        "dest_label": "Destination:",
        "browse": "Browse...",
        "preview": "Preview...",
        "project_info": "Project Info",
        "project_code_label": "Project Code:",
        "sub_topic_label": "Sub Topic:",
        "options": "Options",
        "auto_cluster": "Auto-cluster scattered files",
        "time_interval": "Time interval (sec):",
        "hash_label": "Hash:",
        "hash_no_verify": "Skip",
        "log": "Log",
        "start": "Start",
        "cancel": "Cancel",
        "license": "MIT License",
        "language_label": "Language:",
        # Checkboxes
        "write_exif_label": "Write project info to file EXIF metadata",
        "detect_duplicates_label": "Detect duplicate files (previously imported)",
        # Dialogs
        "select_source": "Select Source Directory",
        "select_dest": "Select Destination Directory",
        "validation_error": "Validation Error",
        "completed_errors": "Completed with Errors",
        "completed_success": "Completed Successfully",
        "fatal_error": "Fatal Error",
        "duplicate_found_title": "Duplicate File Found",
        "duplicate_found_msg": "File already exists:\n{path}\n\nWhat would you like to do?",
        "overwrite": "Overwrite",
        "rename": "Rename",
        "skip": "Skip",
        "duplicate_detected_title": "Duplicate Files Detected",
        "duplicate_detected_msg": "The following {count} files were already imported before:\n{files}\n\nContinue importing?",
        # Preview dialog
        "preview_title": "Preview — {dir}",
        "scanning": "Scanning files...",
        "loading_meta": "Found {count} supported files. Loading metadata & thumbnails...",
        "loaded": "Loaded {count} files. Check/select files to import, then click OK.",
        "select_all": "Select All",
        "deselect_all": "Deselect All",
        "selected_count": "Selected: {count} / {total}",
        "col_select": "Select",
        "col_preview": "Preview",
        "col_filename": "Filename",
        "col_folder": "Folder",
        "col_date": "Date",
        "col_time": "Time",
        "label_video": "VIDEO",
        "label_image": "IMAGE",
        # Validator errors
        "err_source": "Source directory does not exist or is not accessible.",
        "err_dest": "Destination directory does not exist or is not accessible.",
        "err_project_code": "Project Code cannot be empty.",
        "err_sub_topic": "Sub Topic cannot be empty.",
        # Pipeline logs
        "log_using_selected": "Using {count} user-selected files...",
        "log_scanning": "Scanning source directory...",
        "log_found": "Found {count} supported files.",
        "log_no_files": "No supported files found. Aborting.",
        "log_classifying": "Classifying assets...",
        "log_grouping": "Grouping assets...",
        "log_created_groups": "Created {count} groups.",
        "log_creating_dirs": "Creating destination structure...",
        "log_dest_root": "Destination root: {path}",
        "log_starting_transfer": "Starting parallel file transfer ({count} workers)...",
        "log_skipped": "Skipped (user choice): {name}",
        "log_overwriting": "Overwriting: {name}",
        "log_copied": "Copied: {src} -> {dst}",
        "log_error": "ERROR: {name} - {msg}",
        "log_cancelled": "Processing cancelled by user.",
        "log_done": "Done! Processed: {processed}, Skipped: {skipped}, Errors: {errors}",
        "log_exif_written": "Metadata written to {count} files.",
        "log_exif_failed": "Metadata write failed ({count} files): {msg}",
        "log_exif_skipped": "EXIF writing disabled, skipping.",
        "log_duplicates_found": "Detected {count} duplicate files already recorded from previous imports.",
        "log_registering": "Registering imported files to database...",
    },
}


def get_language() -> str:
    return _current_lang


def set_language(lang_code: str):
    global _current_lang
    if lang_code in STRINGS:
        _current_lang = lang_code


def get_text(key: str, **kwargs) -> str:
    text = STRINGS[_current_lang].get(key, STRINGS["zh_CN"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
