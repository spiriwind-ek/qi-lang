"""奇语言 AST 节点定义

铁律6: 先只实现变量声明、赋值、整数/文本字面量、输出、简单算术，其余留桩。
"""
from dataclasses import dataclass, field
from typing import Any


class Node:
    """AST 节点基类"""
    pass


# ─── 字面量 ───

@dataclass
class NumberLiteral(Node):
    value: float
    is_int: bool = True

@dataclass
class StringLiteral(Node):
    value: str

@dataclass
class BoolLiteral(Node):
    value: bool

@dataclass
class NullLiteral(Node):
    pass

@dataclass
class Identifier(Node):
    name: str


# ─── 变量操作 ───

@dataclass
class VarDecl(Node):
    """令 整数 X 为 10。"""
    type_name: str
    name: str
    value: Node

@dataclass
class VarAssign(Node):
    """设 X 为 20。"""
    name: str
    value: Node


# ─── 运算 ───

@dataclass
class BinaryOp(Node):
    left: Node
    op: str
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class TernaryOp(Node):
    condition: Node
    then_val: Node
    else_val: Node


# ─── 输出 ───

@dataclass
class PrintStatement(Node):
    value: Node


# ─── 输入（桩） ───

@dataclass
class InputStatement(Node):
    prompt: Node


# ─── 控制流（桩） ───

@dataclass
class IfStatement(Node):
    condition: Node
    then_block: 'Block'
    elifs: list = field(default_factory=list)
    else_block: 'Block | None' = None

@dataclass
class WhileLoop(Node):
    condition: Node
    body: 'Block'

@dataclass
class RepeatLoop(Node):
    count: Node
    body: 'Block'

@dataclass
class ForEachLoop(Node):
    item_name: str
    list_name: str
    body: 'Block'


# ─── 函数（桩） ───

@dataclass
class FuncDecl(Node):
    return_type: str
    name: str
    params: list  # [(type, name), ...]
    body: 'Block'

@dataclass
class FuncCall(Node):
    name: str
    args: list

@dataclass
class ReturnStatement(Node):
    value: Node | None = None


# ─── 结构体（桩） ───

@dataclass
class StructDecl(Node):
    name: str
    fields: list  # [(type, name), ...]

@dataclass
class StructInstantiate(Node):
    struct_type: str
    name: str
    args: list

@dataclass
class MemberAccess(Node):
    object_name: str
    member_name: str

@dataclass
class MethodCall(Node):
    object_name: str
    method_name: str
    args: list

@dataclass
class MemberAssign(Node):
    object_name: str
    member_name: str
    value: Node


# ─── 列表（桩） ───

@dataclass
class ListDecl(Node):
    element_type: str
    name: str
    elements: list

@dataclass
class ListAccess(Node):
    name: str
    index: Node

@dataclass
class ListAssign(Node):
    name: str
    index: Node
    value: Node

@dataclass
class ListLength(Node):
    name: str


# ─── 模块（桩） ───

@dataclass
class IncludeStatement(Node):
    path: str


# ─── 代码块和程序 ───

@dataclass
class Block(Node):
    statements: list

@dataclass
class Program(Node):
    statements: list
