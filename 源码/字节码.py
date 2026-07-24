"""字节码数据结构：Chunk、ObjFunction"""
import struct
from dataclasses import dataclass, field
from typing import Any
from 指令加载器 import OpCode
from 定义加载器 import 编译签名


# ── 安全序列化：类型标签 ──────────────────────────
# 用结构化的二进制格式替代 pickle，不执行任意代码
_TAG_INT = 0
_TAG_FLOAT = 1
_TAG_STR = 2
_TAG_BOOL = 3
_TAG_NONE = 4
_TAG_LIST = 5
_TAG_OBJFUNC = 6


def _pack_value(val: Any) -> bytes:
    """将常量值编码为带类型标签的字节序列"""
    if val is None:
        return struct.pack('<B', _TAG_NONE)
    if isinstance(val, bool):
        return struct.pack('<BB', _TAG_BOOL, 1 if val else 0)
    if isinstance(val, int):
        return struct.pack('<Bq', _TAG_INT, val)
    if isinstance(val, float):
        return struct.pack('<Bd', _TAG_FLOAT, val)
    if isinstance(val, str):
        b = val.encode('utf-8')
        return struct.pack('<BI', _TAG_STR, len(b)) + b
    if isinstance(val, list):
        items = b''.join(_pack_value(item) for item in val)
        return struct.pack('<BI', _TAG_LIST, len(val)) + items
    if hasattr(val, '_serialize_func'):  # ObjFunction
        fb = val._serialize_func()
        return struct.pack('<BI', _TAG_OBJFUNC, len(fb)) + fb
    raise TypeError(f"不支持序列化的类型: {type(val).__name__}")


def _unpack_value(data: bytes, offset: int) -> tuple[Any, int]:
    """从字节序列解码常量值，返回 (值, 新偏移)"""
    tag = data[offset]
    offset += 1
    if tag == _TAG_NONE:
        return None, offset
    if tag == _TAG_BOOL:
        return bool(data[offset]), offset + 1
    if tag == _TAG_INT:
        val = struct.unpack_from('<q', data, offset)[0]
        return val, offset + 8
    if tag == _TAG_FLOAT:
        val = struct.unpack_from('<d', data, offset)[0]
        return val, offset + 8
    if tag == _TAG_STR:
        length = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        val = data[offset:offset + length].decode('utf-8')
        return val, offset + length
    if tag == _TAG_LIST:
        count = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        items = []
        for _ in range(count):
            item, offset = _unpack_value(data, offset)
            items.append(item)
        return items, offset
    if tag == _TAG_OBJFUNC:
        length = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        func = ObjFunction._deserialize_func(data[offset:offset + length])
        return func, offset + length
    raise ValueError(f"未知的类型标签: {tag}")


def _pack_bytes_list(arr: list[int]) -> bytes:
    """将整数列表（值范围 0-255）打包为字节序列"""
    return struct.pack('<I', len(arr)) + bytes(arr)


def _unpack_bytes_list(data: bytes, offset: int) -> tuple[list[int], int]:
    """从字节序列解包整数列表"""
    length = struct.unpack_from('<I', data, offset)[0]
    offset += 4
    vals = list(data[offset:offset + length])
    return vals, offset + length


# ── 数据结构 ──────────────────────────────────────


@dataclass
class Chunk:
    """字节码块"""
    code: list[int] = field(default_factory=list)     # 指令 + 参数
    constants: list[Any] = field(default_factory=list) # 常量池
    lines: list[int] = field(default_factory=list)     # 行号表（与 code 一一对应）
    max_slot: int = 0                                   # 最大局部变量槽数
    
    def emit_byte(self, byte: int, line: int):
        """发射一个字节（指令或参数）"""
        self.code.append(byte)
        self.lines.append(line)
    
    def emit_op(self, opcode: OpCode, line: int):
        """发射一条指令（不带参数）"""
        self.emit_byte(opcode.value, line)
    
    def emit_constant(self, value: Any, line: int):
        """在常量池中添加值，发射 CONSTANT 指令"""
        idx = self.add_constant(value)
        self.emit_op(OpCode.CONSTANT, line)
        self.emit_byte(idx, line)
        return idx
    
    def add_constant(self, value: Any) -> int:
        """向常量池添加值，返回索引"""
        self.constants.append(value)
        return len(self.constants) - 1
    
    def emit_jump(self, opcode: OpCode, line: int) -> int:
        """发射跳转指令（占位2字节），返回补丁位置"""
        self.emit_op(opcode, line)
        self.emit_byte(0xff, line)  # 占位高位
        self.emit_byte(0xff, line)  # 占位低位
        return len(self.code) - 2  # 返回 offset 起始位置
    
    def patch_jump(self, offset_pos: int):
        """回填跳转 offset"""
        jump = len(self.code) - offset_pos - 2
        self.code[offset_pos] = (jump >> 8) & 0xff
        self.code[offset_pos + 1] = jump & 0xff
    
    def emit_loop(self, loop_start: int, line: int):
        """发射循环回跳指令"""
        offset = len(self.code) + 3 - loop_start
        self.emit_op(OpCode.LOOP, line)
        self.emit_byte((offset >> 8) & 0xff, line)
        self.emit_byte(offset & 0xff, line)

    # ── 序列化 ──────────────────────────────────────

    def serialize(self) -> bytes:
        """将 Chunk 序列化为字节流（.简令 格式）。
        
        使用自定义二进制格式（非 pickle），不执行任意代码。
        格式：[签名][max_slot][code_len][code...][lines_len][lines...]
              [常量数量][常量1][常量2]...
        """
        parts = [
            编译签名,
            struct.pack('<I', self.max_slot),
            _pack_bytes_list(self.code),
            _pack_bytes_list(self.lines),
            struct.pack('<I', len(self.constants)),
        ]
        for c in self.constants:
            parts.append(_pack_value(c))
        return b''.join(parts)

    @staticmethod
    def deserialize(data: bytes) -> 'Chunk':
        """从字节流反序列化 Chunk（安全，不执行代码）"""
        sig = 编译签名
        if data[:len(sig)] != sig:
            raise ValueError("不是有效的 .简令 文件")
        offset = len(sig)

        max_slot = struct.unpack_from('<I', data, offset)[0]
        offset += 4

        code, offset = _unpack_bytes_list(data, offset)
        lines, offset = _unpack_bytes_list(data, offset)

        const_count = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        constants = []
        for _ in range(const_count):
            val, offset = _unpack_value(data, offset)
            constants.append(val)

        chunk = Chunk()
        chunk.code = code
        chunk.constants = constants
        chunk.lines = lines
        chunk.max_slot = max_slot
        return chunk


@dataclass
class ObjFunction:
    """编译后的函数对象"""
    name: str | None = None
    arity: int = 0
    chunk: Chunk = field(default_factory=Chunk)
    upvalue_count: int = 0
    max_slot: int = 0  # 最大局部变量槽数，用于栈预分配

    def _serialize_func(self) -> bytes:
        """序列化 ObjFunction（递归序列化内部 Chunk）"""
        if self.name is None:
            header = b'\x00'
        else:
            encoded = self.name.encode('utf-8')
            header = b'\x01' + struct.pack('<I', len(encoded)) + encoded
        chunk_bytes = self.chunk.serialize() if self.chunk else b''
        return (
            header +
            struct.pack('<III', self.arity, self.upvalue_count, self.max_slot) +
            struct.pack('<I', len(chunk_bytes)) + chunk_bytes
        )

    @staticmethod
    def _deserialize_func(data: bytes) -> 'ObjFunction':
        """反序列化 ObjFunction"""
        offset = 0
        has_name = data[offset]
        offset += 1
        name = None
        if has_name:
            name_len = struct.unpack_from('<I', data, offset)[0]
            offset += 4
            name = data[offset:offset + name_len].decode('utf-8')
            offset += name_len
        arity, upvalue_count, max_slot = struct.unpack_from('<III', data, offset)
        offset += 12
        chunk_len = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        chunk = Chunk.deserialize(data[offset:offset + chunk_len]) if chunk_len > 0 else Chunk()
        return ObjFunction(name=name, arity=arity, chunk=chunk,
                          upvalue_count=upvalue_count, max_slot=max_slot)


@dataclass
class ObjClosure:
    """闭包：函数 + 捕获的 upvalue"""
    func: ObjFunction
    upvalues: list = field(default_factory=list)


@dataclass
class CallFrame:
    """调用帧"""
    closure: ObjClosure
    ip: int = 0          # 指令指针
    slots: int = 0       # 栈上局部变量基址
