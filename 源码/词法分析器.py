"""奇语言 词法分析器

铁律：
1. 全角标点归一化为半角，但 token 名不变（LPAREN/RPAREN）
2. 语句结束符只有。，缺句号报错
3. 中文序列只在 的/为/含/标点处切分，多字符关键字不拆分，全部输出 IDENT
"""
from 记号 import TokenType, Token
from 定义加载器 import ASCII运算符, 标点映射

ASCII_OPS = ASCII运算符
PUNCT_MAP = 标点映射
# 单字符分隔符：标点 + 的/为/含
_SPLIT = set(PUNCT_MAP.keys()) | {'的', '为', '含'}


class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"第{line}行第{col}列: {msg}")
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
                ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0', '\\': '\\', '"': '"', "'": "'"}
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

    def _emit_ident(self, text, line, col):
        """辅助：输出一个 IDENT token"""
        return Token(TokenType.IDENT, text, line, col)

    def tokenize(self):
        tokens = []

        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.peek()
            line, col = self.line, self.col

            # 注释
            if ch == '注':
                word = self.read_word()
                if word == '注' and self.peek() in ('：', ':'):
                    self.advance()
                    while self.pos < len(self.source) and self.peek() not in ('。', '\n'):
                        self.advance()
                    if self.peek() == '。':
                        self.advance()
                    continue
                tokens.append(self._emit_ident(word, line, col))
                continue
            if ch == ':' and self.peek() == ':':
                self.advance()
                self.advance()
                while self.pos < len(self.source) and self.peek() not in ('。', '\n'):
                    self.advance()
                if self.peek() == '。':
                    self.advance()
                continue

            # 字符串
            if ch in ('"', "'"):
                tokens.append(Token(TokenType.STRING, self.read_string(), line, col))
                continue

            # 数字
            if ch.isdigit():
                tokens.append(Token(TokenType.NUMBER, self.read_number(), line, col))
                continue

            # 标点（归一化为半角 token）
            if ch in PUNCT_MAP:
                normalized, tok_type = PUNCT_MAP[ch]
                self.advance()
                tokens.append(Token(tok_type, normalized, line, col))
                continue

            # 半角运算符
            if ch in ('=', '>', '<', '!', '+', '-', '*', '/', '&', '|', '^'):
                op = self.advance()
                nxt = self.peek()
                if nxt == '=' and op in ('=', '>', '<', '!'):
                    op += self.advance()
                tokens.append(Token(ASCII_OPS[op], op, line, col))
                continue

            # 中文序列：只在 的/为/含/标点 处切分，其余作为单个 IDENT
            if ord(ch) > 127:
                # 首字符是分隔符则直接处理
                if ch in _SPLIT:
                    if ch in PUNCT_MAP:
                        normalized, tok_type = PUNCT_MAP[ch]
                        tokens.append(Token(tok_type, normalized, line, col))
                    else:
                        tokens.append(self._emit_ident(ch, line, col))
                    self.advance()
                    continue
                # 读取连续中文序列直到遇到分隔符
                start = self.pos
                while self.pos < len(self.source) and ord(self.peek()) > 127 and self.peek() not in _SPLIT:
                    self.advance()
                seq = self.source[start:self.pos]

                # 在序列内部按分隔符切分
                i = 0
                while i < len(seq):
                    if seq[i] in _SPLIT:
                        if i > 0:
                            tokens.append(self._emit_ident(seq[:i], line, col))
                            col += i
                        if seq[i] in PUNCT_MAP:
                            normalized, tok_type = PUNCT_MAP[seq[i]]
                            tokens.append(Token(tok_type, normalized, line, col))
                        else:
                            tokens.append(self._emit_ident(seq[i], line, col))
                        col += 1
                        seq = seq[i + 1:]
                        i = 0
                    else:
                        i += 1
                if seq:
                    tokens.append(self._emit_ident(seq, line, col))
                continue

            # ASCII 标识符
            if ch.isalpha() or ch == '_':
                tokens.append(self._emit_ident(self.read_word(), line, col))
                continue

            raise LexerError(f"未知字符 '{ch}'", self.line, self.col)

        tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return tokens
