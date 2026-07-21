"""文件库：VFS 文件操作"""
from 环境 import NativeFunction


class 虚拟文件系统:
    """Python 后端的虚拟文件系统"""
    _mode_map = {'读': 'r', '写': 'w', '追加': 'a'}

    def __init__(self):
        self.handles = {}
        self._next_id = 1

    def 打开(self, path, mode):
        py_mode = self._mode_map.get(mode)
        if py_mode is None:
            raise RuntimeError(f"不支持的文件模式 '{mode}'，仅允许: 读、写、追加")
        f = open(path, py_mode, encoding='utf-8')
        hid = self._next_id
        self._next_id += 1
        self.handles[hid] = f
        return hid

    def 读取(self, handle, size=-1):
        if handle not in self.handles:
            raise RuntimeError(f"无效的文件句柄: {handle}")
        if size == -1:
            return self.handles[handle].read()
        return self.handles[handle].read(size)

    def 写入(self, handle, content):
        if handle not in self.handles:
            raise RuntimeError(f"无效的文件句柄: {handle}")
        self.handles[handle].write(content)

    def 关闭(self, handle):
        if handle not in self.handles:
            raise RuntimeError(f"无效的文件句柄: {handle}")
        self.handles[handle].close()
        del self.handles[handle]


_vfs = 虚拟文件系统()


文件库 = {
    '打开': NativeFunction('打开', 2, lambda path, mode: _vfs.打开(path, mode)),
    '读取': NativeFunction('读取', 1, lambda handle, size=-1: _vfs.读取(handle, size)),
    '写入': NativeFunction('写入', 2, lambda handle, content: _vfs.写入(handle, content)),
    '关闭': NativeFunction('关闭', 1, lambda handle: _vfs.关闭(handle)),
}
