"""列表库：列表操作"""
from 环境 import NativeFunction


列表库 = {
    '排序': NativeFunction('排序', 1, lambda lst: sorted(lst)),
    '反转': NativeFunction('反转', 1, lambda lst: list(reversed(lst))),
    '去重': NativeFunction('去重', 1, lambda lst: list(dict.fromkeys(lst))),
    '拥有': NativeFunction('拥有', 2, lambda lst, item: item in lst),
    '长度': NativeFunction('长度', 1, lambda lst: len(lst)),
}
