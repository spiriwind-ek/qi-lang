"""标准库测试"""
import sys
sys.path.insert(0, '源码')
from 解释器 import Interpreter


def run(code):
    return Interpreter().run(code)


# ─── 基础库 ───

def test_数值化():
    assert run('令 整数 X 为 基础库的数值化("123")。输出 X。') == ['123']

def test_文字化():
    assert run('令 X 为 基础库的文字化(42)。输出 X。') == ['42']

def test_取模():
    assert run('令 整数 X 为 基础库的取模(-5)。输出 X。') == ['5']

def test_最大值():
    assert run('令 整数 X 为 基础库的最大值(3、5)。输出 X。') == ['5']

def test_最小值():
    assert run('令 整数 X 为 基础库的最小值(3、5)。输出 X。') == ['3']


# ─── 文本库 ───

def test_文字长度():
    assert run('令 整数 X 为 文本库的长度("hello")。输出 X。') == ['5']

def test_文字截取():
    assert run('令 X 为 文本库的截取("hello"、1、3)。输出 X。') == ['hel']

def test_文字查找():
    assert run('令 整数 X 为 文本库的查找("hello"、"e")。输出 X。') == ['2']

def test_文字替换():
    assert run('令 X 为 文本库的替换("hello"、"e"、"a")。输出 X。') == ['hallo']

def test_转大写():
    assert run('令 X 为 文本库的转大写("hello")。输出 X。') == ['HELLO']

def test_去留白():
    assert run('令 X 为 文本库的去留白("  hi  ")。输出 X。') == ['hi']


# ─── 列表库 ───

def test_列表排序():
    code = '令 整数列 数据 为 [3、1、2]。令 整数列 X 为 列表库的排序(数据)。输出 X[1]。输出 X[2]。输出 X[3]。'
    assert run(code) == ['1', '2', '3']

def test_列表反转():
    code = '令 整数列 数据 为 [1、2、3]。令 整数列 X 为 列表库的反转(数据)。输出 X[1]。输出 X[2]。输出 X[3]。'
    assert run(code) == ['3', '2', '1']

def test_列表去重():
    code = '令 整数列 数据 为 [1、2、1、3]。令 整数列 X 为 列表库的去重(数据)。输出 X的长度。'
    assert run(code) == ['3']

def test_列表长度():
    code = '令 整数列 数据 为 [1、2、3]。令 整数 X 为 列表库的长度(数据)。输出 X。'
    assert run(code) == ['3']

def test_列表拥有():
    code = '令 整数列 数据 为 [1、2、3]。令 X 为 列表库的拥有(数据、2)。输出 X。'
    assert run(code) == ['True']


# ─── 文件库 ───

def test_文件写入读取():
    import os
    code = '''
令 句柄 H 为 文件库的打开("_test_stdlib.txt"、"写")。
文件库的写入(H、"你好世界")。
文件库的关闭(H)。
令 句柄 H2 为 文件库的打开("_test_stdlib.txt"、"读")。
令 X 为 文件库的读取(H2、-1)。
文件库的关闭(H2)。
输出 X。
'''
    result = run(code)
    os.remove("_test_stdlib.txt")
    assert result == ['你好世界']


# ─── 方法调用作为独立语句 ───

def test_方法调用作为语句():
    code = '令 句柄 H 为 文件库的打开("_test_stmt.txt"、"写")。文件库的写入(H、"ok")。文件库的关闭(H)。'
    import os
    run(code)
    with open("_test_stmt.txt") as f:
        assert f.read() == "ok"
    os.remove("_test_stmt.txt")


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f'  ✓ {t.__name__}')
            passed += 1
        except Exception as e:
            print(f'  ✗ {t.__name__}: {e}')
            failed += 1
    print(f'\n{passed} passed, {failed} failed')
