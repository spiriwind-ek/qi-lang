"""奇语言 解释器"""
from ast_nodes import *
from environment import Environment
from tokens import TokenType


# 友好错误提示
RUNTIME_ERROR_MESSAGES = {
    '未定义': "变量未定义。请先用「令」声明变量。",
    '已存在': "变量已存在。请使用「设」修改变量值。",
    '除零': "除零错误。除数不能为零。",
    '循环超过最大迭代次数': "疑似无限循环。请检查循环条件。",
    '函数未定义': "函数未定义。请先定义函数。",
    '期望 N 个参数': "参数数量不匹配。请检查函数调用。",
    '索引越界': "索引超出范围。列表索引从1开始。",
    '文件不存在': "文件不存在。请检查文件路径。",
    '不是列表': "变量不是列表。请检查变量类型。",
    '不是结构体': "变量不是结构体。请检查变量类型。",
    '成员未定义': "结构体成员未定义。请检查结构体字段。",
}


class RuntimeError(Exception):
    def __init__(self, msg):
        # 尝试提供友好的错误提示
        for key, friendly in RUNTIME_ERROR_MESSAGES.items():
            if key in msg:
                super().__init__(f"{msg}\n提示: {friendly}")
                return
        super().__init__(msg)

class ReturnSignal(Exception):
    """函数返回信号，用于从函数体中提前退出"""
    def __init__(self, value):
        self.value = value


class Interpreter:
    def __init__(self):
        self.env = Environment()
        self.output = []

    def run(self, source: str):
        from lexer import Lexer
        from parser import Parser

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.execute(ast)
        return self.output

    def execute(self, node):
        if isinstance(node, Program):
            for stmt in node.statements.statements:
                self.execute(stmt)

        elif isinstance(node, Block):
            for stmt in node.statements:
                self.execute(stmt)

        elif isinstance(node, VarDecl):
            value = self.evaluate(node.value)
            self.env.declare_var(node.name, value, node.type_name)

        elif isinstance(node, VarAssign):
            value = self.evaluate(node.value)
            self.env.assign_var(node.name, value)

        elif isinstance(node, FuncDecl):
            self.env.declare_func(node.name, node)

        elif isinstance(node, ReturnStatement):
            value = self.evaluate(node.value)
            raise ReturnSignal(value)

        elif isinstance(node, PrintStatement):
            value = self.evaluate(node.value)
            self.output.append(str(value))

        elif isinstance(node, InputStatement):
            prompt = self.evaluate(node.prompt) if node.prompt else ""
            try:
                value = input(prompt)
            except EOFError:
                value = ""
            self.env.declare_var("_input", value, "文本")

        elif isinstance(node, IfStatement):
            condition = self.evaluate(node.condition)
            if condition:
                self.execute(node.then_block)
            elif node.else_block:
                self.execute(node.else_block)

        elif isinstance(node, WhileLoop):
            max_iter = 100000
            count = 0
            while self.evaluate(node.condition):
                self.execute(node.body)
                count += 1
                if count > max_iter:
                    raise RuntimeError("循环超过最大迭代次数（100000），疑似无限循环")

        elif isinstance(node, RepeatLoop):
            times = self.evaluate(node.count)
            for _ in range(times):
                self.execute(node.body)

        elif isinstance(node, FuncCall):
            self.call_func(node)

        elif isinstance(node, IncludeStatement):
            path = self.evaluate(node.path)
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            from lexer import Lexer
            from parser import Parser
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            self.execute(ast)

        elif isinstance(node, ListDecl):
            elements = [self.evaluate(e) for e in node.elements]
            self.env.declare_var(node.name, elements, node.element_type)

        elif isinstance(node, StructDecl):
            self.env.declare_struct(node.name, node.fields)

        elif isinstance(node, StructInstantiate):
            struct_fields = self.env.get_struct(node.struct_type)
            values = [self.evaluate(arg) for arg in node.args]
            obj = dict(zip([f[1] for f in struct_fields], values))
            self.env.declare_var(node.name, obj, node.struct_type)

        elif isinstance(node, MemberAssign):
            obj = self.env.get_var(node.object_name)
            if not isinstance(obj, dict):
                raise RuntimeError(f"变量 '{node.object_name}' 不是结构体")
            value = self.evaluate(node.value)
            obj[node.member_name] = value

        elif isinstance(node, ListDecl):
            elements = [self.evaluate(e) for e in node.elements]
            self.env.declare_var(node.name, elements, node.type_name)

        else:
            raise RuntimeError(f"不支持的语句: {type(node).__name__}")

    def evaluate(self, node):
        if isinstance(node, NumberLiteral):
            return float(node.value) if '.' in node.value else int(node.value)

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, BoolLiteral):
            return node.value == '真'

        if isinstance(node, NullLiteral):
            return None

        if isinstance(node, Identifier):
            return self.env.get_var(node.name)

        if isinstance(node, BinaryOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if node.op == '加':
                return left + right
            if node.op == '减':
                return left - right
            if node.op == '乘':
                return left * right
            if node.op == '除':
                if right == 0:
                    raise RuntimeError("算术除零")
                return left / right
            if node.op == '等于':
                return left == right
            if node.op == '不等于':
                return left != right
            if node.op == '大于':
                return left > right
            if node.op == '小于':
                return left < right
            if node.op == '大于等于':
                return left >= right
            if node.op == '小于等于':
                return left <= right
            if node.op == '且':
                return left and right
            if node.op == '或':
                return left or right
            if node.op == '抑或':
                return bool(left) ^ bool(right)

        if isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand)
            if node.op == '非':
                return not operand
            raise RuntimeError(f"不支持的一元运算: {node.op}")

        if isinstance(node, FuncCall):
            return self.call_func(node)

        if isinstance(node, ListAccess):
            lst = self.env.get_var(node.name)
            if not isinstance(lst, list):
                raise RuntimeError(f"变量 '{node.name}' 不是列表")
            idx = self.evaluate(node.index)
            if not isinstance(idx, int):
                raise RuntimeError(f"列表索引必须是整数，得到 {type(idx).__name__}")
            # 1-based 转 0-based
            if idx < 1 or idx > len(lst):
                raise RuntimeError(f"索引 {idx} 越界，列表长度为 {len(lst)}")
            return lst[idx - 1]

        if isinstance(node, ListLength):
            lst = self.env.get_var(node.name)
            if not isinstance(lst, list):
                raise RuntimeError(f"变量 '{node.name}' 不是列表")
            return len(lst)

        if isinstance(node, MemberAccess):
            obj = self.env.get_var(node.object_name)
            if not isinstance(obj, dict):
                raise RuntimeError(f"变量 '{node.object_name}' 不是结构体")
            if node.member_name not in obj:
                raise RuntimeError(f"结构体 '{node.object_name}' 没有成员 '{node.member_name}'")
            return obj[node.member_name]

        raise RuntimeError(f"不支持的表达式: {type(node).__name__}")

    def call_func(self, node):
        func = self.env.get_func(node.name)
        if len(node.args) != len(func.params):
            raise RuntimeError(
                f"函数 '{node.name}' 期望 {len(func.params)} 个参数，"
                f"实际传入 {len(node.args)} 个"
            )
        child_env = self.env.child()
        old_env = self.env
        self.env = child_env
        try:
            for (param_type, param_name), arg in zip(func.params, node.args):
                value = self.evaluate(arg)
                self.env.declare_var(param_name, value, param_type)
            self.execute(func.body)
            return None
        except ReturnSignal as ret:
            return ret.value
        finally:
            self.env = old_env
