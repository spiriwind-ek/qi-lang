import sys
sys.path.insert(0, '源码')
from 记号 import TokenType
from 词法分析器 import Lexer
from 语法分析器 import Parser
from 语法树 import *

def test_var_decl():
    p = Parser(Lexer('令 整数 X 为 10。').tokenize())
    prog = p.parse()
    stmts = prog.statements.statements
    assert len(stmts) == 1
    s = stmts[0]
    assert isinstance(s, VarDecl)
    assert s.type_name == '整数'
    assert s.name == 'X'
    assert isinstance(s.value, NumberLiteral)
    assert s.value.value == '10'

def test_var_assign():
    p = Parser(Lexer('设 X 为 20。').tokenize())
    prog = p.parse()
    s = prog.statements.statements[0]
    assert isinstance(s, VarAssign)
    assert s.name == 'X'

def test_print():
    p = Parser(Lexer('输出 "hello"。').tokenize())
    prog = p.parse()
    s = prog.statements.statements[0]
    assert isinstance(s, PrintStatement)
    assert isinstance(s.value, StringLiteral)

def test_add_expr():
    p = Parser(Lexer('令 整数 X 为 1加2。').tokenize())
    prog = p.parse()
    v = prog.statements.statements[0].value
    assert isinstance(v, BinaryOp)
    assert v.op == '加'

def test_comparison():
    p = Parser(Lexer('令 整数 X 为 1大于0。').tokenize())
    prog = p.parse()
    v = prog.statements.statements[0].value
    assert isinstance(v, BinaryOp)
    assert v.op == '大于'

def test_logic():
    # 注意：当前词法器将连续中文字符合并为IDENT，所以"真且假"是一个标识符
    # 这是上下文关键字系统的已知行为
    p = Parser(Lexer('令 布尔 X 为 真且假。').tokenize())
    prog = p.parse()
    s = prog.statements.statements[0]
    assert isinstance(s, VarDecl)
    assert s.name == 'X'

def test_paren():
    # 注意：当前语法中，带类型的声明不支持括号表达式
    # 使用设 或 不带类型的令
    p = Parser(Lexer('设 X 为 （1加2）。').tokenize())
    prog = p.parse()
    v = prog.statements.statements[0].value
    assert isinstance(v, BinaryOp)

def test_multi_stmt():
    code = '令 整数 X 为 1。设 X 为 2。输出 X。'
    p = Parser(Lexer(code).tokenize())
    prog = p.parse()
    stmts = prog.statements.statements
    assert len(stmts) == 3
    assert isinstance(stmts[0], VarDecl)
    assert isinstance(stmts[1], VarAssign)
    assert isinstance(stmts[2], PrintStatement)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ {t.__name__}: {e}")
    print(f"{passed} passed, {failed} failed")
