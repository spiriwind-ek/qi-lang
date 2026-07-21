"""文本库：字符串操作"""
from 环境 import NativeFunction


文本库 = {
    '长度': NativeFunction('长度', 1, lambda s: len(s)),
    '截取': NativeFunction('截取', 3, lambda s, start, end: s[start-1:end]),
    '查找': NativeFunction('查找', 2, lambda s, sub: s.find(sub) + 1),
    '替换': NativeFunction('替换', 3, lambda s, old, new: s.replace(old, new)),
    '转大写': NativeFunction('转大写', 1, lambda s: s.upper()),
    '转小写': NativeFunction('转小写', 1, lambda s: s.lower()),
    '去留白': NativeFunction('去留白', 1, lambda s: s.strip()),
    '分割': NativeFunction('分割', 2, lambda s, sep: s.split(sep)),
    '包含': NativeFunction('包含', 2, lambda s, sub: sub in s),
    '开头': NativeFunction('开头', 2, lambda s, prefix: s.startswith(prefix)),
    '结尾': NativeFunction('结尾', 2, lambda s, suffix: s.endswith(suffix)),
    '重复': NativeFunction('重复', 2, lambda s, n: s * n),
}
