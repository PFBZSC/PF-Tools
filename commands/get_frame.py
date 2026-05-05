import os
import shutil
import subprocess
from pathlib import Path

__description__ = "使用 FFmpeg 提取视频特定帧（支持正倒数及路径智能识别）"
__aliases__ = ["gf"]
__author__ = "PFBZSC"
__version__ = "1.0.0"

def execute(args: list[str]) -> int:
    # 1. 帮助与空参处理
    if not args or "-h" in args or "--help" in args:
        print("用法: pt get_frame <视频路径> [帧数] [输出路径] [-o 输出路径]")
        print("参数说明:")
        print("  <视频路径>  必需。输入视频的路径")
        print("  [帧数]      可选。默认 1 (第一帧)。支持指定正数或负数(如 -1 为倒数第一帧)")
        print("  [输出路径]  可选。支持智能识别目录/路径/文件名，或使用 -o 指定。默认存至当前目录。")
        return 0

    try:
        # 2. 依赖检查
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            print("错误: 系统环境中未找到 ffmpeg 或 ffprobe，请先安装。")
            return 1

        # 3. 参数解析与智能回退
        output_path = None
        # 处理 -o 标志
        if "-o" in args:
            idx = args.index("-o")
            args.pop(idx)
            if idx < len(args):
                output_path = args.pop(idx)

        if not args:
            print("错误: 缺少必填参数 <视频路径>\n用法: pt get_frame <视频路径> [帧数]")
            return 1

        video_path = args.pop(0)
        if not os.path.isfile(video_path):
            print(f"错误: 视频文件不存在 -> {video_path}")
            return 1

        frame_num = 1
        # 处理 [帧数] (可能是数字，若报错则将其视为 [输出路径])
        if args:
            try:
                frame_num = int(args[0])
                args.pop(0)
            except ValueError:
                pass

        # 兜底处理剩余的位置参数作为输出路径
        if args and not output_path:
            output_path = args.pop(0)

        # 4. 核心帧数计算
        target_frame = frame_num - 1 # FFmpeg select 从 0 开始计算

        if frame_num < 0:
            # 倒数处理：先尝试读取 metadata，若失败则全流扫描统计帧数
            probe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=nb_frames", 
                "-of", "default=nokey=1:noprint_wrappers=1", video_path
            ]
            res = subprocess.run(probe_cmd, capture_output=True, text=True)
            out = res.stdout.strip()
            
            if out and out.isdigit():
                total_frames = int(out)
            else:
                probe_cmd[6] = "stream=nb_read_frames"
                probe_cmd.insert(5, "-count_frames")
                res = subprocess.run(probe_cmd, capture_output=True, text=True)
                out = res.stdout.strip()
                total_frames = int(out) if out.isdigit() else 0

            if total_frames <= 0:
                print("错误: 无法获取视频总帧数，不支持使用负数倒数提取。")
                return 1
            target_frame = total_frames + frame_num

        if target_frame < 0:
            print("错误: 帧索引计算越界。")
            return 1

        # 5. 输出路径智能推导
        v_path = Path(video_path)
        default_name = f"{v_path.stem}_frame_{frame_num}.png"
        
        if output_path:
            out_p = Path(output_path)
            # 若已存在且是目录，或以路径分隔符结尾，判定为目录
            if out_p.is_dir() or output_path.replace("\\", "/").endswith("/"):
                final_out = out_p / default_name
            # 若明确带有图片后缀，判定为具体文件
            elif out_p.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
                final_out = out_p
            # 否则判定为不带后缀的文件名
            else:
                final_out = out_p.with_suffix(".png")
            final_out.parent.mkdir(parents=True, exist_ok=True)
        else:
            final_out = Path.cwd() / default_name

        # 6. FFmpeg 提取调用
        # 注意: subprocess 列表传参无需手动为 select 内容加引号，由系统底层直接传递
        extract_cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"select=eq(n\\,{target_frame})",
            "-frames:v", "1", str(final_out)
        ]

        process = subprocess.run(extract_cmd, capture_output=True, text=True)
        if process.returncode != 0 or not final_out.exists():
            print(f"错误: 帧提取失败。\n{process.stderr}")
            return 1

        print(f"提取成功: {final_out}")
        return 0

    except Exception as e:
        print(f"模块执行异常: {str(e)}")
        return 1