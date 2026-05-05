import os
import sys
import subprocess
from pathlib import Path

__description__ = "交互式视频/图片压缩与转换 (硬件加速)"
__aliases__ = ["ff"]
__author__ = "PFBZSC"
__version__ = "1.0.0"

VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts', '.webm'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}

def execute(args: list[str]) -> int:
    if "-h" in args or "--help" in args:
        print("用法: pt ffmpeg [adv]")
        print("  <无参数>    进入基础模式，对单一文件应用预设压制。")
        print("  adv         进入高级模式，支持文件夹遍历、自定义参数及格式转换。")
        return 0

    # 严格参数校验：只允许空参数或仅包含一个 "adv"
    if len(args) > 1 or (len(args) == 1 and args[0] != "adv"):
        print(f"[!] 参数错误: 无法识别的参数 '{' '.join(args)}'")
        print("用法: pt ffmpeg [adv]")
        print("输入 'pt ffmpeg -h' 获取更多帮助。")
        return 1

    is_adv = (len(args) == 1 and args[0] == "adv")

    try:
        if is_adv:
            return run_advanced()
        else:
            return run_standard()
    except KeyboardInterrupt:
        print("\n[!] 操作已取消")
        return 1
    except Exception as e:
        print(f"[!] 执行异常: {e}")
        return 1

def run_standard() -> int:
    p = input("输入文件路径(简易模式不支持文件夹): ").strip(' "\'')
    if not p or not os.path.isfile(p):
        print("[!] 文件不存在或输入了文件夹。")
        return 1

    path = Path(p)
    ext = path.suffix.lower()

    if ext in IMAGE_EXTS:
        out_path = path.with_name(f"{path.stem}_pt{ext}")
        cmd = ["ffmpeg", "-v", "warning", "-i", str(path)]
        if ext in {'.jpg', '.jpeg'}:
            cmd.extend(["-c:v", "mjpeg", "-q:v", "5", "-f", "image2"])
        cmd.extend(["-y", str(out_path)])
        
        print(f"[*] 正在压缩图片 -> {out_path}")
        subprocess.run(cmd, check=True)
        return 0
    else:
        print("\n视频预设:")
        print("0. 高保真(cq 26, 原分辨率与帧率, 音频copy, p7) [默认]")
        print("1. 1080p60fps, cq 26, p7, 音频128k")
        print("2. 1080p30fps, cq 26, p7, 音频128k")
        print("3. 720p60fps, cq 26, p7, 音频128k")
        print("4. 720p30fps, cq 26, p7, 音频128k")
        choice = input("请选择预设[0]: ").strip() or "0"

        vf = ""
        audio_args = ["-c:a", "copy"]
        if choice == "1":
            vf, audio_args = "scale=-1:1080,fps=60", ["-c:a", "aac", "-b:a", "128k"]
        elif choice == "2":
            vf, audio_args = "scale=-1:1080,fps=30", ["-c:a", "aac", "-b:a", "128k"]
        elif choice == "3":
            vf, audio_args = "scale=-1:720,fps=60", ["-c:a", "aac", "-b:a", "128k"]
        elif choice == "4":
            vf, audio_args = "scale=-1:720,fps=30", ["-c:a", "aac", "-b:a", "128k"]

        out_path = path.with_name(f"{path.stem}_pt.mp4")
        cmd = build_video_cmd(path, out_path, vf=vf, audio_args=audio_args, cq="26", preset="p7")
        print(f"[*] 正在压缩视频 -> {out_path}")
        subprocess.run(cmd, check=True)
        return 0

def run_advanced() -> int:
    p = input("输入文件或文件夹路径(.代表当前路径): ").strip(' "\'')
    if not p:
        return 1
    
    target = Path(p).resolve()
    if not target.exists():
        print("[!] 路径不存在")
        return 1

    is_dir = target.is_dir()
    
    # 交互收集参数
    recursive = True
    media_type = "1" # 1全部 2视频 3图片
    img_format = "1" # 1原格式 2png 3jpg
    
    if is_dir:
        recursive = (input("是否递归? (Y/n) [默认Y]: ").strip().lower() != 'n')
        print("处理类型: 1.全部 2.视频 3.图片")
        media_type = input("请选择类型[1]: ").strip() or "1"
    else:
        # 智能识别单文件类型，屏蔽不相关的参数询问
        if target.suffix.lower() in IMAGE_EXTS:
            media_type = "3"
        else:
            media_type = "2" # 默认按视频处理
    
    # --- 图片参数收集 ---
    if media_type in {"1", "3"}:
        print("图片输出格式: 1.原格式 2.png 3.jpg")
        img_format = input("请选择格式[1]: ").strip() or "1"

    # --- 视频参数收集与初始化 ---
    vf_str = ""
    audio_args = ["-c:a", "copy"]
    target_cq = "26"
    target_preset = "p1"

    if media_type in {"1", "2"}:
        target_res = input("目标分辨率(如 1080 或 1920x1080) [默认原比例不缩放]: ").strip()
        target_fps = input("目标帧率 [默认原帧率]: ").strip()
        audio_opt = input("音频比特率(如 128k, copy) [默认 128k]: ").strip() or "128k"
        target_cq = input("CQ 值 [默认 26]: ").strip() or "26"
        target_preset = input("Preset [默认 p1]: ").strip() or "p1"

        # 构建 vf 参数
        vf_parts = []
        if target_res:
            if "x" in target_res:
                vf_parts.append(f"scale={target_res.replace('x', ':')}")
            else:
                vf_parts.append(f"scale=-1:{target_res}")
        if target_fps:
            vf_parts.append(f"fps={target_fps}")
        vf_str = ",".join(vf_parts)

        audio_args = ["-c:a", "copy"] if audio_opt.lower() == "copy" else ["-c:a", "aac", "-b:a", audio_opt]

    # 收集任务队列
    tasks = [] # list of (input_path, out_path, is_image)
    if not is_dir:
        default_out = target.with_name(f"{target.stem}_pt{target.suffix}")
        out_str = input(f"输出名称 [默认 {default_out.name}]: ").strip()
        out_path = target.with_name(out_str) if out_str else default_out
        
        # 处理图片格式后缀冲突
        is_img = target.suffix.lower() in IMAGE_EXTS
        if is_img and img_format != "1":
            expected_ext = ".png" if img_format == "2" else ".jpg"
            if out_path.suffix.lower() != expected_ext:
                fix = input(f"[警告] 格式选了{expected_ext}但输出为{out_path.suffix}，回车自动修正，或输入新名称: ").strip()
                if not fix:
                    out_path = out_path.with_suffix(expected_ext)
                else:
                    out_path = target.with_name(fix)

        if not is_img and out_path.suffix.lower() != ".mp4":
            out_path = out_path.with_suffix(".mp4")
            
        tasks.append((target, out_path, is_img))
    else:
        default_dir = target.with_name(f"{target.name}_pt")
        out_dir_str = input(f"输出目录 [默认同级 {default_dir.name}]: ").strip()
        out_dir = target.parent / out_dir_str if out_dir_str else default_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 遍历与防死循环过滤
        for root, dirs, files in os.walk(target):
            if not recursive and Path(root) != target:
                break
            # 防死循环：跳过目标目录
            if out_dir in Path(root).resolve().parents or Path(root).resolve() == out_dir.resolve():
                continue
            
            for file in files:
                ext = Path(file).suffix.lower()
                is_img = ext in IMAGE_EXTS
                is_vid = ext in VIDEO_EXTS
                
                if media_type == "2" and not is_vid: continue
                if media_type == "3" and not is_img: continue
                if media_type == "1" and not (is_vid or is_img): continue

                in_path = Path(root) / file
                
                # 确定后缀
                out_ext = ext
                if is_img and img_format == "2": out_ext = ".png"
                elif is_img and img_format == "3": out_ext = ".jpg"
                elif is_vid: out_ext = ".mp4"

                out_path = get_unique_path(out_dir / f"{in_path.stem}{out_ext}")
                tasks.append((in_path, out_path, is_img))

    # 执行任务队列
    total = len(tasks)
    for idx, (in_p, out_p, is_img) in enumerate(tasks, 1):
        print(f"\n[{idx}/{total}] 处理: {in_p.name} -> {out_p.name}")
        if is_img:
            cmd = build_img_cmd(in_p, out_p, img_format)
        else:
            cmd = build_video_cmd(in_p, out_p, vf_str, audio_args, target_cq, target_preset)
        
        subprocess.run(cmd, check=True)

    print("\n[*] 全部处理完成。")
    return 0

def build_video_cmd(in_path: Path, out_path: Path, vf: str, audio_args: list, cq: str, preset: str) -> list:
    cmd = [
        "ffmpeg", "-hwaccel", "cuda", "-i", str(in_path),
        "-c:v", "hevc_nvenc", "-preset", preset, "-tune", "hq",
        "-rc", "vbr", "-cq", cq, "-b:v", "0", "-bf", "3",
        "-rc-lookahead", "32", "-spatial-aq", "1"
    ]
    if vf:
        cmd.extend(["-vf", vf])
    cmd.extend(audio_args)
    cmd.extend(["-f", "mp4", "-y", str(out_path)])
    return cmd

def build_img_cmd(in_path: Path, out_path: Path, img_format: str) -> list:
    cmd = ["ffmpeg", "-v", "warning", "-i", str(in_path)]
    if out_path.suffix.lower() in {'.jpg', '.jpeg'} or img_format == "3":
        cmd.extend(["-c:v", "mjpeg", "-q:v", "5", "-f", "image2"])
    cmd.extend(["-y", str(out_path)])
    return cmd

def get_unique_path(target: Path) -> Path:
    if not target.exists():
        return target
    counter = 1
    while True:
        new_path = target.with_name(f"{target.stem}_{counter}{target.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1