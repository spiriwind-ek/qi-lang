"""基础库：类型转换、数学运算、基础工具"""
from 环境 import NativeFunction
import math
import random as _random
import time as _time


基础库 = {
    '数值化': NativeFunction('数值化', 1, lambda v: int(v)),
    '文字化': NativeFunction('文字化', 1, lambda v: str(v)),
    '浮点化': NativeFunction('浮点化', 1, lambda v: float(v)),
    '取模': NativeFunction('取模', 1, lambda v: abs(v)),
    '最大值': NativeFunction('最大值', 2, lambda a, b: max(a, b)),
    '最小值': NativeFunction('最小值', 2, lambda a, b: min(a, b)),
    '平方根': NativeFunction('平方根', 1, lambda v: math.sqrt(v)),
    '幂': NativeFunction('幂', 2, lambda a, b: a ** b),
    '正弦': NativeFunction('正弦', 1, lambda v: math.sin(v)),
    '余弦': NativeFunction('余弦', 1, lambda v: math.cos(v)),
    '随机': NativeFunction('随机', 2, lambda a, b: _random.randint(a, b)),
    '随机小数': NativeFunction('随机小数', 0, lambda: _random.random()),
    '等待': NativeFunction('等待', 1, lambda ms: _time.sleep(ms / 1000)),
}
