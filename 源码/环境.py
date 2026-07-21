"""奇语言 作用域管理"""

# 统一错误提示（解释器与 VM 共用）
RUNTIME_ERROR_MESSAGES = {
    '未定义': "变量未定义。请先用「令」声明变量。",
    '未定义变量': "变量未定义。请先用「令」声明变量。",
    '已存在': "变量已存在。请使用「设」修改变量值。",
    '除零': "除零错误。除数不能为零。",
    '循环超过最大迭代次数': "疑似无限循环。请检查循环条件。",
    '函数未定义': "函数未定义。请先定义函数。",
    '期望 N 个参数': "参数数量不匹配。请检查函数调用。",
    '参数不匹配': "参数数量不匹配。请检查函数调用。",
    '索引越界': "索引超出范围。列表索引从1开始。",
    '文件不存在': "文件不存在。请检查文件路径。",
    '不是列表': "变量不是列表。请检查变量类型。",
    '不是结构体': "变量不是结构体。请检查变量类型。",
    '成员未定义': "结构体成员未定义。请检查结构体字段。",
    '只能调用函数': "只能调用函数。",
    '类型错误': "类型不匹配。请检查操作数类型。",
}

from 语法树 import Node
from 定义加载器 import 类型名


class NativeFunction:
    """原生函数包装器，用于标准库"""
    def __init__(self, name, arity, impl):
        self.name = name
        self.arity = arity  # 最少参数数量
        self.impl = impl    # Python callable


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.funcs = {}
        self.structs = {}
        self.modules = {}  # 标准库模块
        self.parent = parent
    
    # 标准类型名集合（从配置导入）
    _标准类型 = set(类型名.keys()) | {'列表', '结构体'}

    def declare_var(self, name, value, type_name):
        if name in self.vars:
            raise RuntimeError(f"变量 '{name}' 已存在，不能再次声明")
        # 类型验证（仅标准类型检查，自定义结构体类型跳过，空列表跳过）
        if type_name is not None and type_name in self._标准类型:
            actual = self._infer_type(value)
            if actual != '列表' and actual != type_name:  # 空列表不检查
                raise RuntimeError(f"类型不匹配：期望 {type_name}，得到 {actual}")
        self.vars[name] = {'value': value, 'type': type_name}

    def assign_var(self, name, value):
        if name in self.vars:
            declared = self.vars[name]['type']
            if declared is not None:
                actual = self._infer_type(value)
                if actual != declared:
                    raise RuntimeError(f"类型不匹配：变量 '{name}' 声明为 {declared}，赋值为 {actual}")
            self.vars[name]['value'] = value
        elif self.parent:
            self.parent.assign_var(name, value)
        else:
            raise RuntimeError(f"变量 '{name}' 未定义")

    @staticmethod
    def _infer_type(value):
        if isinstance(value, bool):
            return '布尔'
        if isinstance(value, int):
            return '整数'
        if isinstance(value, float):
            return '小数'
        if isinstance(value, str):
            return '文本'
        if isinstance(value, list):
            if not value:
                return '列表'  # 空列表无法推断元素类型
            first = value[0]
            if isinstance(first, int):
                return '整数列'
            if isinstance(first, float):
                return '小数列'
            if isinstance(first, str):
                return '文本列'
            return '列表'
        if isinstance(value, dict):
            return '结构体'
        return '未知'

    def get_var(self, name):
        if name in self.vars:
            return self.vars[name]['value']
        elif self.parent:
            return self.parent.get_var(name)
        else:
            raise RuntimeError(f"变量 '{name}' 未定义")

    def get_var_type(self, name):
        if name in self.vars:
            return self.vars[name]['type']
        elif self.parent:
            return self.parent.get_var_type(name)
        else:
            raise RuntimeError(f"变量 '{name}' 未定义")
    
    def declare_func(self, name, func_node):
        """注册函数定义"""
        self.funcs[name] = func_node
    
    def get_func(self, name):
        """查找函数定义，沿作用域链向上查找"""
        if name in self.funcs:
            return self.funcs[name]
        elif self.parent:
            return self.parent.get_func(name)
        else:
            raise RuntimeError(f"函数 '{name}' 未定义")
    
    def declare_struct(self, name, fields):
        if name in self.structs:
            raise RuntimeError(f"结构 '{name}' 已定义")
        self.structs[name] = fields
    
    def get_struct(self, name):
        if name in self.structs:
            return self.structs[name]
        elif self.parent:
            return self.parent.get_struct(name)
        else:
            raise RuntimeError(f"结构 '{name}' 未定义")

    def declare_module(self, name, obj):
        self.modules[name] = obj

    def get_module(self, name):
        if name in self.modules:
            return self.modules[name]
        if self.parent:
            return self.parent.get_module(name)
        raise RuntimeError(f"模块 '{name}' 未定义")

    def child(self):
        return Environment(parent=self)
