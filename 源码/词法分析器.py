"""奇语言 词法分析器

铁律：
1. 全角标点归一化为半角，但 token 名不变（LPAREN/RPAREN）
2. 语句结束符只有。，缺句号报错
3. 中文序列在关键字和标点处切分，不需要外部加空格预处理
4. 缩进分块：NEWLINE 后追踪缩进，发射 INDENT/DEDENT
"""
from 记号 import TokenType, Token
from 定义加载器 import ASCII运算符, 标点映射

ASCII_OPS = ASCII运算符
PUNCT_MAP = 标点映射
# 单字符分隔符：标点 + 的/为/含 + 中文引号
_SPLIT = set(PUNCT_MAP.keys()) | {'的', '为', '含',
    chr(0x201C), chr(0x201D), chr(0x2018), chr(0x2019)}

# 始终切分的关键字集合——在任何位置都按关键字处理
# 包括标点级关键字、运算符、控制流词和布尔字面量
_ALWAYS_CN_TOKENS = sorted({
    '的', '为', '含',
    # 二元/一元运算符
    '加', '减', '等于', '不等于', '大于', '小于', '大于等于', '小于等于',
    '且', '或', '抑或', '非',
    # 控制流词
    '则', '时', '次',
    # 布尔字面量
    '真', '假',
    # 其他结构关键字
    '长度', '每个', '每项',
    '等于', '不等于', '大于', '小于', '大于等于', '小于等于',
    '且', '或', '抑或', '非',
    # 控制流词
    '则', '时', '次',
    # 布尔字面量
    '真', '假',
    # 其他始终关键字
    '长度', '每个', '每项',
}, key=lambda k: (-len(k), k))

# 语句起始关键字——仅在序列开头或标点后切分
# 包含控制流、声明、I/O 等关键字
_STMT_START_TOKENS = sorted({
    '令', '设', '若', '再若', '否则', '当', '重复', '返回', '输出',
    '结构', '包括', '对', '调',
}, key=lambda k: (-len(k), k))

# 类型关键字——仅在 令/设 之后才启用切分
# 由 _try_split 中的 _check_types 标志控制，不加入 _STMT_START_TOKENS
_TYPE_TOKENS = {'整数', '小数', '文本', '布尔', '空', '无',
                '整数列', '小数列', '文本列'}

# 缩进：1 Tab = 4 空格
_TAB_WIDTH = 4


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
        self._indent_stack = [0]  # 缩进栈，初始顶层

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

    def _calc_indent(self) -> int:
        """计算当前行（已跳过 \n）的缩进值，消费空白字符"""
        indent = 0
        while self.pos < len(self.source):
            ch = self.peek()
            if ch == ' ':
                indent += 1
                self.advance()
            elif ch == '\t':
                indent += _TAB_WIDTH
                self.advance()
            else:
                break
        return indent

    def _skip_line(self):
        """跳过当前行剩余内容（遇到 \n 或 EOF 停止）"""
        while self.pos < len(self.source) and self.peek() != '\n':
            self.advance()

    def read_string(self):
        quote = self.advance()
        # 中文引号配对
        _QUOTE_PAIRS = {'\u201c': '\u201d', '\u2018': '\u2019'}
        close_quote = _QUOTE_PAIRS.get(quote, quote)
        result = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch is None:
                raise LexerError("未闭合的字符串", self.line, self.col)
            if ch == close_quote:
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

    def _handle_newline(self, tokens):
        """消费换行，计算下一行缩进，逐级发射 INDENT/DEDENT"""
        self.advance()  # 消费 \n
        # 计算下一行缩进
        indent = self._calc_indent()
        
        if self.pos >= len(self.source):
            return
        
        next_ch = self.peek()
        
        # 空行 / 注释行 → 跳过内容但仍需更新缩进跟踪
        if next_ch == '\n':
            return  # 空行：不改变缩进，不发射 NEWLINE
        if next_ch == '注':
            # 注：注释 — 跳过行，不改变缩进
            self._skip_line()
            return
        if next_ch == ':' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == ':':
            # :: 注释
            self.advance()
            self.advance()
            self._skip_line()
            return
        
        # 有效行 → 发射 NEWLINE
        tokens.append(Token(TokenType.NEWLINE, '\n', self.line, 1))
        
        # 按 4 空格一级逐级发射 INDENT/DEDENT
        if indent > self._indent_stack[-1]:
            cur = self._indent_stack[-1]
            while cur < indent:
                cur += _TAB_WIDTH
                self._indent_stack.append(cur)
                tokens.append(Token(TokenType.INDENT, cur, self.line, 1))
        elif indent < self._indent_stack[-1]:
            while self._indent_stack[-1] > indent:
                self._indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, indent, self.line, 1))

    def tokenize(self):
        tokens = []

        while self.pos < len(self.source):
            # ---- 换行 + 缩进处理 ----
            if self.peek() == '\n':
                self._handle_newline(tokens)
                continue
            
            # ---- 水平空白（同行内跳过） ----
            while self.pos < len(self.source) and self.peek() == ' ':
                self.advance()
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

            # 字符串（支持 ASCII 引号和中文引号 \u201c \u201d \u2018 \u2019）
            _Q = set('"\'') | {chr(0x201C), chr(0x201D), chr(0x2018), chr(0x2019)}
            if ch in _Q:
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

            # 中文序列：在关键字和标点处切分
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
                # 读取连续中文序列
                start = self.pos
                while self.pos < len(self.source) and ord(self.peek()) > 127 and self.peek() not in _SPLIT:
                    self.advance()
                seq = self.source[start:self.pos]

                # 按始终关键字和语句起始关键字切分
                def _try_split(seq, kw_list):
                    """尝试在 seq 的当前位置匹配 kw_list 中的关键字"""
                    for kw in kw_list:
                        if seq.startswith(kw):
                            return kw
                    return None

                i = 0
                _check_types = False  # 仅在 令/设 之后启用类型关键字切分
                while i < len(seq):
                    # 在当前位置优先匹配始终关键字
                    kw = _try_split(seq[i:], _ALWAYS_CN_TOKENS)
                    if kw is None and i == 0:
                        # seq 开头：也匹配语句起始关键字
                        kw = _try_split(seq, _STMT_START_TOKENS)
                    if kw is None and _check_types:
                        # 令/设 之后：也匹配类型关键字
                        kw = _try_split(seq[i:], _TYPE_TOKENS)
                    if kw:
                        if i > 0:
                            tokens.append(self._emit_ident(seq[:i], line, col))
                            col += i
                        tokens.append(self._emit_ident(kw, line, col))
                        col += len(kw)
                        seq = seq[i + len(kw):]
                        i = 0
                        _check_types = (kw in ('令', '设'))
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

        # 文件结束：弹出所有缩进栈
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, 0, self.line, 1))
        tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return tokens
