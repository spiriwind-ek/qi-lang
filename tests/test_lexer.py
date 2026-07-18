"""词法分析器测试"""
import sys
sys.path.insert(0, 'src')

from tokens import TokenType
from lexer import Lexer, LexerError


def test_let_and_set_are_different():
    """铁律1: 令=LET，设=SET，绝不混用"""
    tokens = Lexer('令 整数 X 为 10。').tokenize()
    assert tokens[0].type == TokenType.LET

    tokens = Lexer('设 X 为 20。').tokenize()
    assert tokens[0].type == TokenType.SET


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


def test_cn_operator_add():
    tokens = Lexer('X 加 1。').tokenize()
    assert any(t.type == TokenType.ADD for t in tokens)


def test_ascii_operator_add():
    tokens = Lexer('X + 1。').tokenize()
    assert any(t.type == TokenType.ADD for t in tokens)


def test_comment_skipped():
    tokens = Lexer('注：这是注释。令 整数 X 为 1。').tokenize()
    assert not any(t.value == '注' for t in tokens)


def test_fullwidth_paren_normalized():
    """铁律4: 全角括号归一化为半角"""
    tokens = Lexer('求和（3、5）。').tokenize()
    lparen = [t for t in tokens if t.type == TokenType.LPAREN]
    rparen = [t for t in tokens if t.type == TokenType.RPAREN]
    assert len(lparen) == 1
    assert lparen[0].value == '('
    assert len(rparen) == 1
    assert rparen[0].value == ')'


def test_struct_keyword():
    tokens = Lexer('令 结构 学生 含：').tokenize()
    assert any(t.type == TokenType.STRUCT for t in tokens)


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
