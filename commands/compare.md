# 模块名称: compare
> 本文档专为 AI 跨模块调用参考生成。

## 1. 基础信息
- **模块文件**: `commands/compare.py`
- **CLI 指令**: `pt compare`
- **短指令 (Aliases)**: `['comp']`
- **功能描述**: 比较两文件是否相同：基于文件大小与动态分段抽样的快速比对，可选全量二进制深度比对。

## 2. 命令行调用 (CLI)
- **语法**: `pt compare <文件1> <文件2> [all]`
- **示例**: `pt compare fileA.zip fileB.zip all`

## 3. 跨模块调用 (Python API)
如果你在其他 `commands/*.py` 模块中需要复用此功能，请使用以下方式：
```python
from commands.compare import execute as compare_execute

# 参数必须按序放入列表中，全为字符串
args = ["path/to/fileA.zip", "path/to/fileB.zip", "all"]
exit_code = compare_execute(args)