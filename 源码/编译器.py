"""AST 编译器：遍历 AST 生成字节码 Chunk"""
from 语法树 import *
from 字节码 import Chunk, ObjFunction, ObjClosure
from 指令加载器 import OpCode


class CompileError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(f"【第 {line} 行】{msg}" if line else msg)
        self.line = line


class Compiler:
    """AST → 字节码 编译器"""
    
    def __init__(self, structs=None, enclosing=None, globals_set=None):
        self.chunk = Chunk()
        self.func = ObjFunction()
        self.scope_depth = 0
        self.locals = []
        self._structs = structs or {}
        self._last_line = 0
        self._enclosing = enclosing
        self._upvalues = []
        self._globals = globals_set or set()  # 已声明的全局变量名集合
    
    def compile(self, node) -> Chunk:
        """编译 AST 根节点，返回 Chunk"""
        self._compile_node(node)
        self._emit_op(OpCode.NIL, 0)     # 默认返回值
        self._emit_op(OpCode.RETURN, 0)
        self.chunk.max_slot = self.func.max_slot
        return self.chunk
    
    # ─── 工具方法 ───
    
    def _get_line(self, node) -> int:
        """从 AST 节点获取行号（尽量提供）"""
        line = getattr(node, 'line', 0)
        if line:
            self._last_line = line
        return self._last_line
    
    def _emit_op(self, opcode: OpCode, line: int):
        self.chunk.emit_op(opcode, line)
    
    def _emit_byte(self, byte: int, line: int):
        self.chunk.emit_byte(byte, line)
    
    def _emit_constant(self, value, line: int):
        self.chunk.emit_constant(value, line)
    
    def _make_constant(self, value) -> int:
        return self.chunk.add_constant(value)
    
    def _emit_jump(self, opcode: OpCode, line: int) -> int:
        return self.chunk.emit_jump(opcode, line)
    
    def _patch_jump(self, pos: int):
        self.chunk.patch_jump(pos)
    
    def _emit_loop(self, loop_start: int, line: int):
        self.chunk.emit_loop(loop_start, line)
    
    def _error(self, msg: str, line: int = 0):
        raise CompileError(msg, line)
    
    # ─── 主分派 ───
    
    def _compile_node(self, node):
        """根据节点类型分派到对应的编译方法"""
        if isinstance(node, Program):
            self._compile_program(node)
        elif isinstance(node, Block):
            self._compile_block(node)
        elif isinstance(node, VarDecl):
            self._compile_var_decl(node)
        elif isinstance(node, VarAssign):
            self._compile_var_assign(node)
        elif isinstance(node, PrintStatement):
            self._compile_print(node)
        elif isinstance(node, IfStatement):
            self._compile_if(node)
        elif isinstance(node, WhileLoop):
            self._compile_while(node)
        elif isinstance(node, RepeatLoop):
            self._compile_repeat(node)
        elif isinstance(node, ForEachLoop):
            self._compile_foreach(node)
        elif isinstance(node, FuncDecl):
            self._compile_func_decl(node)
        elif isinstance(node, FuncCall):
            self._compile_func_call(node)
        elif isinstance(node, MethodCall):
            self._compile_method_call(node)
        elif isinstance(node, ReturnStatement):
            self._compile_return(node)
        elif isinstance(node, ListDecl):
            self._compile_list_decl(node)
        elif isinstance(node, ListAccess):
            self._compile_list_access(node)
        elif isinstance(node, ListAssign):
            self._compile_list_assign(node)
        elif isinstance(node, ListLength):
            self._compile_list_length(node)
        elif isinstance(node, StructDecl):
            self._compile_struct_decl(node)
        elif isinstance(node, StructInstantiate):
            self._compile_struct_instantiate(node)
        elif isinstance(node, MemberAccess):
            self._compile_member_access(node)
        elif isinstance(node, MemberAssign):
            self._compile_member_assign(node)
        elif isinstance(node, IncludeStatement):
            self._compile_include(node)
        elif isinstance(node, InputStatement):
            self._compile_input(node)
        elif isinstance(node, NumberLiteral):
            # NumberLiteral.value 是字符串（如 "3.14"），需转为数字
            raw = str(node.value)
            val = float(raw) if '.' in raw else int(raw)
            self._emit_constant(val, self._get_line(node))
        elif isinstance(node, StringLiteral):
            self._emit_constant(node.value, self._get_line(node))
        elif isinstance(node, BoolLiteral):
            line = self._get_line(node)
            if node.value == '真':
                self._emit_op(OpCode.TRUE, line)
            else:
                self._emit_op(OpCode.FALSE, line)
        elif isinstance(node, NullLiteral):
            self._emit_op(OpCode.NIL, self._get_line(node))
        elif isinstance(node, Identifier):
            self._compile_identifier(node)
        elif isinstance(node, BinaryOp):
            self._compile_binary(node)
        elif isinstance(node, UnaryOp):
            self._compile_unary(node)
        elif isinstance(node, TernaryOp):
            self._compile_ternary(node)
        else:
            self._error(f"不支持的节点类型: {type(node).__name__}", 0)
    
    # ─── 程序、块 ───
    
    def _compile_program(self, node: Program):
        for stmt in node.statements.statements:
            self._compile_node(stmt)
    
    def _compile_block(self, node: Block):
        for stmt in node.statements:
            self._compile_node(stmt)
    
    # ─── 变量 ───
    
    def _resolve_local(self, name: str) -> int | None:
        """查找局部变量 slot"""
        for i in range(len(self.locals) - 1, -1, -1):
            if self.locals[i][0] == name:
                return i
        return None
    
    def _add_upvalue(self, index: int, is_local: bool) -> int:
        """添加 upvalue，返回索引"""
        for i, up in enumerate(self._upvalues):
            if up['index'] == index and up['is_local'] == is_local:
                return i
        self._upvalues.append({'is_local': is_local, 'index': index})
        self.func.upvalue_count = len(self._upvalues)
        return len(self._upvalues) - 1
    
    def _resolve_upvalue(self, name: str) -> int | None:
        """在外层编译器中查找 upvalue"""
        if self._enclosing is None:
            return None
        # 在外层的 locals 中查找
        slot = self._enclosing._resolve_local(name)
        if slot is not None:
            self._enclosing.locals[slot][2] = True  # 标记被捕获
            return self._add_upvalue(slot, True)
        # 在外层的 upvalues 中查找（递归）
        up = self._enclosing._resolve_upvalue(name)
        if up is not None:
            return self._add_upvalue(up, False)
        return None
    
    def _add_local(self, name: str):
        self.locals.append([name, self.scope_depth, False])  # [name, depth, is_captured]
        # 追踪峰值局部变量槽数，用于 VM 栈预分配
        if len(self.locals) > self.func.max_slot:
            self.func.max_slot = len(self.locals)
    
    def _compile_var_decl(self, node: VarDecl):
        line = self._get_line(node)
        self._compile_node(node.value)
        
        if self.scope_depth > 0:
            # 局部变量
            self._add_local(node.name)
            slot = len(self.locals) - 1
            self._emit_op(OpCode.SET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            # 全局变量
            if node.name in self._globals:
                raise CompileError(f"变量 '{node.name}' 已声明", line)
            self._globals.add(node.name)
            name_idx = self._make_constant(node.name)
            self._emit_op(OpCode.DEFINE_GLOBAL, line)
            self._emit_byte(name_idx, line)
    
    def _compile_var_assign(self, node: VarAssign):
        line = self._get_line(node)
        self._compile_node(node.value)
        
        slot = self._resolve_local(node.name)
        if slot is not None:
            self._emit_op(OpCode.SET_LOCAL, line)
            self._emit_byte(slot, line)
            return
        up = self._resolve_upvalue(node.name)
        if up is not None:
            self._emit_op(OpCode.SET_UPVALUE, line)
            self._emit_byte(up, line)
            return
        name_idx = self._make_constant(node.name)
        self._emit_op(OpCode.SET_GLOBAL, line)
        self._emit_byte(name_idx, line)
    
    def _compile_identifier(self, node: Identifier):
        line = self._get_line(node)
        # 先找局部变量
        slot = self._resolve_local(node.name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
            return
        # 再找 upvalue（外层函数的局部变量）
        up = self._resolve_upvalue(node.name)
        if up is not None:
            self._emit_op(OpCode.GET_UPVALUE, line)
            self._emit_byte(up, line)
            return
        # 最后是全局变量
        name_idx = self._make_constant(node.name)
        self._emit_op(OpCode.GET_GLOBAL, line)
        self._emit_byte(name_idx, line)
    
    # ─── 输出 ───
    
    def _compile_print(self, node: PrintStatement):
        line = self._get_line(node)
        self._compile_node(node.value)
        self._emit_op(OpCode.PRINT, line)
    
    # ─── 控制流 ───
    
    def _compile_if(self, node: IfStatement):
        line = self._get_line(node)
        self._compile_node(node.condition)
        
        # else 分支跳转
        else_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
        
        # then 分支
        self._emit_op(OpCode.POP, line)  # 弹出条件值
        self._compile_node(node.then_block)
        
        # then 执行完后跳过 else
        end_jump = self._emit_jump(OpCode.JUMP, line)
        
        # else 分支
        self._patch_jump(else_jump)
        self._emit_op(OpCode.POP, line)  # 弹出条件值
        if node.else_block:
            self._compile_node(node.else_block)
        
        self._patch_jump(end_jump)
    
    def _compile_while(self, node: WhileLoop):
        line = self._get_line(node)
        loop_start = len(self.chunk.code)
        self._compile_node(node.condition)
        
        exit_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
        self._emit_op(OpCode.POP, line)
        self._compile_node(node.body)
        self._emit_loop(loop_start, line)
        
        self._patch_jump(exit_jump)
        self._emit_op(OpCode.POP, line)
    
    def _compile_repeat(self, node: RepeatLoop):
        line = self._get_line(node)
        self._compile_node(node.count)
        counter_slot = len(self.locals)
        self._add_local('__计数器__')
        self._emit_op(OpCode.SET_LOCAL, line)
        self._emit_byte(counter_slot, line)
        # 不 POP——slot 0 的值留在栈底供 GET_LOCAL 读取
        
        loop_start = len(self.chunk.code)
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(counter_slot, line)
        self._emit_constant(0, line)
        self._emit_op(OpCode.GREATER, line)
        exit_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
        self._emit_op(OpCode.POP, line)
        
        self._compile_node(node.body)
        
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(counter_slot, line)
        self._emit_constant(1, line)
        self._emit_op(OpCode.SUBTRACT, line)
        self._emit_op(OpCode.SET_LOCAL, line)
        self._emit_byte(counter_slot, line)
        
        self._emit_loop(loop_start, line)
        
        self._patch_jump(exit_jump)
        self._emit_op(OpCode.POP, line)  # 弹出条件值
        # 清理栈上残留的局部变量槽值
        self._emit_op(OpCode.POP, line)
        self.locals.pop()
    
    def _compile_foreach(self, node: ForEachLoop):
        """编译 foreach：对 列表 的 每个 X"""
        line = self._get_line(node)
        slot = self._resolve_local(node.list_name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.list_name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        
        list_slot = len(self.locals)
        self._add_local('__列表__')
        self._emit_op(OpCode.SET_LOCAL, line)
        self._emit_byte(list_slot, line)
        self._emit_op(OpCode.POP, line)  # 弹出 SET_LOCAL 留下的值
        
        index_slot = len(self.locals)
        self._add_local('__索引__')
        self._emit_constant(1, line)
        self._emit_op(OpCode.SET_LOCAL, line)
        self._emit_byte(index_slot, line)
        self._emit_op(OpCode.POP, line)  # 弹出 SET_LOCAL 留下的值
        
        loop_start = len(self.chunk.code)
        
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(index_slot, line)
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(list_slot, line)
        len_idx = self._make_constant('长度')
        self._emit_op(OpCode.INVOKE, line)
        self._emit_byte(len_idx, line)
        self._emit_byte(0, line)
        self._emit_op(OpCode.GREATER, line)
        self._emit_op(OpCode.NOT, line)
        exit_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
        self._emit_op(OpCode.POP, line)
        
        # 获取当前元素
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(list_slot, line)
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(index_slot, line)
        self._emit_op(OpCode.INDEX_GET, line)
        
        item_slot = len(self.locals)
        self._add_local(node.item_name)
        self._emit_op(OpCode.SET_LOCAL, line)
        self._emit_byte(item_slot, line)
        
        self._compile_node(node.body)
        
        self.locals.pop()  # 弹出 item 局部变量
        self._emit_op(OpCode.POP, line)  # 弹出 item 栈上值
        
        # 索引 += 1
        self._emit_op(OpCode.GET_LOCAL, line)
        self._emit_byte(index_slot, line)
        self._emit_constant(1, line)
        self._emit_op(OpCode.ADD, line)
        self._emit_op(OpCode.SET_LOCAL, line)
        self._emit_byte(index_slot, line)
        self._emit_op(OpCode.POP, line)  # 弹出 SET_LOCAL 留下的值
        
        self._emit_loop(loop_start, line)
        
        self._patch_jump(exit_jump)
        self._emit_op(OpCode.POP, line)  # 弹出退出时的条件值
        self.locals.pop()  # 弹出 __列表__
        self.locals.pop()  # 弹出 __索引__
    
    # ─── 函数 ───
    
    def _compile_func_decl(self, node: FuncDecl):
        """编译函数定义：创建独立 ObjFunction，用 CLOSURE 包装"""
        line = self._get_line(node)
        
        # 创建嵌套编译器编译函数体，传递已声明的全局变量集合
        child = Compiler(structs=self._structs, enclosing=self, globals_set=self._globals)
        child._last_line = self._last_line
        child.func.name = node.name
        child.func.arity = len(node.params)
        child.scope_depth = 1
        
        # 注册参数为局部变量（slot 0, 1, 2, ...）
        for (ptype, pname) in node.params:
            child._add_local(pname)
        
        # 编译函数体
        child._compile_node(node.body)
        
        # 函数体末尾加默认 RETURN
        child._emit_op(OpCode.NIL, line)
        child._emit_op(OpCode.RETURN, line)
        
        # 创建 ObjFunction
        child.func.chunk = child.chunk
        child.func.upvalue_count = len(child._upvalues)
        
        # 主程序：CLOSURE + upvalue 信息 + DEFINE_GLOBAL
        func_idx = self._make_constant(child.func)
        self._emit_op(OpCode.CLOSURE, line)
        self._emit_byte(func_idx, line)
        # 为每个 upvalue 发射信息
        for up in child._upvalues:
            self._emit_byte(1 if up['is_local'] else 0, line)
            self._emit_byte(up['index'], line)
        
        if node.name in self._globals:
            raise CompileError(f"变量 '{node.name}' 已声明", line)
        self._globals.add(node.name)
        name_idx = self._make_constant(node.name)
        self._emit_op(OpCode.DEFINE_GLOBAL, line)
        self._emit_byte(name_idx, line)
    
    def _compile_func_call(self, node: FuncCall):
        line = self._get_line(node)
        # 先加载函数到栈底
        slot = self._resolve_local(node.name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        # 再编译参数（栈上：函数, 参数1, 参数2...）
        for arg in node.args:
            self._compile_node(arg)
        # 调用
        self._emit_op(OpCode.CALL, line)
        self._emit_byte(len(node.args), line)
    
    def _compile_method_call(self, node: MethodCall):
        line = self._get_line(node)
        # 加载模块
        slot = self._resolve_local(node.object_name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.object_name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        # 编译参数
        for arg in node.args:
            self._compile_node(arg)
        # 调用方法
        method_idx = self._make_constant(node.method_name)
        self._emit_op(OpCode.INVOKE, line)
        self._emit_byte(method_idx, line)
        self._emit_byte(len(node.args), line)
    
    def _compile_return(self, node: ReturnStatement):
        line = self._get_line(node)
        if node.value:
            self._compile_node(node.value)
        else:
            self._emit_op(OpCode.NIL, line)
        self._emit_op(OpCode.RETURN, line)
    
    # ─── 列表 ───
    
    def _compile_list_decl(self, node: ListDecl):
        line = self._get_line(node)
        # 编译每个元素
        for elem in node.elements:
            self._compile_node(elem)
        # 构建列表
        self._emit_op(OpCode.BUILD_LIST, line)
        self._emit_byte(len(node.elements), line)
        # 定义变量
        if node.name in self._globals:
            raise CompileError(f"变量 '{node.name}' 已声明", line)
        self._globals.add(node.name)
        name_idx = self._make_constant(node.name)
        self._emit_op(OpCode.DEFINE_GLOBAL, line)
        self._emit_byte(name_idx, line)
    
    def _compile_list_access(self, node: ListAccess):
        line = self._get_line(node)
        slot = self._resolve_local(node.name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        self._compile_node(node.index)
        self._emit_op(OpCode.INDEX_GET, line)
    
    def _compile_list_assign(self, node: ListAssign):
        line = self._get_line(node)
        slot = self._resolve_local(node.name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        self._compile_node(node.index)
        self._compile_node(node.value)
        self._emit_op(OpCode.INDEX_SET, line)
    
    def _compile_list_length(self, node: ListLength):
        line = self._get_line(node)
        slot = self._resolve_local(node.name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        # 用 INVOKE 调用长度方法
        method_idx = self._make_constant('长度')
        self._emit_op(OpCode.INVOKE, line)
        self._emit_byte(method_idx, line)
        self._emit_byte(0, line)
    
    # ─── 结构体 ───
    
    def _compile_struct_decl(self, node: StructDecl):
        self._structs[node.name] = node.fields
    
    def _compile_struct_instantiate(self, node: StructInstantiate):
        line = self._get_line(node)
        fields = self._structs.get(node.struct_type, [])
        if not fields:
            self._error(f"未定义的结构体 '{node.struct_type}'", line)
            return
        # 编译所有参数值，栈上为 [val1, val2, ...]
        for arg in node.args:
            self._compile_node(arg)
        # 用 BUILD_STRUCT 构建字典
        field_names = [f[1] for f in fields]
        fn_idx = self._make_constant(field_names)
        self._emit_op(OpCode.BUILD_STRUCT, line)
        self._emit_byte(len(node.args), line)
        self._emit_byte(fn_idx, line)
        # 定义全局变量
        name_idx = self._make_constant(node.name)
        self._emit_op(OpCode.DEFINE_GLOBAL, line)
        self._emit_byte(name_idx, line)
    
    def _compile_member_access(self, node: MemberAccess):
        line = self._get_line(node)
        # 加载对象
        slot = self._resolve_local(node.object_name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.object_name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        # 读取属性
        prop_idx = self._make_constant(node.member_name)
        self._emit_op(OpCode.GET_PROP, line)
        self._emit_byte(prop_idx, line)
    
    def _compile_member_assign(self, node: MemberAssign):
        line = self._get_line(node)
        slot = self._resolve_local(node.object_name)
        if slot is not None:
            self._emit_op(OpCode.GET_LOCAL, line)
            self._emit_byte(slot, line)
        else:
            name_idx = self._make_constant(node.object_name)
            self._emit_op(OpCode.GET_GLOBAL, line)
            self._emit_byte(name_idx, line)
        self._compile_node(node.value)
        prop_idx = self._make_constant(node.member_name)
        self._emit_op(OpCode.SET_PROP, line)
        self._emit_byte(prop_idx, line)
    
    # ─── 输入 ───
    
    def _compile_input(self, node: InputStatement):
        line = self._get_line(node)
        if node.prompt:
            self._compile_node(node.prompt)
        else:
            self._emit_constant("", line)
        self._emit_op(OpCode.INPUT, line)
        # 把输入值存入 _input 全局变量（与 AST 解释器行为一致）
        self._emit_op(OpCode.DUP, line)
        self._emit_constant("_input", line)
        self._emit_op(OpCode.DEFINE_GLOBAL, line)
    
    # ─── Include ───
    
    def _compile_include(self, node: IncludeStatement):
        """包括：独立编译被包含文件为独立模块（方案A）
        
        生成 CLOSURE + CALL 指令，使被包含文件在独立帧栈中运行，
        避免栈污染。
        """
        line = self._get_line(node)
        path = getattr(node.path, 'value', None)
        if path and isinstance(path, str):
            import os
            # 安全检查
            if os.path.isabs(path):
                raise CompileError(f"不允许使用绝对路径: {path}")
            real_path = os.path.realpath(os.path.join(os.getcwd(), path))
            work_dir = os.path.realpath(os.getcwd())
            if not real_path.startswith(work_dir + os.sep) and real_path != work_dir:
                raise CompileError(f"不允许访问工作目录外的文件: {path}")
            if os.path.exists(real_path):
                with open(real_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                from 词法分析器 import Lexer
                from 语法分析器 import Parser
                tokens = Lexer(source).tokenize()
                ast = Parser(tokens).parse()
                
                # 独立编译：子编译器生成独立 ObjFunction（方案A）
                child = Compiler(
                    structs=self._structs, enclosing=self,
                    globals_set=self._globals
                )
                child._last_line = self._last_line
                child.func.name = path
                child.scope_depth = 0
                child_chunk = child.compile(ast)
                child.func.chunk = child_chunk
                child.func.upvalue_count = len(child._upvalues)
                
                # CLOSURE: 包装为可调用闭包
                func_idx = self._make_constant(child.func)
                self._emit_op(OpCode.CLOSURE, line)
                self._emit_byte(func_idx, line)
                for upvalue in child._upvalues:
                    self._emit_byte(1 if upvalue.is_local else 0, line)
                    self._emit_byte(upvalue.index, line)
                
                # CALL: 执行模块（0 参数）
                self._emit_op(OpCode.CALL, line)
                self._emit_byte(0, line)
                # POP: 丢弃模块返回值
                self._emit_op(OpCode.POP, line)
                return
        
        # 动态路径（无法在编译时解析）：保留旧行为
        self._compile_node(node.path)
        self._emit_op(OpCode.POP, line)
    
    # ─── 运算 ───
    
    def _compile_binary(self, node: BinaryOp):
        line = self._get_line(node)
        
        # 短路逻辑运算符单独处理（不预编译 right）
        if node.op in ('且', '或'):
            if node.op == '且':
                # a 且 b：a 假则短路推 False；a 真则求 b 的值
                self._compile_node(node.left)
                end_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
                self._emit_op(OpCode.POP, line)
                self._compile_node(node.right)
                patch_false = self._emit_jump(OpCode.JUMP, line)
                self._patch_jump(end_jump)
                self._emit_op(OpCode.POP, line)
                self._emit_op(OpCode.FALSE, line)
                self._patch_jump(patch_false)
            else:  # 或
                # a 或 b：a 真则短路推 True；a 假则求 b 的值
                self._compile_node(node.left)
                else_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
                self._emit_op(OpCode.POP, line)
                self._emit_op(OpCode.TRUE, line)
                end_jump = self._emit_jump(OpCode.JUMP, line)
                self._patch_jump(else_jump)
                self._emit_op(OpCode.POP, line)
                self._compile_node(node.right)
                self._patch_jump(end_jump)
            return
        
        # 非短路运算符：预编译左右两侧
        self._compile_node(node.left)
        self._compile_node(node.right)
        
        op_map = {
            '加': OpCode.ADD,
            '减': OpCode.SUBTRACT,
            '乘': OpCode.MULTIPLY,
            '除': OpCode.DIVIDE,
            '等于': OpCode.EQUAL,
            '不等于': None,
            '大于': OpCode.GREATER,
            '小于': OpCode.LESS,
            '大于等于': None,
            '小于等于': None,
            '抑或': None,
        }
        
        op = op_map.get(node.op)
        if op:
            self._emit_op(op, line)
        elif node.op == '不等于':
            self._emit_op(OpCode.EQUAL, line)
            self._emit_op(OpCode.NOT, line)
        elif node.op == '大于等于':
            self._emit_op(OpCode.LESS, line)
            self._emit_op(OpCode.NOT, line)
        elif node.op == '小于等于':
            self._emit_op(OpCode.GREATER, line)
            self._emit_op(OpCode.NOT, line)
        elif node.op == '抑或':
            self._emit_op(OpCode.EQUAL, line)
            self._emit_op(OpCode.NOT, line)
        else:
            self._error(f"不支持的操作符: {node.op}", line)
    
    def _compile_unary(self, node: UnaryOp):
        line = self._get_line(node)
        self._compile_node(node.operand)
        if node.op == '非':
            self._emit_op(OpCode.NOT, line)
        elif node.op == '-':
            self._emit_op(OpCode.NEGATE, line)
        else:
            self._error(f"不支持的一元运算符: {node.op}", line)
    
    def _compile_ternary(self, node: TernaryOp):
        line = self._get_line(node)
        self._compile_node(node.condition)
        
        # 假则跳转到 else
        else_jump = self._emit_jump(OpCode.JUMP_IF_FALSE, line)
        self._emit_op(OpCode.POP, line)
        self._compile_node(node.then_val)
        
        end_jump = self._emit_jump(OpCode.JUMP, line)
        
        self._patch_jump(else_jump)
        self._emit_op(OpCode.POP, line)
        self._compile_node(node.else_val)
        
        self._patch_jump(end_jump)
