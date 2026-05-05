# 模块名称: ffmpeg
> 本文档专为 AI 跨模块调用参考生成。

## 1. 基础信息
- **模块文件**: `commands/ffmpeg.py`
- **CLI 指令**: `pt ffmpeg`
- **短指令 (Aliases)**: `['ff']`
- **功能描述**: 交互式视频/图片压缩与转换 (利用 FFmpeg CUDA 硬件加速)。支持单文件极速预设，及高级模式下的目录遍历、自动化重命名与防死循环逻辑。

## 2. 命令行调用 (CLI)
- **语法**: `pt ffmpeg [adv]`
- **示例**: 
  - `pt ffmpeg` (启动单文件标准模式)
  - `pt ffmpeg adv` (启动带文件夹批处理支持的高级模式)

## 3. 跨模块调用 (Python API)
如果你在其他 `commands/*.py` 模块中需要复用此功能，请使用以下方式：

\`\`\`python
from commands.ffmpeg import execute as ffmpeg_execute

# 参数必须按序放入列表中，全为字符串
args = []       # 调用标准交互模式
# args = ["adv"] # 调用高级交互模式
exit_code = ffmpeg_execute(args)
\`\`\`

## 4. 返回值与异常机制
- **返回值**: 返回 `0` 视作成功，返回非 `0` 视作失败（含 Ctrl+C 中断或系统抛错）。
- **副作用**: 强依赖于系统的输入输出 `input()` 及标准输出打印流。将在指定的输出路径/目录产生压缩后的多媒体实体文件。

## 5. 依赖说明
- **系统/外部依赖**: `ffmpeg` (必须加入环境变量，并包含 `hevc_nvenc` 支持)。
- **内置依赖**: `os`, `sys`, `subprocess`, `pathlib`