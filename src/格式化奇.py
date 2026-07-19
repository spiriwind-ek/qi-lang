"""奇语言代码格式化工具

核心思路：lexer 分词 + 语法匹配 + 补冒号 + 缩进
"""
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from 记号 import TokenType
from 词法分析器 import Lexer


class FormatError(Exception):
    pass


def normalize_punct(raw: str) -> str:
    raw = raw.replace('\u201c', '"').replace('\u201d', '"')
    raw = raw.replace('\u2018', "'").replace('\u2019', "'")
    raw = raw.replace('::', '注：')
    raw = raw.replace('(', '（').replace(')', '）')
    raw = raw.replace(',', '、')
    raw = raw.replace(':', '：')
    raw = raw.replace(';', '；')
    return raw


def _extract_comments(raw: str):
    comments = []
    result = []
    i = 0
    while i < len(raw):
        if raw[i:i+2] == '注：':
            end = i + 2
            while end < len(raw) and raw[end] not in '。\n':
                end += 1
            if end < len(raw) and raw[end] == '。':
                end += 1
            comments.append(raw[i:end])
            result.append(f'"__C{len(comments)-1}__"')
            i = end
        else:
            result.append(raw[i])
            i += 1
    return ''.join(result), comments


def _restore_comments(text: str, comments: list) -> str:
    for i, c in enumerate(comments):
        text = text.replace(f'"__C{i}__"', c)
    return text


def format_qi(raw: str) -> str:
    out = normalize_punct(raw)
    out, comments = _extract_comments(out)

    lexer = Lexer(out)
    tokens = lexer.tokenize()

    lines = []
    indent = 0
    INDENT = 4
    pending = []

    for tok in tokens:
        if tok.type == TokenType.STRING and '__C' in tok.value:
            import re
            m = re.search(r'__C(\d+)__', tok.value)
            if m:
                idx = int(m.group(1))
                if pending:
                    pending.append(' ' + comments[idx])
                elif lines:
                    lines[-1] += ' ' + comments[idx]
                else:
                    lines.append(comments[idx])
            continue

        if tok.type == TokenType.EOF:
            break

        if tok.type == TokenType.COLON:
            if pending:
                lines.append(' ' * (indent * INDENT) + ''.join(pending) + '：')
                pending = []
            indent += 1
            continue

        if tok.type == TokenType.DOT:
            if pending:
                lines.append(' ' * (indent * INDENT) + ''.join(pending) + '。')
                pending = []
            indent = max(0, indent - 1)
            continue

        if tok.type == TokenType.SEMI:
            if pending:
                lines.append(' ' * (indent * INDENT) + ''.join(pending) + '；')
                pending = []
            continue

        # 标点符号归一化
        if tok.type == TokenType.STRING:
            pending.append('"' + tok.value + '"')
            continue
        if tok.type == TokenType.LBRACK:
            pending.append('【')
            continue
        if tok.type == TokenType.RBRACK:
            pending.append('】')
            continue
        if tok.type == TokenType.LPAREN:
            pending.append('（')
            continue
        if tok.type == TokenType.RPAREN:
            pending.append('）')
            continue
        if tok.type == TokenType.ENUM:
            pending.append('、')
            continue

        pending.append(tok.value)

    if pending:
        lines.append(' ' * (indent * INDENT) + ''.join(pending))

    result = []
    for line in lines:
        stripped = line.rstrip()
        if stripped:
            stripped = _restore_comments(stripped, comments)
        result.append(stripped)

    return '\n'.join(result) + '\n'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python 格式化奇.py <文件名>")
        sys.exit(1)
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        raw = f.read()
    try:
        print(format_qi(raw))
    except FormatError as e:
        print(f"错误: {e}")
        sys.exit(1)
