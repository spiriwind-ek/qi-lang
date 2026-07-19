"""指令加载器：从 TOML 定义文件动态生成 OpCode 枚举"""
import tomllib
from enum import Enum
from pathlib import Path
from typing import Any


def _load_opcodes():
    """读取指令定义 TOML，生成 OpCode 枚举"""
    path = Path(__file__).parent / '指令定义.toml'
    with open(path, 'rb') as f:
        data = tomllib.load(f)
    
    # 按 TOML 中的顺序创建枚举成员
    members = {}
    meta = {}
    for name, info in data['opcode'].items():
        members[name] = len(members)
        meta[members[name]] = info
    
    OpCode = Enum('OpCode', members)
    return OpCode, meta


OpCode, _OPCODE_META = _load_opcodes()


def get_opcode_info(opcode) -> dict[str, Any]:
    """获取指令的元数据（参数类型、栈效果等）"""
    return _OPCODE_META.get(opcode.value, {})


def opcode_arg_count(opcode) -> int:
    """计算指令的参数占用的字节数"""
    info = _OPCODE_META.get(opcode.value, {})
    total = 0
    for arg in info.get('args', []):
        if arg == 'byte':
            total += 1
        elif arg == 'short':
            total += 2
        elif arg == 'constant':
            total += 1
    return total
