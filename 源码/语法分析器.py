"""奇语言 语法分析器（递归下降）

铁律：
1. 关键字由语法分析器根据上下文判断，词法分析器只输出 IDENT
2. 句号。= DOT 为唯一语句终止符
3. 每个 parse_xxx() 方法从当前 token 开始，返回对应 AST 节点
"""
from 记号 import TokenType, Token
from 关键字 import (
    ALWAYS, STMT_START, AFTER_LET,
    AFTER_PREV, EXPR_KEYWORDS, BIN_OPS, UNARY_OPS,
)
from 语法树 import (
    Program, VarDecl, VarAssign, BinaryOp, TernaryOp, UnaryOp,
    IfStatement, WhileLoop, RepeatLoop, ForEachLoop, FuncDecl, FuncCall,
    ReturnStatement, ListDecl, ListAccess, ListAssign, ListLength,
    StructDecl, StructInstantiate, MemberAccess, MemberAssign, MethodCall,
    IncludeStatement, PrintStatement, InputStatement,
    Block, NumberLiteral, StringLiteral, BoolLiteral, NullLiteral, Identifier,
)


# 友好错误提示
PARSE_ERROR_MESSAGES = {
    'ASSIGN': "变量声明格式：令 整数 名字 为 值。\n例如：令 整数 X 为 10。",
    'DOT': "语句必须以句号结尾。\n例如：令 整数 X 为 10。",
    'COLON': "代码块需要用冒号开始。\n例如：若 条件 则：\n    语句。",
    'LPAREN': "函数参数列表需要左括号。\n例如：令 整数 求和 为（整数 甲、整数 乙）：",
    'RPAREN': "参数列表缺少右括号。",
    'RBRACK': "列表缺少右括号。\n例如：[1、2、3]",
}


class ParseError(Exception):
    def __init__(self, msg, token):
        # 尝试提供友好的错误提示
        friendly = PARSE_ERROR_MESSAGES.get(msg, msg)
        if friendly == msg:
            super().__init__(f"第{token.line}行第{token.col}列: {msg}")
        else:
            super().__init__(f"第{token.line}行第{token.col}列:\n{friendly}")
        self.token = token


# 语句起始 token 集合（用于 _parse_block_body 判断）
STMT_STARTER_TYPES = set(STMT_START.values()) | {TokenType.ELSE, TokenType.ELIF}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self._prev = None  # 上一个已消费 token 的解析后类型

    def _set_line(self, node, token=None):
        """从 token 设置节点行号，默认使用当前 token"""
        tok = token or self.peek()
        node.line = getattr(tok, 'line', 0)
        return node

    # ─── 关键字解析核心 ───

    def _resolve(self, tok):
        """将 IDENT 解析为可能的关键字类型"""
        if tok.type != TokenType.IDENT:
            return tok.type

        value = tok.value

        # 1. 始终关键字（标点级别）
        if value in ALWAYS:
            return ALWAYS[value]

        # 2. 根据上一个已消费 token 的类型判断
        if self._prev in (None, TokenType.DOT, TokenType.COLON, TokenType.SEMI):
            if value in STMT_START:
                return STMT_START[value]

        if self._prev == TokenType.LET:
            if value in AFTER_LET:
                return AFTER_LET[value]

        # COLON / LPAREN 后面也需要识别类型名（结构体字段、函数参数）
        if self._prev in (TokenType.COLON, TokenType.LPAREN, TokenType.ENUM):
            if value in AFTER_LET:
                return AFTER_LET[value]

        if self._prev in AFTER_PREV:
            if value in AFTER_PREV[self._prev]:
                return AFTER_PREV[self._prev][value]

        # 3. 表达式位置的运算符和关键字
        # 在表达式内部，几乎所有 token 后面都可能出现运算符/布尔/则
        # 只有 DOT/COLON/SEMI/EOF 和特定语句起始关键字后面不算表达式位置
        _stmt_start_ctx = {
            TokenType.DOT, TokenType.COLON, TokenType.SEMI,
            TokenType.LET, TokenType.SET,
            TokenType.STRUCT, TokenType.INCLUDE,
            TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STR,
            TokenType.TYPE_BOOL, TokenType.TYPE_VOID, TokenType.TYPE_NULL,
            TokenType.TYPE_LIST,
        }
        if self._prev not in _stmt_start_ctx:
            if value in EXPR_KEYWORDS:
                return EXPR_KEYWORDS[value]
            if value in BIN_OPS:
                return BIN_OPS[value]
            if value in UNARY_OPS:
                return UNARY_OPS[value]

        # 4. 运算符右侧也检查一元运算符（如 `且 非 X`）
        if value in UNARY_OPS:
            return UNARY_OPS[value]

        # 5. 默认：IDENT
        return TokenType.IDENT

    # ─── token 工具 ───

    def peek(self):
        return self.tokens[self.pos]

    def peek_type(self):
        """返回当前 token 的解析后类型"""
        return self._resolve(self.tokens[self.pos])

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        self._prev = self._resolve(tok)
        return tok

    def at(self, *types):
        return self.peek_type() in types

    def expect(self, *types):
        pt = self.peek_type()
        if pt not in types:
            expected_names = '或'.join(t.name for t in types)
            raise ParseError(f"期望 {expected_names}，得到 {pt.name}", self.peek())
        return self.advance()

    def _in_block(self):
        return self.peek_type() in STMT_STARTER_TYPES

    def _parse_block_body(self):
        """解析块：深度计数匹配 。，else/再若 终止。
        
        只在当前层级消费 ；和 。——嵌套块的 。 由各自的 _parse_block_body 处理。
        """
        self.expect(TokenType.COLON)
        depth = 1
        stmts = []
        while depth > 0:
            if self.at(TokenType.ELSE, TokenType.ELIF):
                break
            if self.at(TokenType.COLON):
                depth += 1
                self.advance()
            stmts.append(self.parse_statement())
            if self.at(TokenType.SEMI):
                self.advance()
            elif self.at(TokenType.DOT):
                depth -= 1
                if depth == 0:
                    self.advance()
            else:
                # 控制流语句消费了自己的 。，
                # 下一个 token 不是 ；也不是 。，块结束
                break
        return Block(stmts)

    def _parse_func_body(self) -> Block:
        """解析函数体：多条语句，遇到下一个顶层声明时终止
        
        与 _parse_block_body 不同，函数体不用深度计数，
        因为它没有缩进层级——函数体的结束由"下一个顶层声明"决定。
        LET 特殊处理：嵌套函数定义（FuncDecl）保留，变量声明视为函数体结束。
        
        控制流语句（IF/WHILE/REPEAT）会消费自己的 。，
        语句后若 token 不是 ；也不是 。，则函数体结束。
        """
        stmts = []
        while not self.at(TokenType.EOF):
            if self.at(TokenType.LET):
                saved = self.pos
                saved_prev = self._prev
                stmt = self.parse_let_statement()
                if isinstance(stmt, FuncDecl):
                    stmts.append(stmt)
                    if self.at(TokenType.DOT):
                        self.advance()
                    continue
                self.pos = saved
                self._prev = saved_prev
                break
            stmts.append(self.parse_statement())
            if self.at(TokenType.SEMI):
                self.advance()
            elif self.at(TokenType.DOT):
                self.advance()
                break
            else:
                break
        return Block(stmts)

    # ─── 程序 ───

    def parse(self):
        stmts = []
        while not self.at(TokenType.EOF):
            stmts.append(self.parse_statement())
            if self.at(TokenType.DOT):
                self.advance()
        return Program(Block(stmts))

    # ─── 语句 ───

    def parse_statement(self):
        line = self.peek().line
        if self.at(TokenType.LET):
            return self._set_line(self.parse_let_statement())
        if self.at(TokenType.SET):
            return self._set_line(self.parse_var_assign())
        if self.at(TokenType.IF, TokenType.ELIF):
            return self._set_line(self.parse_if())
        if self.at(TokenType.WHILE):
            return self._set_line(self.parse_while())
        if self.at(TokenType.REPEAT):
            return self._set_line(self.parse_repeat())
        if self.at(TokenType.RETURN):
            return self._set_line(self.parse_return())
        if self.at(TokenType.OUTPUT):
            return self._set_line(self.parse_print())
        if self.at(TokenType.INCLUDE):
            return self._set_line(self.parse_include())
        if self.at(TokenType.INPUT):
            return self._set_line(self.parse_input())
        if self.at(TokenType.IN):
            return self._set_line(self.parse_for_each())
        if self.at(TokenType.INVOKE):
            return self._set_line(self.parse_invoke_statement())
        if self.at(TokenType.IDENT):
            # 先尝试解析为表达式（函数调用或方法调用）
            expr = self.parse_expression()
            if isinstance(expr, (FuncCall, MethodCall)):
                return self._set_line(expr)
            raise ParseError(f"意外的表达式", self.peek())
        tok = self.peek()
        raise ParseError(f"不支持的语句: {tok.value}", tok)

    # ─── 变量声明 / 函数定义 ───

    def parse_let_statement(self):
        """处理所有 令 语句：变量声明、列表声明、结构体声明、结构体实例化"""
        self.expect(TokenType.LET)
        # 结构体声明：令 结构 学生 含：文本 姓名、整数 年龄。
        if self.at(TokenType.STRUCT):
            return self.parse_struct_decl()
        # 列表声明：令 整数列 库存 为 [10、20、30]。
        # 仅当为后面跟 [ 时走列表字面量路径，否则走普通变量声明
        if self.at(TokenType.TYPE_LIST):
            saved = self.pos
            self.advance()  # TYPE_LIST
            self.expect(TokenType.IDENT)  # name
            self.expect(TokenType.ASSIGN)  # 为
            if self.at(TokenType.LBRACK):
                elements = self.parse_list_literal()
                type_tok_val = self.tokens[saved].value
                name_tok_val = self.tokens[saved + 1].value
                return ListDecl(type_tok_val, name_tok_val, elements)
            # 回退，走普通声明路径
            self.pos = saved
            # 重建 _prev 为 LET（因为回退到了 LET 之后的位置）
            self._prev = TokenType.LET
        # 结构体实例化或变量声明：令 TYPE NAME 为 VALUE。
        if self.at(TokenType.IDENT):
            first = self.advance()
            # 类型推断：令 NAME 为 VALUE（下一个 token 是 为）
            if self.at(TokenType.ASSIGN):
                self.expect(TokenType.ASSIGN)
                value = self.parse_expression()
                return VarDecl(None, first.value, value)
            # 结构体实例化：令 TYPE NAME 为 VALUE
            name_tok = self.expect(TokenType.IDENT)
            self.expect(TokenType.ASSIGN)
            value = self.parse_expression()
            if isinstance(value, StructInstantiate):
                value.struct_type = first.value
                value.name = name_tok.value
                return value
            return VarDecl(first.value, name_tok.value, value)
        # 普通类型变量声明或函数定义
        type_tok = self.expect(
            TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STR,
            TokenType.TYPE_BOOL, TokenType.TYPE_VOID, TokenType.TYPE_NULL,
            TokenType.TYPE_LIST,
            TokenType.TRUE, TokenType.FALSE,
        )
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.ASSIGN)  # 为

        # ── 函数定义：为（参数）： ──
        if self.at(TokenType.LPAREN):
            self.advance()  # 消费 (
            params = []
            if not self.at(TokenType.RPAREN):
                while True:
                    ptype = self.expect(
                        TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STR,
                        TokenType.TYPE_BOOL, TokenType.TYPE_NULL,
                    )
                    pname = self.expect(TokenType.IDENT)
                    params.append((ptype.value, pname.value))
                    if not self.at(TokenType.ENUM):
                        break
                    self.advance()  # 消费 、 或 ,
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.COLON)  # ：
            body = self._parse_func_body()
            return FuncDecl(type_tok.value, name_tok.value, params, body)

        # ── 普通变量声明 ──
        value = self.parse_expression()
        return VarDecl(type_tok.value, name_tok.value, value)

    def parse_struct_decl(self):
        """令 结构 学生 含：文本 姓名、整数 年龄。"""
        self.expect(TokenType.STRUCT)
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.CONTAINS)  # 含
        self.expect(TokenType.COLON)     # ：
        fields = []
        # 解析第一个字段
        type_tok = self.expect(TokenType.TYPE_INT, TokenType.TYPE_FLOAT, 
                              TokenType.TYPE_STR, TokenType.TYPE_BOOL)
        field_name = self.expect(TokenType.IDENT)
        fields.append((type_tok.value, field_name.value))
        # 解析后续字段（以、分隔）
        while self.at(TokenType.ENUM):
            self.advance()  # 消费 、
            type_tok = self.expect(TokenType.TYPE_INT, TokenType.TYPE_FLOAT, 
                                  TokenType.TYPE_STR, TokenType.TYPE_BOOL)
            field_name = self.expect(TokenType.IDENT)
            fields.append((type_tok.value, field_name.value))
        return StructDecl(name_tok.value, fields)

    # ─── 变量赋值 ───

    def parse_var_assign(self):
        self.expect(TokenType.SET)
        name_tok = self.expect(TokenType.IDENT)
        # 列表元素赋值：设 列表[INDEX] 为 VALUE
        if self.at(TokenType.LBRACK):
            self.advance()
            index = self.parse_expression()
            self.expect(TokenType.RBRACK)
            self.expect(TokenType.ASSIGN)
            value = self.parse_expression()
            return ListAssign(name_tok.value, index, value)
        # 成员赋值：设 OBJ.MEMBER 为 VALUE
        if self.at(TokenType.MEMBER_ACCESS):
            self.advance()
            member = self.expect(TokenType.IDENT)
            self.expect(TokenType.ASSIGN)
            value = self.parse_expression()
            return MemberAssign(name_tok.value, member.value, value)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()
        return VarAssign(name_tok.value, value)

    # ─── 条件语句 ───

    def parse_if(self):
        """若 condition 则：statement 否则：statement"""
        # 接受 IF(若) 或 ELIF(再若) 作为起始
        if self.at(TokenType.ELIF):
            self.advance()
        else:
            self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.expect(TokenType.THEN)
        then_block = self._parse_block_body()
        else_block = None
        if self.at(TokenType.ELSE):
            self.advance()
            else_block = self._parse_block_body()
        elif self.at(TokenType.ELIF):
            else_block = Block([self.parse_if()])
        return IfStatement(condition=condition, then_block=then_block, else_block=else_block)

    # ─── 条件循环 ───

    def parse_while(self):
        """当 condition 时：statement"""
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        self.expect(TokenType.THEN)
        body = self._parse_block_body()
        return WhileLoop(condition, body)

    # ─── 计数循环 ───

    def parse_repeat(self):
        """重复 N 次：statement。（单语句体）"""
        self.expect(TokenType.REPEAT)
        count = self.parse_expression()
        self.expect(TokenType.TIMES)
        body = self._parse_block_body()
        return RepeatLoop(count, body)

    def parse_for_each(self):
        """对 列表 的 每个 X：statement"""
        self.expect(TokenType.IN)                # 对
        list_tok = self.expect(TokenType.IDENT)  # 列表
        if self.at(TokenType.MEMBER_ACCESS):     # 的（可选）
            self.advance()
        self.expect(TokenType.EACH)              # 每个
        item_tok = self.expect(TokenType.IDENT)  # X
        body = self._parse_block_body()          # ：
        return ForEachLoop(item_tok.value, list_tok.value, body)

    # ─── 返回 ───

    def parse_return(self):
        self.expect(TokenType.RETURN)
        value = self.parse_expression()
        return ReturnStatement(value)

    # ─── 输出 ───

    def parse_print(self):
        """输出 X。"""
        self.expect(TokenType.OUTPUT)
        value = self.parse_expression()
        return PrintStatement(value)

    # ─── 输入 ───

    def parse_input(self):
        """读取（"提示"）。"""
        self.expect(TokenType.INPUT)
        self.expect(TokenType.LPAREN)
        prompt = self.parse_expression() if not self.at(TokenType.RPAREN) else StringLiteral("")
        self.expect(TokenType.RPAREN)
        return InputStatement(prompt)

    # ─── 模块导入 ───

    def parse_include(self):
        self.expect(TokenType.INCLUDE)
        path = self.parse_expression()
        return IncludeStatement(path)

    def parse_invoke_statement(self):
        """调 对象 的 成员 / 调 对象 的 方法（参数）"""
        self.expect(TokenType.INVOKE)        # 调
        expr = self.parse_expression()
        if not isinstance(expr, (MemberAccess, MethodCall, ListLength)):
            raise ParseError("调 后面需要跟成员访问表达式", self.peek())
        return expr

    # ─── 参数列表 ───

    def _parse_args(self):
        """解析参数列表：（expr、expr、...）"""
        self.expect(TokenType.LPAREN)
        args = []
        if not self.at(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.at(TokenType.ENUM):
                self.advance()
                args.append(self.parse_expression())
        self.expect(TokenType.RPAREN)
        return args

    # ─── 表达式 ───

    def parse_expression(self):
        return self.parse_ternary()

    def parse_ternary(self):
        """三元表达式：若 condition 则 A 否则 B"""
        if self.at(TokenType.IF):
            self.advance()
            condition = self.parse_logic_or()
            self.expect(TokenType.THEN)
            then_val = self.parse_ternary()
            self.expect(TokenType.ELSE)
            else_val = self.parse_ternary()
            return TernaryOp(condition, then_val, else_val)
        return self.parse_logic_or()

    def parse_logic_or(self):
        left = self.parse_xor()
        while self.at(TokenType.OR):
            op = self.advance()
            right = self.parse_xor()
            left = BinaryOp(left, op.value, right)
        return left

    def parse_xor(self):
        """抑或（XOR）"""
        left = self.parse_logic_and()
        while self.at(TokenType.XOR):
            op = self.advance()
            right = self.parse_logic_and()
            left = BinaryOp(left, op.value, right)
        return left

    def parse_logic_and(self):
        left = self.parse_comparison()
        while self.at(TokenType.AND):
            op = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op.value, right)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.at(TokenType.EQ, TokenType.NE, TokenType.GT, TokenType.LT,
                      TokenType.GE, TokenType.LE):
            op = self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, op.value, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.at(TokenType.ADD, TokenType.SUB):
            op = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op.value, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.at(TokenType.MUL, TokenType.DIV):
            op = self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op.value, right)
        return left

    def parse_unary(self):
        if self.at(TokenType.NOT):
            op = self.advance()
            operand = self.parse_unary()
            return UnaryOp(op.value, operand)
        if self.at(TokenType.SUB):
            op = self.advance()
            operand = self.parse_unary()
            return UnaryOp('-', operand)
        return self.parse_primary()

    def parse_primary(self):
        pt = self.peek_type()
        tok = self.peek()

        if pt == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(tok.value)

        if pt == TokenType.STRING:
            self.advance()
            return StringLiteral(tok.value)

        if pt in (TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return BoolLiteral(tok.value)

        if pt == TokenType.TYPE_NULL:
            self.advance()
            return NullLiteral(tok.value)

        # ── 标识符：变量 / 函数调用 / 成员访问 ──
        if pt == TokenType.IDENT:
            self.advance()
            name = tok.value

            # 列表访问：IDENT[expr]
            if self.at(TokenType.LBRACK):
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACK)
                return ListAccess(name, index)

            # 函数调用：IDENT（args）
            if self.at(TokenType.LPAREN):
                return FuncCall(name, self._parse_args())

            # 成员访问：IDENT的IDENT / 的长度 / 的方法调用
            if self.at(TokenType.MEMBER_ACCESS):
                self.advance()
                # 方法调用：模块的函数（参数）
                if self.at(TokenType.IDENT):
                    member = self.expect(TokenType.IDENT)
                    # 处理包含→包+含的情况
                    if self.at(TokenType.CONTAINS):
                        member_name = member.value + '含'
                        self.advance()
                    else:
                        member_name = member.value
                    if self.at(TokenType.LPAREN):
                        return MethodCall(name, member_name, self._parse_args())
                    return MemberAccess(name, member_name)
                # 长度/读取：检查后面是否跟括号
                if self.at(TokenType.LENGTH, TokenType.INPUT):
                    tok_type = self.peek_type()
                    name_map = {TokenType.LENGTH: '长度', TokenType.INPUT: '读取'}
                    # 跳过 LENGTH/INPUT 看下一个 token
                    saved = self.pos
                    self.advance()
                    if self.at(TokenType.LPAREN):
                        # 不消费 LPAREN，让 _parse_args 处理
                        return MethodCall(name, name_map[tok_type], self._parse_args())
                    # 回退，走原有逻辑
                    self.pos = saved
                    self.advance()
                    if tok_type == TokenType.LENGTH:
                        return ListLength(name)
                raise ParseError(f"意外的 token: {self.peek().value}", self.peek())

            # 结构体实例化：IDENT含（args）
            if self.at(TokenType.CONTAINS):
                self.advance()
                return StructInstantiate(struct_type=name, name="", args=self._parse_args())

            return Identifier(name)

        # ── 括号表达式 ──
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"意外的 token: {tok.value}", tok)

    # ─── 列表字面量 ───

    def parse_list_literal(self):
        self.expect(TokenType.LBRACK)
        elements = []
        if not self.at(TokenType.RBRACK):
            elements.append(self.parse_expression())
            while self.at(TokenType.ENUM):
                self.advance()
                elements.append(self.parse_expression())
        self.expect(TokenType.RBRACK)
        return elements
