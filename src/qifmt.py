"""奇语言代码格式化工具 (qifmt)

铁律：
1. 冒号即缩进：半角:和全角：统一为：，后接换行+4空格缩进
2. 句号即断行：。为语句终结符，遇之强制断行
3. 括号归一：( )归一为（ ）
4. 顿号归一：半角,与全角、统一为、
5. 拒绝半角赋值：检测到=或==直接报错
6. 分词只插空格：白名单词粘连汉字时自动补空格，绝不拆散字符串字面量
"""
import re


class FormatError(Exception):
    """格式化错误"""
    pass


KW_DECL = {'令', '设', '返回', '输出', '读取', '包括'}
KW_FLOW = {'若', '再若', '否则', '当', '重复', '对', '每项', '于', '时', '则'}
KW_TYPE = {'整数', '小数', '文本', '真', '假', '空', '无', '列', '结构'}
KW_LINK = {'为', '之', '含', '加', '减', '乘', '除',
           '大于', '小于', '等于', '大于等于', '小于等于', '不等于',
           '且', '或', '抑或', '次'}

ALL_KWS = KW_DECL | KW_FLOW | KW_TYPE | KW_LINK
KW_SORTED = sorted(ALL_KWS, key=len, reverse=True)
KW_PATTERN = '(' + '|'.join(re.escape(k) for k in KW_SORTED) + ')'

MERGE_PATTERNS = [
    (r'为 （', '为（'), (r'（ ', '（'), (r' ）：', '）：'),
    (r'时 ：', '时：'), (r'则 ：', '则：'),
]


def normalize_punct(raw: str) -> str:
    if '=' in raw or '==' in raw:
        raise FormatError("qifmt：检测到半角等号，请使用「为」代替。")
    raw = raw.replace('(', '（').replace(')', '）')
    raw = re.sub(r'[,，]', '、', raw)
    raw = raw.replace(':', '：')
    return raw


def split_statements(raw: str) -> list[str]:
    parts = raw.split('。')
    return [p.strip() for p in parts if p.strip()]


def insert_spaces(stmt: str) -> str:
    parts = re.split(r'(".*?")', stmt)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = re.sub(KW_PATTERN, r' \1 ', part)
            part = re.sub(r'\s+', ' ', part).strip()
            for pattern, replacement in MERGE_PATTERNS:
                part = part.replace(pattern, replacement)
        result.append(part)
    joined = ''.join(result)
    joined = re.sub(r'([\u4e00-\u9fff\w])(")', r'\1 \2', joined)
    joined = re.sub(r'"([^"]*?)\s+"', r'"\1"', joined)
    return joined


def format_qi(raw: str) -> str:
    out = normalize_punct(raw)
    stmts = split_statements(out)
    stmts = [insert_spaces(s) for s in stmts]

    lines = []
    indent = 0

    for stmt in stmts:
        if stmt.startswith('否则') or stmt.startswith('再若'):
            indent = max(0, indent - 4)

        # 若...则...格式
        if '则' in stmt and (stmt.startswith('若') or stmt.startswith('再若')):
            parts = stmt.split('则', 1)
            if len(parts) == 2:
                cond = parts[0] + '则'
                body = parts[1].strip()
                lines.append(' ' * indent + cond + '：')
                indent += 4
                lines.append(' ' * indent + body + '。')
                indent -= 4
                continue

        # 否则...格式
        if stmt.startswith('否则'):
            body = stmt[2:].strip()
            lines.append(' ' * indent + '否则：')
            indent += 4
            lines.append(' ' * indent + body + '。')
            indent -= 4
            continue

        # 代码块起始：当/重复/对/令...为（...）：
        is_block = False
        for kw in ['当', '重复', '对']:
            if stmt.startswith(kw):
                is_block = True
                break
        if re.match(r'令\s+\S+\s+\S+\s+为\s*（', stmt):
            is_block = True

        if is_block:
            lines.append(' ' * indent + stmt + '：')
            indent += 4
        else:
            lines.append(' ' * indent + stmt + '。')

    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python qifmt.py <文件名>")
        sys.exit(1)
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        raw = f.read()
    try:
        print(format_qi(raw))
    except FormatError as e:
        print(f"错误: {e}")
        sys.exit(1)
