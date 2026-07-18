"""奇语言 词法分析器

铁律：
1. 令 → LET，设 → SET，绝不混用
2. 全角标点归一化为半角，但 token 名不变（LPAREN/RPAREN）
3. 语句结束符只有。，缺句号报错
"""
from tokens import TokenType, Token

# ─── 关键字映射 ───
KEYWORDS = {
    '令':   TokenType.LET,
    '设':   TokenType.SET,
    '若':   TokenType.IF,
    '再若': TokenType.ELIF,
    '否则': TokenType.ELSE,
    '当':   TokenType.WHILE,
    '重复': TokenType.REPEAT,
    '返回': TokenType.RETURN,
    '读取': TokenType.INPUT,
    '输出': TokenType.OUTPUT,
    '真':   TokenType.TRUE,
    '假':   TokenType.FALSE,
    '结构': TokenType.STRUCT,
    '对':   TokenType.FOR_EACH,
    '每项': TokenType.EACH,
    '于':   TokenType.IN,
    '包括': TokenType.INCLUDE,
}

TYPES = {
    '整数': TokenType.TYPE_INT,
    '小数': TokenType.TYPE_FLOAT,
    '文本': TokenType.TYPE_STR,
    '空':   TokenType.TYPE_VOID,
    '无':   TokenType.TYPE_NULL,
    '整数列': TokenType.TYPE_LIST,
    '小数列': TokenType.TYPE_LIST,
    '文本列': TokenType.TYPE_LIST,
}

CN_OPERATORS = {
    '为':     TokenType.ASSIGN,
    '等于':   TokenType.EQ,
    '大于':   TokenType.GT,
    '小于':   TokenType.LT,
    '大于等于': TokenType.GE,
    '小于等于': TokenType.LE,
    '不等于': TokenType.NE,
    '加':     TokenType.ADD,
    '减':     TokenType.SUB,
    '乘':     TokenType.MUL,
    '除':     TokenType.DIV,
    '且':     TokenType.AND,
    '或':     TokenType.OR,
    '非':     TokenType.NOT,
    '抑或':   TokenType.XOR,
    '则':     TokenType.THEN,
    '时':     TokenType.THEN,
    '次':     TokenType.TIMES,
    '含':     TokenType.CONTAINS,
    '之':     TokenType.MEMBER_ACCESS,
    '长度':   TokenType.LENGTH,
}

ASCII_OPS = {
    '=':  TokenType.ASSIGN, '==': TokenType.EQ,
    '>':  TokenType.GT,     '<':  TokenType.LT,
    '>=': TokenType.GE,     '<=': TokenType.LE,
    '!=': TokenType.NE,
    '+':  TokenType.ADD,    '-':  TokenType.SUB,
    '*':  TokenType.MUL,    '/':  TokenType.DIV,
    '&&': TokenType.AND,    '||': TokenType.OR,
    '!':  TokenType.NOT,    '^':  TokenType.XOR,
}

PUNCT_MAP = {
    '。': ('.',  TokenType.DOT),
    '、': (',',  TokenType.ENUM),
    '：': (':',  TokenType.COLON),
    '；': (';',  TokenType.SEMI),
    '（': ('(',  TokenType.LPAREN),
    '）': (')',  TokenType.RPAREN),
    '【': ('[',  TokenType.LBRACK),
    '】': (']',  TokenType.RBRACK),
    '.':  ('.',  TokenType.DOT),
    ',':  (',',  TokenType.ENUM),
    ':':  (':',  TokenType.COLON),
    ';':  (';',  TokenType.SEMI),
    '(':  ('(',  TokenType.LPAREN),
    ')':  (')',  TokenType.RPAREN),
    '[':  ('[',  TokenType.LBRACK),
    ']':  (']',  TokenType.RBRACK),
}

# ─── 友好错误提示 ───
ERROR_MESSAGES = {
    '=': "检测到半角等号，请使用「为」代替。例如：令 整数 X 为 10。",
    '未知字符': "使用了不支持的字符。请检查是否使用了特殊符号。",
    '未闭合的字符串': "字符串没有结束引号。请确保字符串用引号正确闭合。",
}


class LexerError(Exception):
    """词法错误"""
    def __init__(self, msg, line, col):
        # 提供友好的错误提示
        friendly = ERROR_MESSAGES.get(msg, msg)
        super().__init__(f"第{line}行第{col}列: {friendly}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def peek(self):
        return self.source[self.pos] if self.pos < len(self.source) else None

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\n\r':
            self.advance()

    def read_string(self):
        quote = self.advance()
        result = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch is None:
                raise LexerError("未闭合的字符串", self.line, self.col)
            if ch == quote:
                self.advance()
                return ''.join(result)
            if ch == '\\':
                self.advance()
                esc = self.advance() if self.pos < len(self.source) else None
                if esc is None:
                    raise LexerError("转义字符不完整", self.line, self.col)
                ESCAPES = {'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}
                result.append(ESCAPES.get(esc, esc))
            else:
                result.append(self.advance())
        raise LexerError("未闭合的字符串", self.line, self.col)

    def read_number(self):
        start = self.pos
        has_dot = False
        while self.pos < len(self.source):
            ch = self.peek()
            if ch and ch.isdigit():
                self.advance()
            elif ch == '.' and not has_dot:
                has_dot = True
                self.advance()
            else:
                break
        return self.source[start:self.pos]

    def read_word(self):
        """读取连续的中文或ASCII字符序列（遇到标点/跨类字符停止）"""
        STOP_CHARS = set('。，、：；（）【】！？""\'\'')
        start = self.pos
        is_chinese = ord(self.source[self.pos]) > 127
        
        while self.pos < len(self.source):
            ch = self.peek()
            if ch is None:
                break
            if ch in STOP_CHARS:
                break
            if is_chinese:
                if ord(ch) > 127:
                    self.advance()
                else:
                    break
            else:
                if ch.isascii() and (ch.isalnum() or ch == '_'):
                    self.advance()
                else:
                    break
        return self.source[start:self.pos]

    def tokenize(self):
        tokens = []

        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.peek()
            line, col = self.line, self.col

            # ── 注释：注：... ──
            if ch == '注':
                word = self.read_word()
                if word == '注' and self.peek() in ('：', ':'):
                    self.advance()
                    while self.pos < len(self.source) and self.peek() not in ('。', '\n'):
                        self.advance()
                    continue
                tokens.append(Token(TokenType.IDENT, word, line, col))
                continue

            # ── 字符串字面量 ──
            if ch in ('"', "'"):
                tokens.append(Token(TokenType.STRING, self.read_string(), line, col))
                continue

            # ── 数字字面量 ──
            if ch.isdigit():
                tokens.append(Token(TokenType.NUMBER, self.read_number(), line, col))
                continue

            # ── 标点符号（归一化） ──
            if ch in PUNCT_MAP:
                normalized, tok_type = PUNCT_MAP[ch]
                self.advance()
                tokens.append(Token(tok_type, normalized, line, col))
                continue

            # ── 半角运算符 ──
            if ch in ('=', '>', '<', '!', '+', '-', '*', '/', '&', '|', '^'):
                op = self.advance()
                nxt = self.peek()
                if nxt == '=' and op in ('=', '>', '<', '!'):
                    op += self.advance()
                tokens.append(Token(ASCII_OPS[op], op, line, col))
                continue

            # ── 中文字符（最长匹配：关键词/运算符优先于标识符） ──
            if ord(ch) > 127:
                start_pos = self.pos
                while self.pos < len(self.source) and ord(self.peek()) > 127 and self.peek() not in PUNCT_MAP:
                    self.advance()
                seq = self.source[start_pos:self.pos]
                
                # 最长匹配拆分
                i = 0
                while i < len(seq):
                    matched = False
                    for length in range(min(4, len(seq) - i), 0, -1):
                        candidate = seq[i:i+length]
                        if candidate in KEYWORDS:
                            tokens.append(Token(KEYWORDS[candidate], candidate, line, col))
                            i += length
                            col += length
                            matched = True
                            break
                        elif candidate in TYPES:
                            tokens.append(Token(TYPES[candidate], candidate, line, col))
                            i += length
                            col += length
                            matched = True
                            break
                        elif candidate in CN_OPERATORS:
                            tokens.append(Token(CN_OPERATORS[candidate], candidate, line, col))
                            i += length
                            col += length
                            matched = True
                            break
                    if not matched:
                        # 未匹配的中文字符作为标识符的一部分
                        id_start = i
                        while i < len(seq):
                            found_known = False
                            for length in range(min(4, len(seq) - i), 0, -1):
                                c = seq[i:i+length]
                                if c in KEYWORDS or c in TYPES or c in CN_OPERATORS:
                                    found_known = True
                                    break
                            if found_known:
                                break
                            i += 1
                        ident = seq[id_start:i]
                        tokens.append(Token(TokenType.IDENT, ident, line, col))
                        col += len(ident)
                continue

            # ── ASCII 标识符 ──
            if ch.isalpha() or ch == '_':
                tokens.append(Token(TokenType.IDENT, self.read_word(), line, col))
                continue

            raise LexerError(f"未知字符 '{ch}'", self.line, self.col)

        tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return tokens
