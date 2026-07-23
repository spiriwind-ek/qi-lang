"""奇语言代码格式化工具

基于 AST 的格式化：解析 → 遍历 AST → 生成缩进规范、空格合理的代码。
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from 语法树 import *
from 词法分析器 import Lexer
from 语法分析器 import Parser


class FormatError(Exception):
    pass


# 用于预处理的关键字集合（确保词法分析器能正确分词）
_KEYWORDS = {
    # 语句起始
    '令', '设', '若', '再若', '否则', '当', '重复', '返回', '输出',
    '结构', '包括', '对', '调',
    # 类型
    '整数', '小数', '文本', '布尔', '空', '无', '列',
    '整数列', '小数列', '文本列',
    # 运算符（除、乘 不在列表中——避免拆分"删除""阶乘"）
    '加', '减', '除',
    '等于', '不等于', '大于', '小于', '大于等于', '小于等于',
    '且', '或', '抑或', '非',
    # 布尔
    '真', '假',
    # 控制流
    '则', '时', '次',
    # 结构关键字
    '含', '的', '为', '长度', '每个', '每项',
}


def normalize_punct(raw: str) -> str:
    """统一标点符号风格"""
    raw = raw.replace('\u201c', '"').replace('\u201d', '"')
    raw = raw.replace('\u2018', "'").replace('\u2019', "'")
    raw = raw.replace('(', '（').replace(')', '）')
    raw = raw.replace(',', '、')
    raw = raw.replace(':', '：')
    raw = raw.replace(';', '；')
    return raw


def _space_tokens(text: str) -> str:
    """在关键字之间添加空格，确保词法分析器能正确分词。

    用正则一次性匹配所有关键字（最长匹配优先），避免单字符
    关键字拆分多字符关键字。使用负向后顾+前瞻防止拆分中文词。
    """
    # 保护字符串字面量
    strings = []
    def save_str(m):
        strings.append(m.group(0))
        return f'\x00S{len(strings)-1}\x00'
    text = re.sub(r'"[^"]*"', save_str, text)
    
    # 按长度降序排列，构建正则（最长匹配优先）
    kws = sorted(_KEYWORDS, key=lambda k: (-len(k), k))
    # 中文字符集
    _CN = r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]'
    pattern = '|'.join(re.escape(kw) for kw in kws)
    # 用负向后顾+前瞻确保不拆分中文复合词
    text = re.sub(f'(?<!{_CN})({pattern})(?!{_CN})', r' \1 ', text)
    
    # 清理多余空格
    text = re.sub(r' +', ' ', text)
    
    # 恢复字符串
    for i, s in enumerate(strings):
        text = text.replace(f'\x00S{i}\x00', s)
    
    return text.strip()


# 中文数字支持
_CN_DIGITS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
}
_CN_SCALES = {
    '十': 10, '百': 100, '千': 1000, '万': 10000,
}


def chinese_to_int(text: str) -> int | None:
    """中文数字 → 整数。如 十→10, 二十五→25。非中文数字返回 None"""
    if not text:
        return None
    for ch in text:
        if ch not in _CN_DIGITS and ch not in _CN_SCALES:
            return None
    # 单字：一→1, 十→10
    if len(text) == 1:
        if text in _CN_DIGITS:
            return _CN_DIGITS[text]
        if text in _CN_SCALES:
            return _CN_SCALES[text]
    # 组合：十一→11, 二十五→25, 一百→100
    result = 0
    current = 0
    for ch in text:
        if ch in _CN_DIGITS:
            current = _CN_DIGITS[ch]
        elif ch in _CN_SCALES:
            scale = _CN_SCALES[ch]
            if current == 0:
                current = 1
            result += current * scale
            current = 0
    return result + current


def _cn_number_preprocess(text: str) -> str:
    """把文本中的中文数字替换为阿拉伯数字"""
    # 只在字符串外替换
    strings = []
    def save_str(m):
        strings.append(m.group(0))
        return f'\x00S{len(strings)-1}\x00'
    text = re.sub(r'"[^"]*"', save_str, text)
    
    # 匹配连续的中文数字字符
    cn_num_pat = re.compile(r'[零一二三四五六七八九十百千万]+')
    
    def repl(m):
        cn = m.group(0)
        val = chinese_to_int(cn)
        if val is not None:
            return str(val)
        return cn  # 不认识的就保留
    
    text = cn_num_pat.sub(repl, text)
    
    for i, s in enumerate(strings):
        text = text.replace(f'\x00S{i}\x00', s)
    return text


def _extract_comments(raw: str):
    """提取注释，用空格替换，返回（无注释源码，注释列表[(行号, 文本)]）"""
    comments = []
    result = []
    i = 0
    line = 1
    while i < len(raw):
        if raw[i] == '\n':
            line += 1
            result.append(raw[i])
            i += 1
        elif raw[i:i+2] == '注：':
            start_line = line
            end = i + 2
            while end < len(raw) and raw[end] not in '。\n':
                if raw[end] == '\n':
                    line += 1
                end += 1
            if end < len(raw) and raw[end] == '。':
                end += 1
            comment_text = raw[i:end]
            comments.append((start_line, comment_text))
            result.append(' ' * (end - i))
            i = end
        else:
            result.append(raw[i])
            i += 1
    return ''.join(result), comments


class AstFormatter:
    """基于 AST 的格式化器"""
    
    INDENT = 4
    
    def __init__(self, comments: list = None):
        self._lines: list[tuple[int, str]] = []
        self._comments = comments or []
        # comments: [(original_line, text), ...]
        self._comment_queue = list(self._comments)
    
    def format(self, program: Program) -> str:
        self._lines = []
        self._comment_queue = list(self._comments)
        self._format_program(program)
        # 剩余的注释追加到末尾
        for _, text in self._comment_queue:
            self._lines.append((0, text))
        return self._render()
    
    def _emit_comments_before(self, target_line: int):
        """输出所有行号 <= target_line 的注释（消耗式）"""
        remaining = []
        for line_no, text in self._comment_queue:
            if line_no <= target_line:
                self._lines.append((0, text))
            else:
                remaining.append((line_no, text))
        self._comment_queue = remaining
    
    def _render(self) -> str:
        result = []
        for indent, text in self._lines:
            line = ' ' * (indent * self.INDENT) + text
            result.append(line.rstrip())
        return '\n'.join(result) + '\n'
    
    # ─── 语句级格式化 ───
    
    def _format_program(self, node: Program, indent: int = 0):
        stmts = node.statements.statements if isinstance(node.statements, Block) else node.statements
        for stmt in stmts:
            # 输出排在当前语句之前的注释
            stmt_line = getattr(stmt, 'line', 999999)
            self._emit_comments_before(stmt_line)
            self._format_stmt(stmt, indent)
        # 输出剩余的注释
        self._emit_comments_before(999999)
    
    def _format_block(self, node: Block, indent: int):
        for stmt in node.statements:
            self._format_stmt(stmt, indent)
    
    def _format_stmt(self, node, indent: int):
        if isinstance(node, VarDecl):
            self._fmt_var_decl(node, indent)
        elif isinstance(node, VarAssign):
            self._fmt_var_assign(node, indent)
        elif isinstance(node, PrintStatement):
            self._fmt_print(node, indent)
        elif isinstance(node, ReturnStatement):
            self._fmt_return(node, indent)
        elif isinstance(node, IfStatement):
            self._fmt_if(node, indent)
        elif isinstance(node, WhileLoop):
            self._fmt_while(node, indent)
        elif isinstance(node, RepeatLoop):
            self._fmt_repeat(node, indent)
        elif isinstance(node, ForEachLoop):
            self._fmt_for_each(node, indent)
        elif isinstance(node, FuncDecl):
            self._fmt_func_decl(node, indent)
        elif isinstance(node, FuncCall):
            self._lines.append((indent, self._expr_to_str(node) + '。'))
        elif isinstance(node, MethodCall):
            self._lines.append((indent, f'调 {self._expr_to_str(node)}。'))
        elif isinstance(node, MemberAccess):
            self._lines.append((indent, f'调 {self._expr_to_str(node)}。'))
        elif isinstance(node, StructDecl):
            self._fmt_struct_decl(node, indent)
        elif isinstance(node, StructInstantiate):
            self._fmt_struct_instantiate(node, indent)
        elif isinstance(node, InputStatement):
            self._fmt_input(node, indent)
        elif isinstance(node, IncludeStatement):
            self._fmt_include(node, indent)
        elif isinstance(node, ListDecl):
            self._fmt_list_decl(node, indent)
        elif isinstance(node, MemberAssign):
            self._fmt_member_assign(node, indent)
        elif isinstance(node, ListAssign):
            self._fmt_list_assign(node, indent)
        else:
            self._lines.append((indent, repr(node)))
    
    # ─── 具体语句格式化 ───
    
    def _fmt_var_decl(self, node: VarDecl, indent: int):
        parts = ['令']
        if node.type_name:
            parts.append(node.type_name)
        parts.append(node.name)
        parts.append('为')
        parts.append(self._expr_to_str(node.value))
        self._lines.append((indent, ' '.join(parts) + '。'))
    
    def _fmt_var_assign(self, node: VarAssign, indent: int):
        self._lines.append((indent, 
            f'设 {node.name} 为 {self._expr_to_str(node.value)}。'))
    
    def _fmt_print(self, node: PrintStatement, indent: int):
        self._lines.append((indent, f'输出 {self._expr_to_str(node.value)}。'))
    
    def _fmt_return(self, node: ReturnStatement, indent: int):
        if node.value:
            self._lines.append((indent, f'返回 {self._expr_to_str(node.value)}。'))
        else:
            self._lines.append((indent, '返回。'))
    
    def _fmt_if(self, node: IfStatement, indent: int):
        self._lines.append((indent, f'若 {self._expr_to_str(node.condition)} 则：'))
        self._format_block(node.then_block, indent + 1)
        if node.else_block:
            if (node.else_block.statements and 
                isinstance(node.else_block.statements[0], IfStatement)):
                self._fmt_elif_chain(node.else_block.statements[0], indent)
            else:
                self._lines.append((indent, '否则：'))
                self._format_block(node.else_block, indent + 1)
    
    def _fmt_elif_chain(self, node: IfStatement, indent: int):
        self._lines.append((indent, f'再若 {self._expr_to_str(node.condition)} 则：'))
        self._format_block(node.then_block, indent + 1)
        if node.else_block:
            if (node.else_block.statements and 
                isinstance(node.else_block.statements[0], IfStatement)):
                self._fmt_elif_chain(node.else_block.statements[0], indent)
            else:
                self._lines.append((indent, '否则：'))
                self._format_block(node.else_block, indent + 1)
    
    def _fmt_while(self, node: WhileLoop, indent: int):
        self._lines.append((indent, f'当 {self._expr_to_str(node.condition)} 时：'))
        self._format_block(node.body, indent + 1)
    
    def _fmt_repeat(self, node: RepeatLoop, indent: int):
        self._lines.append((indent, f'重复 {self._expr_to_str(node.count)} 次：'))
        self._format_block(node.body, indent + 1)
    
    def _fmt_for_each(self, node: ForEachLoop, indent: int):
        self._lines.append((indent, f'对 {node.list_name} 的 每个 {node.item_name}：'))
        self._format_block(node.body, indent + 1)
    
    def _fmt_func_decl(self, node: FuncDecl, indent: int):
        params = '、'.join(f'{pt} {pn}' for pt, pn in node.params)
        self._lines.append((indent, f'令 {node.return_type} {node.name} 为（{params}）：'))
        self._format_block(node.body, indent + 1)
    
    def _fmt_struct_decl(self, node: StructDecl, indent: int):
        self._lines.append((indent, f'令 结构 {node.name} 含：'))
        for i, (ptype, pname) in enumerate(node.fields):
            suffix = '、' if i < len(node.fields) - 1 else ''
            self._lines.append((indent + 1, f'{ptype} {pname}{suffix}'))
    
    def _fmt_struct_instantiate(self, node: StructInstantiate, indent: int):
        args = '、'.join(self._expr_to_str(a) for a in node.args)
        name_part = f'令 {node.struct_type} {node.name} 为 ' if node.name else ''
        self._lines.append((indent, f'{name_part}{node.struct_type}含（{args}）。'))
    
    def _fmt_input(self, node: InputStatement, indent: int):
        self._lines.append((indent,
            f'读（{self._expr_to_str(node.prompt)}）。'))
    
    def _fmt_include(self, node: IncludeStatement, indent: int):
        self._lines.append((indent, f'包括 {self._expr_to_str(node.path)}。'))
    
    def _fmt_list_decl(self, node: ListDecl, indent: int):
        elems = '、'.join(self._expr_to_str(e) for e in node.elements)
        self._lines.append((indent, 
            f'令 {node.element_type} {node.name} 为 【{elems}】。'))
    
    def _fmt_member_assign(self, node: MemberAssign, indent: int):
        self._lines.append((indent, 
            f'设 {node.object_name} 的 {node.member_name} 为 {self._expr_to_str(node.value)}。'))
    
    def _fmt_list_assign(self, node: ListAssign, indent: int):
        self._lines.append((indent, 
            f'设 {node.name}【{self._expr_to_str(node.index)}】 为 {self._expr_to_str(node.value)}。'))
    
    # ─── 表达式格式化（返回内联字符串） ───
    
    def _expr_to_str(self, node) -> str:
        if isinstance(node, NumberLiteral):
            return str(node.value)
        if isinstance(node, StringLiteral):
            return f'"{node.value}"'
        if isinstance(node, BoolLiteral):
            return node.value if isinstance(node.value, str) else ('真' if node.value else '假')
        if isinstance(node, NullLiteral):
            return '无'
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, BinaryOp):
            return f'{self._expr_to_str(node.left)} {node.op} {self._expr_to_str(node.right)}'
        if isinstance(node, UnaryOp):
            op = node.op
            operand = self._expr_to_str(node.operand)
            return f'-{operand}' if op == '-' else f'{op} {operand}'
        if isinstance(node, TernaryOp):
            return (f'若 {self._expr_to_str(node.condition)} 则 '
                    f'{self._expr_to_str(node.then_val)} 否则 '
                    f'{self._expr_to_str(node.else_val)}')
        if isinstance(node, FuncCall):
            args = '、'.join(self._expr_to_str(a) for a in node.args)
            return f'{node.name}（{args}）'
        if isinstance(node, MethodCall):
            args = '、'.join(self._expr_to_str(a) for a in node.args)
            return f'{node.object_name} 的 {node.method_name}（{args}）'
        if isinstance(node, ListAccess):
            return f'{node.name}【{self._expr_to_str(node.index)}】'
        if isinstance(node, ListLength):
            return f'{node.name} 的长度'
        if isinstance(node, MemberAccess):
            return f'{node.object_name} 的 {node.member_name}'
        if isinstance(node, StructInstantiate):
            args = '、'.join(self._expr_to_str(a) for a in node.args)
            return f'{node.struct_type}含（{args}）'
        return str(node)


def format_qi(raw: str) -> str:
    """格式化奇语言代码"""
    out = normalize_punct(raw)
    out = _cn_number_preprocess(out)  # 中文数字 → 阿拉伯数字
    out, comments = _extract_comments(out)
    out = _space_tokens(out)
    
    try:
        tokens = Lexer(out).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        formatter = AstFormatter(comments)
        return formatter.format(ast)
    except Exception:
        return _fallback_format(out, comments)


def _fallback_format(raw: str, comments: list) -> str:
    """回退格式化：基于 token 流的基本排版"""
    tokens = Lexer(raw).tokenize()
    
    lines = []
    indent = 0
    INDENT = 4
    pending = []
    comment_map = {}
    for line_no, text in comments:
        comment_map.setdefault(line_no, []).append(text)
    
    for tok in tokens:
        if tok.type.name == 'EOF':
            break
        if tok.type.name == 'STRING':
            pending.append(f'"{tok.value}"')
            continue
        val = str(tok.value)
        if val == '：':
            if pending:
                lines.append(' ' * (indent * INDENT) + ''.join(pending) + '：')
                pending = []
            indent += 1
        elif val == '。':
            if pending:
                lines.append(' ' * (indent * INDENT) + ''.join(pending) + '。')
                pending = []
            indent = max(0, indent - 1)
        elif val == '；':
            if pending:
                lines.append(' ' * (indent * INDENT) + ''.join(pending) + '；')
                pending = []
        else:
            # 在 token 之间加空格，防止标识符粘连
            if pending and pending[-1] not in ('（', '【'):
                pending.append(' ' + val)
            else:
                pending.append(val)
    
    if pending:
        lines.append(' ' * (indent * INDENT) + ''.join(pending))
    
    result = []
    inserted = set()
    for i, line in enumerate(lines):
        line_no = i + 1
        if line_no in comment_map:
            for c in comment_map[line_no]:
                if c not in inserted:
                    result.append(c)
                    inserted.add(c)
        result.append(line.rstrip())
    
    return '\n'.join(result) + '\n'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python 格式化奇.py <文件名>")
        sys.exit(1)
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        raw = f.read()
    try:
        print(format_qi(raw), end='')
    except FormatError as e:
        print(f"错误: {e}")
        sys.exit(1)
