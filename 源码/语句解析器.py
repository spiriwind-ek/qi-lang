"""奇语言 语句解析器

继承 ExprParser，添加语句级解析方法。
"""
from 表达式解析器 import ExprParser, ParseError, STMT_STARTER_TYPES
from 记号 import TokenType
from 关键字 import STMT_START
from 语法树 import (
    Program, VarDecl, VarAssign,
    IfStatement, WhileLoop, RepeatLoop, ForEachLoop,
    FuncDecl, FuncCall, ReturnStatement,
    ListDecl, ListAssign, StructDecl, StructInstantiate,
    MemberAssign, MethodCall,
    IncludeStatement, PrintStatement, InputStatement,
    Block, StringLiteral,
)

# 函数体内联模式中，遇到这些关键字时继续解析（表示函数体未结束）
_FUNC_BODY_STMT_STARTERS = {
    TokenType.LET, TokenType.SET, TokenType.IF,
    TokenType.WHILE, TokenType.REPEAT,
    TokenType.RETURN, TokenType.OUTPUT, TokenType.INPUT,
    TokenType.STRUCT, TokenType.INCLUDE, TokenType.IN, TokenType.INVOKE,
}


class StmtParser(ExprParser):
    """语句解析器：继承表达式解析器，添加语句解析方法"""

    # ─── 块 ───

    def _parse_block_body(self):
        """解析块：支持两种模式
        - 缩进：：后换行 + INDENT，DEDENT 结束
        - 行内：：后跟单语句，。结束（兼容）
        """
        self.expect(TokenType.COLON)
        
        # 缩进模式
        if self.at(TokenType.NEWLINE):
            self.advance()
            while self.at(TokenType.INDENT):
                self.advance()
            stmts = []
            while not self.at(TokenType.DEDENT) and not self.at(TokenType.EOF):
                while self.at(TokenType.NEWLINE):
                    self.advance()
                if self.at(TokenType.DEDENT, TokenType.EOF, TokenType.ELSE, TokenType.ELIF):
                    break
                stmts.append(self.parse_statement())
                if self.at(TokenType.SEMI):
                    self.advance()
                elif self.at(TokenType.DOT):
                    self.advance()
            if self.at(TokenType.DEDENT):
                self.advance()
            return Block(stmts)

        # 行内模式：多语句（；分隔）。嵌套块的。被内层消费后，
        # 外层继续解析下一条语句。否则/再若 属于上层 if，停止。
        stmts = []
        while not self.at(TokenType.EOF):
            # 跳过语句间的分隔符
            if self.at(TokenType.SEMI):
                self.advance()
                continue
            # 否则/再若 属于上层解析器，不由本块消费
            if self.at(TokenType.ELSE, TokenType.ELIF):
                break
            stmts.append(self.parse_statement())
            if self.at(TokenType.DOT):
                self.advance()
                break
        return Block(stmts)

    def _parse_func_body(self) -> Block:
        """解析函数体：支持缩进和行内两种模式"""
        stmts = []

        # 缩进模式
        if self.at(TokenType.NEWLINE):
            self.advance()
            while self.at(TokenType.INDENT):
                self.advance()
            while not self.at(TokenType.DEDENT) and not self.at(TokenType.EOF):
                while self.at(TokenType.NEWLINE):
                    self.advance()
                if self.at(TokenType.DEDENT, TokenType.EOF):
                    break
                stmts.append(self.parse_statement())
                if self.at(TokenType.SEMI):
                    self.advance()
                elif self.at(TokenType.DOT):
                    self.advance()
            if self.at(TokenType.DEDENT):
                self.advance()
            return Block(stmts)

        # 行内模式：；分隔多语句，。结束
        while not self.at(TokenType.EOF):
            if self.at(TokenType.SEMI):
                self.advance()
                continue
            if self.at(TokenType.DOT):
                self.advance()
                break
            # 嵌套函数定义：令 空 名 为（参数）：
            if self.at(TokenType.LET):
                saved = self.pos
                saved_prev = self._prev
                stmt = self.parse_let_statement()
                if isinstance(stmt, FuncDecl):
                    stmts.append(stmt)
                    continue
                # 不是 FuncDecl，回退，但继续解析（R03：变量声明后还有语句）
                self.pos = saved
                self._prev = saved_prev
            stmts.append(self.parse_statement())
            # 分隔符→继续解析函数体
            if self.at(TokenType.SEMI):
                continue
            # DOT→函数体结束
            if self.at(TokenType.DOT):
                self.advance()
                break
            # 下一个 token 是语句起始关键字→函数体继续
            if self.peek_type() in _FUNC_BODY_STMT_STARTERS:
                continue
            # 其他→函数体结束（防止吞入外层语句）
            break
        return Block(stmts)

    # ─── 程序 ───

    def parse(self):
        stmts = []
        while not self.at(TokenType.EOF):
            # 跳过顶层 NEWLINE/INDENT/DEDENT
            while self.at(TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                self.advance()
            if self.at(TokenType.EOF):
                break
            stmts.append(self.parse_statement())
            if self.at(TokenType.DOT):
                self.advance()
        return Program(Block(stmts))

    # ─── 语句 ───

    def parse_statement(self):
        # 跳过行间 NEWLINE
        while self.at(TokenType.NEWLINE):
            self.advance()
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
            self.pos = saved
            self._prev = TokenType.LET
        # 结构体实例化或变量声明：令 TYPE NAME 为 VALUE。
        if self.at(TokenType.IDENT):
            first = self.advance()
            # 类型推断：令 NAME 为 VALUE（下一个 token 是 为）
            if self.at(TokenType.ASSIGN):
                self.expect(TokenType.ASSIGN)
                value = self.parse_expression()
                return VarDecl(None, first.value, value)
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
        type_tok = self.expect(TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                              TokenType.TYPE_STR, TokenType.TYPE_BOOL)
        field_name = self.expect(TokenType.IDENT)
        fields.append((type_tok.value, field_name.value))
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
        if self.at(TokenType.LBRACK):
            self.advance()
            index = self.parse_expression()
            self.expect(TokenType.RBRACK)
            self.expect(TokenType.ASSIGN)
            value = self.parse_expression()
            return ListAssign(name_tok.value, index, value)
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
        """重复 N 次：statement。"""
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
