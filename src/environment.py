"""奇语言 作用域管理"""
from ast_nodes import Node


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.funcs = {}
        self.structs = {}
        self.parent = parent
    
    def declare_var(self, name, value, type_name):
        if name in self.vars:
            raise RuntimeError(f"变量 '{name}' 已存在，不能再次声明")
        self.vars[name] = {'value': value, 'type': type_name}

    def assign_var(self, name, value):
        if name in self.vars:
            self.vars[name]['value'] = value
        elif self.parent:
            self.parent.assign_var(name, value)
        else:
            raise RuntimeError(f"变量 '{name}' 未定义")

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

    def child(self):
        return Environment(parent=self)
