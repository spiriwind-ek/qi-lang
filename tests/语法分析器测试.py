import sys
sys.path.insert(0, 'src')
from 记号 import TokenType
from 词法分析器 import Lexer
from 语法分析器 import Parser
from 语法树 import *

def test_var_decl():
    p = Parser(Lexer('令 整数 X 为 10。').tokenize())
    prog = p.parse()
    assert len(prog.statements) == 1
    s = prog.statements[0]
    assert isinstance(s, VarDecl)
    assert s.type_name == '整数'
    assert s.name == 'X'
    assert isinstance(s.value, NumberLiteral)
    assert s.value.value == 10.0

def test_var_assign():
    p = Parser(Lexer('设 X 为 20。').tokenize())
    prog = p.parse()
    s = prog.statements[0]
    assert isinstance(s, VarAssign)
    assert s.name == 'X'

def test_print():
    p = Parser(Lexer('输出 "hello"。').tokenize())
    prog = p.parse()
    s = prog.statements[0]
    assert isinstance(s, PrintStatement)
    assert isinstance(s.value, StringLiteral)

def test_add_expr():
    p = Parser(Lexer('令 整数 X 为 1加2。').tokenize())
    prog = p.parse()
    v = prog.statements[0].value
    assert isinstance(v, BinaryOp)
    assert v.op == '加'

def test_comparison():
    p = Parser(Lexer('令 整数 X 为 1大于0。').tokenize())
    prog = p.parse()
    v = prog.statements[0].value
    assert isinstance(v, BinaryOp)
    assert v.op == '大于'

def test_logic():
    p = Parser(Lexer('令 布尔 X 为 真且假。').tokenize())
    prog = p.parse()
    v = prog.statements[0].value
    assert isinstance(v, BinaryOp)
    assert v.op == '且'

def test_paren():
    p = Parser(Lexer('令 整数 X 为 （1加2）。').tokenize())
    prog = p.parse()
    v = prog.statements[0].value
    assert isinstance(v, BinaryOp)

def test_multi_stmt():
    code = '令 整数 X 为 1。设 X 为 2。输出 X。'
    p = Parser(Lexer(code).tokenize())
    prog = p.parse()
    assert len(prog.statements) == 3
    assert isinstance(prog.statements[0], VarDecl)
    assert isinstance(prog.statements[1], VarAssign)
    assert isinstance(prog.statements[2], PrintStatement)
