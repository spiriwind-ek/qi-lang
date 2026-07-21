"""词法分析器测试（注意：关键字识别已移交给语法分析器，词法分析器只输出 IDENT）"""
import sys
sys.path.insert(0, '源码')

from 记号 import TokenType
from 词法分析器 import Lexer, LexerError


def test_ident_produced():
    """上下文关键字系统：词法分析器输出 IDENT，语法分析器负责解析关键字"""
    tokens = Lexer('令 整数 X 为 10。').tokenize()
    # '令' 现在是 IDENT（关键字由语法分析器解析）
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].value == '令'


def test_string_literal():
    tokens = Lexer('令 文本 名字 为 "张三"。').tokenize()
    str_tok = [t for t in tokens if t.type == TokenType.STRING]
    assert len(str_tok) == 1
    assert str_tok[0].value == '张三'


def test_number_literal():
    tokens = Lexer('令 整数 X 为 3.14。').tokenize()
    num_tok = [t for t in tokens if t.type == TokenType.NUMBER]
    assert len(num_tok) == 1
    assert num_tok[0].value == '3.14'


def test_cn_operator_ident():
    """中文运算符现在是 IDENT（语法分析器解析）"""
    tokens = Lexer('X 加 1。').tokenize()
    assert any(t.type == TokenType.IDENT and t.value == '加' for t in tokens)


def test_ascii_operator_add():
    tokens = Lexer('X + 1。').tokenize()
    assert any(t.type == TokenType.ADD for t in tokens)


def test_comment_skipped():
    tokens = Lexer('注：这是注释。令 整数 X 为 1。').tokenize()
    assert not any(t.value == '注' for t in tokens)


def test_fullwidth_paren_normalized():
    """全角括号识别为 LPAREN/RPAREN"""
    tokens = Lexer('求和（3、5）。').tokenize()
    lparen = [t for t in tokens if t.type == TokenType.LPAREN]
    rparen = [t for t in tokens if t.type == TokenType.RPAREN]
    assert len(lparen) == 1
    assert len(rparen) == 1


def test_struct_and_contains_idents():
    """'结构' 和 '含' 现在是 IDENT"""
    tokens = Lexer('令 结构 学生 含：').tokenize()
    values = [t.value for t in tokens if t.type == TokenType.IDENT]
    assert '结构' in values
    assert '含' in values


def test_unknown_char_raises():
    try:
        Lexer('令 整数 X 为 #。').tokenize()
        assert False, "应该抛出异常"
    except LexerError as e:
        assert '未知字符' in str(e)


def test_chinese_period_is_dot():
    tokens = Lexer('输出 "hello"。').tokenize()
    dots = [t for t in tokens if t.type == TokenType.DOT]
    assert len(dots) == 1


if __name__ == '__main__':
    import traceback
    passed = 0
    failed = 0
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                traceback.print_exc()
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
