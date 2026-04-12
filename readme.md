

数字资产整理软件


AssetRefactor Pro (GUI 版 - 命名增强型)
项目目标：
开发一个基于 Python 和 PyQt6 的桌面 GUI 应用，用于将摄影/视频资产重构到指定的 NAS 或本地路径。 软件名为AssetRefactor

1. 界面与身份标识 (GUI & Branding):

窗口底部状态栏 (Status Bar)： 在界面最下方，使用较小但清晰的字体（如 9pt Gray）展示：© 2026 lynnhsin. All Rights Reserved.

交互逻辑： 包含源路径选择、目标路径选择、ProjectCode 和 SubTopic 输入框，以及实时日志输出和进度条。
    源路径选择技术要求：用户选择源路径导入图片或者视频时，导入界面需支持预览要导入的文件的时间信息和缩略图、视频预览等，方便用户精准选中同一个项目的图片或者视频。
2. 核心重命名与目录逻辑 (核心需求更新):

根目录命名： {YYYYMMDD}_{ProjectCode}_{SubTopic}。

A. 序列文件夹导入逻辑（如果源路径中包含子文件夹）：

目标位置：/imgRaws/[原文件夹名]/。

文件名公式： {YYYYMMDD}_{ProjectCode}_{SubTopic}_{原文件夹名}_{Original4Digits}.{ext}。


B. 散碎文件导入逻辑（直接选择的文件或无子文件夹）：

目标位置：/imgRaws/。

文件名公式： {YYYYMMDD}_{ProjectCode}_{SubTopic}_{Original4Digits}.{ext}。

自动聚类： 若散碎文件间符合“时间间隔 < 3秒 + 文件名连续”，自动创建子文件夹归类，并按公式 A 命名（seqfoldername 可设为 AutoSeq_N）。

3. 资产分类规格:

/imgRaws: 移动图片（.ARW, .CR3, .dng 及同步 .xmp）。

/vidRaws: 移动视频（.mp4, .mov）。

/Masters & /Exports: 创建对应的二级及三级空目录备用。

4. 技术要求:

调用 exiftool 提取 DateTimeOriginal 作为日期前缀，如果没有找到exiftool要提示用户选择exiftool的安装位置。

使用 re 正则表达式精准截取原文件名末尾 4 位数字。

集成哈希校验，确保跨设备（NAS）传输的数据完整性。


v0.1 
改进：
1.提升文件拷贝的速度，同时确保准确性。
2.增加重复文件检测的功能，如果发现