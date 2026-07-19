"""奇语言 词法记号定义"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    """词法记号类型"""
    # 关键字 — 变量操作
    LET = auto()        # 令（声明变量）
    SET = auto()        # 设（赋值）

    # 关键字 — 控制流
    IF = auto()          # 若
    ELIF = auto()        # 再若
    ELSE = auto()        # 否则
    WHILE = auto()       # 当
    THEN = auto()         # 则
    REPEAT = auto()      # 重复
    FOR_EACH = auto()    # 对（遍历）
    TIMES = auto()       # 次（计数循环）
    END_BLOCK = auto()   # 结束（块终止符）

    # 关键字 — 函数
    RETURN = auto()      # 返回

    # 关键字 — IO
    INPUT = auto()       # 读取
    OUTPUT = auto()      # 输出

    # 关键字 — 布尔
    TRUE = auto()        # 真
    FALSE = auto()       # 假

    # 关键字 — 类型/结构
    STRUCT = auto()      # 结构
    EACH = auto()        # 每项
    IN = auto()          # 于
    INCLUDE = auto()     # 包括
    MEMBER_ACCESS = auto()  # 之
    CONTAINS = auto()       # 含
    LENGTH = auto()         # 长度

    # 类型名
    TYPE_INT = auto()    # 整数
    TYPE_FLOAT = auto()  # 小数
    TYPE_STR = auto()    # 文本
    TYPE_BOOL = auto()   # 布尔
    TYPE_VOID = auto()   # 空
    TYPE_NULL = auto()   # 无
    TYPE_LIST = auto()   # 列

    # 运算符 — 赋值
    ASSIGN = auto()      # 为 / =

    # 运算符 — 比较
    EQ = auto()          # 等于 / ==
    GT = auto()          # 大于 / >
    LT = auto()          # 小于 / <
    GE = auto()          # 大于等于 / >=
    LE = auto()          # 小于等于 / <=
    NE = auto()          # 不等于 / !=

    # 运算符 — 算术
    ADD = auto()         # 加 / +
    SUB = auto()         # 减 / -
    MUL = auto()         # 乘 / *
    DIV = auto()         # 除 / /

    # 运算符 — 逻辑
    AND = auto()         # 且 / &&
    OR = auto()          # 或 / ||
    NOT = auto()         # 非 / !
    XOR = auto()         # 抑或 / ^

    # 标点（归一化后存储半角值）
    DOT = auto()         # 。
    ENUM = auto()        # 、
    COLON = auto()       # ：
    SEMI = auto()        # 承
    LPAREN = auto()      # （ → (
    RPAREN = auto()      # ） → )
    LBRACK = auto()      # [
    RBRACK = auto()      # ]

    # 字面量 / 标识符
    IDENT = auto()       # 标识符
    NUMBER = auto()      # 数字（整数或小数）
    STRING = auto()      # 字符串

    # 特殊
    EOF = auto()         # 文件结束
    NEWLINE = auto()     # 换行


@dataclass
class Token:
    """词法记号"""
    type: TokenType
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}C{self.col})"
