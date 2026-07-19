"""字节码数据结构：Chunk、ObjFunction"""
from dataclasses import dataclass, field
from typing import Any
from 指令加载器 import OpCode


@dataclass
class Chunk:
    """字节码块"""
    code: list[int] = field(default_factory=list)     # 指令 + 参数
    constants: list[Any] = field(default_factory=list) # 常量池
    lines: list[int] = field(default_factory=list)     # 行号表（与 code 一一对应）
    
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
        # offset = 当前指令位置 + 3(LOOP指令长度) - 循环开始位置
        offset = len(self.code) + 3 - loop_start
        self.emit_op(OpCode.LOOP, line)
        self.emit_byte((offset >> 8) & 0xff, line)
        self.emit_byte(offset & 0xff, line)


@dataclass
class ObjFunction:
    """编译后的函数对象"""
    name: str | None = None
    arity: int = 0
    chunk: Chunk = field(default_factory=Chunk)
    upvalue_count: int = 0


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
