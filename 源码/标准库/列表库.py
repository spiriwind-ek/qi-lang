"""列表库：列表操作"""
from 环境 import NativeFunction


def _追加(lst, item):
    lst.append(item)
    return lst

def _插入(lst, idx, item):
    lst.insert(idx - 1, item)
    return lst

def _删除(lst, idx):
    del lst[idx - 1]
    return lst


列表库 = {
    '排序': NativeFunction('排序', 1, lambda lst: sorted(lst)),
    '反转': NativeFunction('反转', 1, lambda lst: list(reversed(lst))),
    '去重': NativeFunction('去重', 1, lambda lst: list(dict.fromkeys(lst))),
    '拥有': NativeFunction('拥有', 2, lambda lst, item: item in lst),
    '长度': NativeFunction('长度', 1, lambda lst: len(lst)),
    '追加': NativeFunction('追加', 2, _追加),
    '插入': NativeFunction('插入', 3, _插入),
    '删除': NativeFunction('删除', 2, _删除),
}
