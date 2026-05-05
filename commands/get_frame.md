# 模块名称: get_frame
> 本文档专为 AI 跨模块调用参考生成。

## 1. 基础信息
- **模块文件**: `commands/get_frame.py`
- **CLI 指令**: `pt get_frame`
- **短指令 (Aliases)**: `['gf']`
- **功能描述**: 使用 FFmpeg 提取视频的特定帧，支持正倒数索引（如 `-1` 提取最后一帧）及智能输出路径识别。

## 2. 命令行调用 (CLI)
- **语法**: `pt get_frame <视频路径> [帧数] [输出路径] [-o 输出路径]`
- **示例**: 
  - 提取首帧至默认目录: `pt gf input.mp4`
  - 提取第10帧并指定名称: `pt gf input.mp4 10 custom_name.png`
  - 提取倒数第2帧至指定目录: `pt gf input.mp4 -2 ./output_dir/`
  - 跳过帧数参数直接指定输出: `pt gf input.mp4 -o out.jpg`

## 3. 跨模块调用 (Python API)
如果你在其他 `commands/*.py` 模块中需要复用此功能，请使用以下方式：
```python
from commands.get_frame import execute as get_frame_execute

# 参数必须按序放入列表中，全为字符串
args = ["video.mp4", "-1", "-o", "output.png"]
exit_code = get_frame_execute(args)