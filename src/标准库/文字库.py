"""文字库：字符串操作"""
from 环境 import NativeFunction


文字库 = {
    '长度': NativeFunction('长度', 1, lambda s: len(s)),
    '截取': NativeFunction('截取', 3, lambda s, start, end: s[start-1:end]),
    '查找': NativeFunction('查找', 2, lambda s, sub: s.find(sub) + 1),
    '替换': NativeFunction('替换', 3, lambda s, old, new: s.replace(old, new)),
    '转大写': NativeFunction('转大写', 1, lambda s: s.upper()),
    '转小写': NativeFunction('转小写', 1, lambda s: s.lower()),
    '去留白': NativeFunction('去留白', 1, lambda s: s.strip()),
}
