"""奇语言 表达式解析器（递归下降）

铁律：
1. 关键字由解析器根据上下文判断，词法分析器只输出 IDENT
2. 句号。= DOT 为唯一语句终止符
3. 每个 parse_xxx() 方法从当前 token 开始，返回对应 AST 节点
"""
from 记号 import TokenType, Token
from 关键字 import (
    ALWAYS, STMT_START, AFTER_LET,
    AFTER_PREV, EXPR_KEYWORDS, BIN_OPS, UNARY_OPS,
)
from 语法树 import (
    BinaryOp, TernaryOp, UnaryOp, FuncCall, MethodCall, MemberAccess,
    ListAccess, ListLength, StructInstantiate,
    NumberLiteral, StringLiteral, BoolLiteral, NullLiteral, Identifier,
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
        friendly = PARSE_ERROR_MESSAGES.get(msg, msg)
        if friendly == msg:
            super().__init__(f"第{token.line}行第{token.col}列: {msg}")
        else:
            super().__init__(f"第{token.line}行第{token.col}列:\n{friendly}")
        self.token = token


# 语句起始 token 集合（用于 _parse_block_body 判断）
STMT_STARTER_TYPES = set(STMT_START.values()) | {TokenType.ELSE, TokenType.ELIF}


class ExprParser:
    """表达式解析器基类，包含关键字解析和表达式优先级解析"""

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
        if self._prev in (None, TokenType.DOT, TokenType.COLON, TokenType.SEMI,
                          TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
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
        _stmt_start_ctx = {
            TokenType.DOT, TokenType.COLON, TokenType.SEMI,
            TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT,
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
            return NullLiteral()

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
                    saved = self.pos
                    self.advance()
                    if self.at(TokenType.LPAREN):
                        return MethodCall(name, name_map[tok_type], self._parse_args())
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
