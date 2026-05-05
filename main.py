import sys
import importlib.util
import ast
from pathlib import Path

BASE_DIR = Path(__file__).parent
COMMANDS_DIR = BASE_DIR / "commands"

def get_module_meta(file_path: Path):
    """【升级版】支持无限扩展的元数据解析"""
    desc = "未提供功能描述"
    aliases = []
    extra_meta = {} # 用于动态存放所有扩展字段
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path.name)
            
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # 1. 核心字段解析
                        if var_name == '__description__' and isinstance(node.value, ast.Constant):
                            desc = node.value.value
                        elif var_name == '__aliases__' and isinstance(node.value, (ast.List, ast.Tuple)):
                            aliases = [elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)]
                        # 2. 【核心扩展点】自动捕获其他所有 __xxx__ 字符串变量
                        elif var_name.startswith('__') and var_name.endswith('__') and isinstance(node.value, ast.Constant):
                            if var_name not in ('__description__', '__aliases__', '__file__', '__name__'):
                                # 剥离下划线作为展示标签 (如 __author__ -> author)
                                clean_key = var_name.strip('_').title() 
                                extra_meta[clean_key] = node.value.value
    except Exception:
        pass
        
    return desc, aliases, extra_meta

def print_global_help():
    print("用法: pt <command> [args...]\n")
    print("可用指令:")
    
    if not COMMANDS_DIR.exists():
        print("  [未找到 commands 目录]")
        return
        
    for file in COMMANDS_DIR.glob("*.py"):
        if file.name.startswith("__"): continue
        
        cmd_name = file.stem
        desc, aliases, extra_meta = get_module_meta(file)
        
        # 格式化指令与别名
        alias_str = f" ({', '.join(aliases)})" if aliases else ""
        display_name = f"{cmd_name}{alias_str}"
        
        # 格式化扩展字段 (如 [Author: John, Github: xxx])
        meta_info = [f"{k}: {v}" for k, v in extra_meta.items()]
        meta_str = f"\n{' ' * 24}└─ [{', '.join(meta_info)}]" if meta_info else ""
        
        print(f"  {display_name:<20} {desc}{meta_str}")

def find_command_file(cmd_name: str) -> Path | None:
    # 1. 极速匹配：直接查找同名文件 (O(1))
    direct_file = COMMANDS_DIR / f"{cmd_name}.py"
    if direct_file.exists():
        return direct_file
        
    # 2. 别名回退：AST 遍历所有文件查找别名 (O(N)，但 AST 解析极快)
    if COMMANDS_DIR.exists():
        for file in COMMANDS_DIR.glob("*.py"):
            if file.name.startswith("__"): continue
            
            # 【修复点】：这里需要接收 3 个返回值，用 _ 忽略掉不需要的 extra_meta
            _, aliases, _ = get_module_meta(file)
            
            if cmd_name in aliases:
                return file
                
    return None

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print_global_help()
        sys.exit(0)

    input_cmd = sys.argv[1]
    cmd_args = sys.argv[2:]
    
    # 解析指令（支持原名和别名）
    cmd_file = find_command_file(input_cmd)

    if not cmd_file:
        print(f"错误: 未知指令 '{input_cmd}'。")
        print("输入 'pt help' 查看可用指令。")
        sys.exit(1)

    # 定位到文件后，真正执行动态加载
    spec = importlib.util.spec_from_file_location(cmd_file.stem, cmd_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, 'execute'):
        print(f"错误: 模块 '{cmd_file.name}' 格式不规范，缺少 'execute(args)' 函数。")
        sys.exit(1)

    try:
        exit_code = module.execute(cmd_args)
        sys.exit(exit_code if exit_code is not None else 0)
    except Exception as e:
        print(f"执行指令时发生未捕获的异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()