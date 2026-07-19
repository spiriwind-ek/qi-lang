"""奇语言 解释器"""
from 语法树 import *
from 环境 import Environment, NativeFunction
from 记号 import TokenType


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
    def __init__(self, use_vm=False):
        self.env = Environment()
        self.output = []
        self.use_vm = use_vm
        self._加载标准库()

    def _加载标准库(self):
        from 标准库 import 标准库
        for name, module in 标准库.items():
            self.env.declare_module(name, module)

    def run(self, source: str):
        if self.use_vm:
            return self._run_vm(source)
        from 词法分析器 import Lexer
        from 语法分析器 import Parser

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        self.execute(ast)
        return self.output

    def _run_vm(self, source: str):
        """使用字节码 VM 执行"""
        from 词法分析器 import Lexer
        from 语法分析器 import Parser
        from 编译器 import Compiler
        from 虚拟机 import VM

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        compiler = Compiler()
        chunk = compiler.compile(ast)
        vm = VM()
        vm.run(chunk)
        return vm.get_output()

    def execute(self, node):
        if isinstance(node, Program):
            for stmt in node.statements.statements:
                self.execute(stmt)

        elif isinstance(node, Block):
            for stmt in node.statements:
                self.execute(stmt)

        elif isinstance(node, VarDecl):
            value = self.evaluate(node.value)
            type_name = node.type_name
            if type_name is None:
                type_name = self._infer_type(value)
            self.env.declare_var(node.name, value, type_name)

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

        elif isinstance(node, MethodCall):
            self.evaluate(node)

        elif isinstance(node, IncludeStatement):
            import os
            path = self.evaluate(node.path)
            # 绝对路径拒绝
            if os.path.isabs(path):
                raise RuntimeError(f"不允许使用绝对路径: {path}")
            # 相对路径基于当前工作目录解析
            real_path = os.path.realpath(os.path.join(os.getcwd(), path))
            # 限制在当前工作目录内（防止路径遍历）
            work_dir = os.path.realpath(os.getcwd())
            if not real_path.startswith(work_dir + os.sep) and real_path != work_dir:
                raise RuntimeError(f"不允许访问工作目录外的文件: {path}")
            if not os.path.exists(real_path):
                raise RuntimeError(f"文件不存在: {path}")
            # 文件后缀检查
            _, ext = os.path.splitext(real_path)
            from 定义加载器 import 所有后缀
            if ext and ext not in 所有后缀:
                raise RuntimeError(f"不支持的文件后缀 '{ext}'，仅允许: {', '.join(所有后缀)}")
            with open(real_path, 'r', encoding='utf-8') as f:
                source = f.read()
            from 词法分析器 import Lexer
            from 语法分析器 import Parser
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            self.execute(ast)

        elif isinstance(node, ListDecl):
            elements = [self.evaluate(e) for e in node.elements]
            self.env.declare_var(node.name, elements, node.element_type)

        elif isinstance(node, ForEachLoop):
            lst = self.env.get_var(node.list_name)
            if not isinstance(lst, list):
                raise RuntimeError(f"变量 '{node.list_name}' 不是列表")
            for item in lst:
                child = self.env.child()
                old_env = self.env
                self.env = child
                try:
                    self.env.declare_var(node.item_name, item, None)
                    self.execute(node.body)
                finally:
                    self.env = old_env

        elif isinstance(node, ListAssign):
            lst = self.env.get_var(node.name)
            if not isinstance(lst, list):
                raise RuntimeError(f"变量 '{node.name}' 不是列表")
            idx = self.evaluate(node.index)
            if not isinstance(idx, int):
                raise RuntimeError("列表索引必须是整数")
            if idx < 1 or idx > len(lst):
                raise RuntimeError(f"索引 {idx} 越界")
            lst[idx - 1] = self.evaluate(node.value)

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
                result = left / right
                if isinstance(left, int) and isinstance(right, int) and result == int(result):
                    return int(result)
                return result
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
                return bool(left) != bool(right)

        if isinstance(node, TernaryOp):
            cond = self.evaluate(node.condition)
            return self.evaluate(node.then_val if cond else node.else_val)

        if isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand)
            if node.op == '非':
                return not operand
            if node.op == '-':
                return -operand
            raise RuntimeError(f"不支持的一元运算: {node.op}")

        if isinstance(node, ListAccess):
            lst = self.env.get_var(node.name)
            if not isinstance(lst, list):
                raise RuntimeError(f"变量 '{node.name}' 不是列表")
            idx = self.evaluate(node.index)
            if not isinstance(idx, int):
                raise RuntimeError("列表索引必须是整数")
            if idx < 1 or idx > len(lst):
                raise RuntimeError(f"索引 {idx} 越界")
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
                raise RuntimeError(f"结构体没有成员 '{node.member_name}'")
            return obj[node.member_name]

        if isinstance(node, FuncCall):
            return self.call_func(node)

        if isinstance(node, MethodCall):
            module = self.env.get_module(node.object_name)
            method = module.get(node.method_name)
            if method is None:
                raise RuntimeError(f"模块 '{node.object_name}' 中没有方法 '{node.method_name}'")
            if isinstance(method, NativeFunction):
                args = [self.evaluate(a) for a in node.args]
                if len(args) < method.arity:
                    raise RuntimeError(
                        f"模块 '{node.object_name}' 的 '{node.method_name}' "
                        f"至少需要 {method.arity} 个参数，实际传入 {len(args)} 个"
                    )
                return method.impl(*args)
            raise RuntimeError(f"'{node.object_name}的{node.method_name}' 不是可调用的方法")

        raise RuntimeError(f"不支持的表达式: {type(node).__name__}")

    def _infer_type(self, value):
        """从值推断类型"""
        if isinstance(value, bool):
            return '布尔'
        if isinstance(value, int):
            return '整数'
        if isinstance(value, float):
            return '小数'
        if isinstance(value, str):
            return '文本'
        if isinstance(value, list):
            return '列表'
        if isinstance(value, dict):
            return '结构体'
        return '未知'

    def call_func(self, node):
        func = self.env.get_func(node.name)
        if isinstance(func, NativeFunction):
            args = [self.evaluate(a) for a in node.args]
            return func.impl(*args)
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
