"""基础库：类型转换、数学运算"""
from 环境 import NativeFunction


基础库 = {
    '数值化': NativeFunction('数值化', 1, lambda v: int(v)),
    '文字化': NativeFunction('文字化', 1, lambda v: str(v)),
    '浮点化': NativeFunction('浮点化', 1, lambda v: float(v)),
    '取模': NativeFunction('取模', 1, lambda v: abs(v)),
    '最大值': NativeFunction('最大值', 2, lambda a, b: max(a, b)),
    '最小值': NativeFunction('最小值', 2, lambda a, b: min(a, b)),
}
