"""奇语言 语法分析器（递归下降）

铁律：
1. 令 = LET → let_statement；设 = SET → assignment
2. 句号。= DOT 为唯一语句终止符
3. 每个 parse_xxx() 方法从当前 token 开始，返回对应 AST 节点
"""
from tokens import TokenType, Token
from ast_nodes import (
    Program, VarDecl, VarAssign, BinaryOp, UnaryOp,
    IfStatement, WhileLoop, RepeatLoop, FuncDecl, FuncCall,
    ReturnStatement, ListDecl, ListAccess, ListLength,
    StructDecl, StructInstantiate, MemberAccess, MemberAssign,
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
            # 如果没有预定义的友好提示，就用原始消息
            super().__init__(f"第{token.line}行第{token.col}列: {msg}")
        else:
            super().__init__(f"第{token.line}行第{token.col}列:\n{friendly}")
        self.token = token


# 语句起始 token 集合（用于判断块边界）
STMT_STARTERS = frozenset({
    TokenType.LET, TokenType.SET, TokenType.OUTPUT, TokenType.IF,
    TokenType.WHILE, TokenType.REPEAT, TokenType.FOR_EACH, TokenType.RETURN,
    TokenType.INPUT, TokenType.INCLUDE,
})


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ─── token 工具 ───

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def at(self, *types):
        return self.peek().type in types

    def expect(self, *types):
        tok = self.peek()
        if tok.type not in types:
            expected_names = '或'.join(t.name for t in types)
            raise ParseError(f"期望 {expected_names}，得到 {tok.type.name}", tok)
        return self.advance()

    # ─── 程序 ───

    def parse(self):
        stmts = []
        while not self.at(TokenType.EOF):
            stmts.append(self.parse_statement())
        return Program(Block(stmts))

    # ─── 语句 ───

    def parse_statement(self):
        if self.at(TokenType.LET):
            return self.parse_let_statement()
        if self.at(TokenType.SET):
            return self.parse_var_assign()
        if self.at(TokenType.IF):
            return self.parse_if()
        if self.at(TokenType.WHILE):
            return self.parse_while()
        if self.at(TokenType.REPEAT):
            return self.parse_repeat()
        if self.at(TokenType.RETURN):
            return self.parse_return()
        if self.at(TokenType.OUTPUT):
            return self.parse_print()
        if self.at(TokenType.INCLUDE):
            return self.parse_include()
        if self.at(TokenType.INPUT):
            return self.parse_input()
        # 函数调用或结构体实例化
        if self.at(TokenType.IDENT):
            return self.parse_func_call_stmt()
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
        if self.at(TokenType.TYPE_LIST):
            type_tok = self.advance()
            name_tok = self.expect(TokenType.IDENT)
            self.expect(TokenType.ASSIGN)
            elements = self.parse_list_literal()
            self.expect(TokenType.DOT)
            return ListDecl(type_tok.value, name_tok.value, elements)
        # 结构体实例化或变量声明：令 TYPE NAME 为 VALUE。
        if self.at(TokenType.IDENT):
            type_tok = self.advance()
            name_tok = self.expect(TokenType.IDENT)
            self.expect(TokenType.ASSIGN)
            value = self.parse_expression()
            self.expect(TokenType.DOT)
            # 如果值是结构体实例化，填充实例名称
            if isinstance(value, StructInstantiate):
                value.struct_type = type_tok.value
                value.name = name_tok.value
                return value
            return VarDecl(type_tok.value, name_tok.value, value)
        # 普通类型变量声明或函数定义
        type_tok = self.expect(
            TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STR,
            TokenType.TYPE_BOOL, TokenType.TYPE_VOID, TokenType.TYPE_NULL,
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
            # 函数体：多条语句，直到遇到下一个顶层声明
            body_stmts = []
            while not self.at(TokenType.EOF, TokenType.LET, 
                              TokenType.WHILE, TokenType.REPEAT, TokenType.STRUCT):
                if self.at(TokenType.SET):
                    body_stmts.append(self.parse_var_assign())
                elif self.at(TokenType.RETURN):
                    body_stmts.append(self.parse_return())
                elif self.at(TokenType.IF):
                    body_stmts.append(self.parse_if())
                elif self.at(TokenType.OUTPUT):
                    body_stmts.append(self.parse_print())
                else:
                    break
            body = Block(body_stmts)
            return FuncDecl(type_tok.value, name_tok.value, params, body)

        # ── 普通变量声明 ──
        value = self.parse_expression()
        self.expect(TokenType.DOT)  # 。
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
        self.expect(TokenType.DOT)  # 。
        return StructDecl(name_tok.value, fields)

    # ─── 变量赋值 ───

    def parse_var_assign(self):
        self.expect(TokenType.SET)
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.ASSIGN)  # 为
        value = self.parse_expression()
        self.expect(TokenType.DOT)
        return VarAssign(name_tok.value, value)

    # ─── 条件语句 ───

    def parse_if(self):
        """若 condition 则：statement 否则：statement"""
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.expect(TokenType.THEN)  # 则 / 时
        self.expect(TokenType.COLON)  # ：
        then_block = Block([self.parse_statement()])
        else_block = None
        if self.at(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.COLON)  # ：
            else_block = Block([self.parse_statement()])
        elif self.at(TokenType.ELIF):
            elif_tok = self.peek()
            elif_stmt = self.parse_if()
            else_block = Block([elif_stmt])
        return IfStatement(condition=condition, then_block=then_block, else_block=else_block)

    # ─── 条件循环 ───

    def parse_while(self):
        """当 condition 时：statement"""
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        self.expect(TokenType.THEN)  # 时
        self.expect(TokenType.COLON)  # ：
        body = Block([self.parse_statement()])
        return WhileLoop(condition, body)

    # ─── 计数循环 ───

    def parse_repeat(self):
        """重复 N 次：statement。（单语句体）"""
        self.expect(TokenType.REPEAT)
        count = self.parse_expression()
        self.expect(TokenType.TIMES)  # 次
        self.expect(TokenType.COLON)  # ：
        body = Block([self.parse_statement()])
        return RepeatLoop(count, body)

    # ─── 返回 ───

    def parse_return(self):
        self.expect(TokenType.RETURN)
        value = self.parse_expression()
        self.expect(TokenType.DOT)
        return ReturnStatement(value)

    # ─── 输出 ───

    def parse_print(self):
        """输出 X。"""
        self.expect(TokenType.OUTPUT)
        value = self.parse_expression()
        self.expect(TokenType.DOT)  # 。
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
        self.expect(TokenType.DOT)
        return IncludeStatement(path)

    # ─── 函数调用语句 ───

    def parse_func_call_stmt(self):
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.LPAREN)
        args = []
        if not self.at(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.at(TokenType.ENUM):
                self.advance()
                args.append(self.parse_expression())
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.DOT)
        return FuncCall(name_tok.value, args)

    # ─── 表达式 ───

    def parse_expression(self):
        return self.parse_logic_or()

    def parse_logic_or(self):
        left = self.parse_logic_and()
        while self.at(TokenType.OR):
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
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()

        if tok.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(tok.value)

        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(tok.value)

        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return BoolLiteral(tok.value)

        if tok.type == TokenType.TYPE_NULL:
            self.advance()
            return NullLiteral(tok.value)

        # ── 标识符：变量 / 函数调用 / 成员访问 ──
        if tok.type == TokenType.IDENT:
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
                self.advance()
                args = []
                if not self.at(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.at(TokenType.ENUM):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN)
                return FuncCall(name, args)

            # 成员访问：IDENT之IDENT / IDENT之长度
            if self.at(TokenType.MEMBER_ACCESS):
                self.advance()
                if self.at(TokenType.LENGTH):
                    self.advance()
                    return ListLength(name)
                member = self.expect(TokenType.IDENT)
                return MemberAccess(name, member.value)

            # 结构体实例化：IDENT含（args）
            if self.at(TokenType.CONTAINS):
                self.advance()
                self.expect(TokenType.LPAREN)
                args = []
                if not self.at(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.at(TokenType.ENUM):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN)
                return StructInstantiate(struct_type=name, name="", args=args)

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
