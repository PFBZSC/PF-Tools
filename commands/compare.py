import os
import sys

__description__ = "比较两文件是否相同：基于文件大小与动态分段抽样的快速比对，可选全量二进制深度比对。"
__aliases__ = ["comp"]
__author__ = "PFBZSC"
__version__ = "1.0.0"

def execute(args: list[str]) -> int:
    if not args or args[0] in ('-h', '--help'):
        print(f"用法: compare <文件1> <文件2> [all]")
        print(f"别名: {', '.join(__aliases__)}")
        print(f"描述: {__description__}")
        print("参数:")
        print("  all    可选。强制对文件二进制进行完全比对 (类似 fc /b)，遇差异终止。")
        return 0

    if len(args) < 2:
        print("错误: 参数不足。请使用 compare -h 查看用法。")
        return 1

    file1, file2 = args[0], args[1]
    is_full_compare = (len(args) > 2 and args[2].lower() == 'all')

    try:
        # 1. 前置拦截：存在性与文件大小检查 (O(1) 开销)
        if not os.path.isfile(file1):
            print(f"错误: 找不到文件 {file1}")
            return 1
        if not os.path.isfile(file2):
            print(f"错误: 找不到文件 {file2}")
            return 1

        size1 = os.path.getsize(file1)
        size2 = os.path.getsize(file2)

        if size1 != size2:
            print(f"差异: 文件大小不一致 ({size1} bytes vs {size2} bytes)")
            return 1

        if size1 == 0:
            print("相同: 均为 0 字节空文件。")
            return 0

        # 2. 路由到对应的比对引擎
        if is_full_compare:
            return _full_binary_compare(file1, file2)
        else:
            return _quick_sample_compare(file1, file2, size1)

    except Exception as e:
        print(f"执行异常: {str(e)}")
        return 1

def _quick_sample_compare(f1_path: str, f2_path: str, file_size: int) -> int:
    """动态抽样比对引擎：按体积动态计算抽样锚点"""
    MAX_CHUNK_SIZE = 8192  # 抽样块上限: 8KB
    
    # 确定中段抽样点数量
    if file_size < 10 * 1024 * 1024:         # <10MB: 抽 1 段
        mid_points = 1
    elif file_size < 100 * 1024 * 1024:      # 10MB~100MB: 抽 2 段
        mid_points = 2
    else:                                    # >=100MB: 抽 3 段
        mid_points = 3

    # 构建抽样偏移量 (Offset)
    offsets = [0]  # 强制包含头部
    
    if file_size > MAX_CHUNK_SIZE:
        offsets.append(file_size - MAX_CHUNK_SIZE)  # 强制包含尾部
        
        # 计算中段均匀分布的锚点
        step = file_size // (mid_points + 1)
        for i in range(1, mid_points + 1):
            mid_offset = (step * i) - (MAX_CHUNK_SIZE // 2)
            # 边界修正，防止读取越界
            offsets.append(max(0, min(mid_offset, file_size - MAX_CHUNK_SIZE)))
    
    # 去重并排序 (应对极小文件导致的偏移量重叠)
    offsets = sorted(list(set(offsets)))

    # 执行抽样比对
    with open(f1_path, 'rb') as f1, open(f2_path, 'rb') as f2:
        for offset in offsets:
            f1.seek(offset)
            f2.seek(offset)
            if f1.read(MAX_CHUNK_SIZE) != f2.read(MAX_CHUNK_SIZE):
                print(f"差异: 快速抽样发现内容不一致 (异常偏移量参考: 0x{offset:08X})。")
                return 1
                
    print("相同: 多重抽样校验通过。")
    return 0

def _full_binary_compare(f1_path: str, f2_path: str) -> int:
    """全量二进制比对引擎：遇异即抛 (类似 fc /b)"""
    CHUNK_SIZE = 1024 * 128  # 使用较大的缓冲块 (128KB) 优化 IO 吞吐
    current_offset = 0
    
    with open(f1_path, 'rb') as f1, open(f2_path, 'rb') as f2:
        while True:
            chunk1 = f1.read(CHUNK_SIZE)
            chunk2 = f2.read(CHUNK_SIZE)
            
            if chunk1 != chunk2:
                # 块内定位精确差异点
                for i in range(len(chunk1)):
                    if chunk1[i] != chunk2[i]:
                        diff_offset = current_offset + i
                        print(f"差异: 0x{diff_offset:08X}: 0x{chunk1[i]:02X} 0x{chunk2[i]:02X}")
                        return 1
            
            if not chunk1:
                break
            current_offset += len(chunk1)
            
    print("相同: 全量二进制比对一致。")
    return 0