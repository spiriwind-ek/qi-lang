"""单元测试：边界情况和新功能"""
import sys
sys.path.insert(0, '源码')
from 解释器 import Interpreter


def run(code):
    return Interpreter().run(code)


# ─── 类型推断 ───

def test_type_inference_int():
    assert run('令 X 为 10。输出 X。') == ['10']

def test_type_inference_float():
    assert run('令 X 为 3.14。输出 X。') == ['3.14']

def test_type_inference_str():
    assert run('令 X 为 "hello"。输出 X。') == ['hello']

def test_type_inference_bool():
    assert run('令 X 为 真。输出 X。') == ['True']

def test_type_inference_expr():
    assert run('令 X 为 3 加 4。输出 X。') == ['7']


# ─── 列表元素赋值 ───

def test_list_assign():
    assert run('令 整数列 X 为 [1、2、3]。设 X[2] 为 99。输出 X[2]。') == ['99']

def test_list_assign_boundary():
    assert run('令 整数列 X 为 [10、20、30]。设 X[1] 为 0。设 X[3] 为 99。输出 X[1]。输出 X[3]。') == ['0', '99']


# ─── 除法 ───

def test_int_division():
    assert run('令 X 为 6 除 2。输出 X。') == ['3']

def test_float_division():
    assert run('令 X 为 7 除 2。输出 X。') == ['3.5']

def test_division_by_zero():
    try:
        run('令 X 为 10 除 0。')
        assert False, "应该抛出异常"
    except Exception as e:
        assert '除零' in str(e)


# ─── 字符串转义 ───

def test_escape_n():
    assert run('输出 "a\\nb"。') == ['a\nb']

def test_escape_t():
    assert run('输出 "a\\tb"。') == ['a\tb']

def test_escape_r():
    assert run('输出 "a\\rb"。') == ['a\rb']

def test_escape_backslash():
    assert run('输出 "a\\\\b"。') == ['a\\b']


# ─── 结构体字段修改 ───

def test_member_assign():
    code = '令 结构 点 含：整数 X。令 点 P 为 点 含（10）。设 P的X 为 20。输出 P的X。'
    assert run(code) == ['20']


# ─── FOR_EACH 循环 ───

def test_for_each():
    code = '令 文本列 水果 为 ["苹果"、"香蕉"]。对 水果 的 每个 名称：输出 名称。'
    assert run(code) == ['苹果', '香蕉']

def test_for_each_empty():
    code = '令 整数列 数据 为 []。令 整数 X 为 0。对 数据 的 每个 Y：设 X 为 X 加 1。输出 X。'
    assert run(code) == ['0']


# ─── 多语句块 ───

def test_multi_stmt_block():
    code = '令 整数 X 为 0。若 真 则：设 X 为 1；设 X 为 2。输出 X。'
    assert run(code) == ['2']

def test_nested_if():
    code = '令 整数 X 为 5。若 X 大于 0 则：若 X 小于 10 则：输出 "范围内"。否则：输出 "范围外"。否则：输出 "非正数"。'
    assert run(code) == ['范围内']

def test_while_multi():
    code = '令 整数 X 为 0。当 X 小于 3 时：设 X 为 X 加 1；输出 X。'
    assert run(code) == ['1', '2', '3']


# ─── 注释 ───

def test_comment():
    code = '注：这是注释。令 X 为 10。输出 X。'
    assert run(code) == ['10']

def test_ascii_comment():
    code = ':: 这是注释\n令 X 为 10。输出 X。'
    assert run(code) == ['10']


# ─── 冒泡排序 ───

def test_bubble_sort():
    code = '''令 整数列 列表 为 [64、34、25、12、22、11、90]。
令 整数 n 为 列表 的 长度。
令 整数 i 为 1。
令 整数 j 为 1。
令 整数 temp 为 0。
当 i 小于 n 时：设 j 为 1；当 j 小于 n 减 i 加 1 时：若 列表[j 加 1] 小于 列表[j] 则：设 temp 为 列表[j]；设 列表[j] 为 列表[j 加 1]；设 列表[j 加 1] 为 temp。设 j 为 j 加 1。设 i 为 i 加 1。
令 整数 k 为 1。
当 k 小于等于 n 时：输出 列表[k]；设 k 为 k 加 1。'''
    assert run(code) == ['11', '12', '22', '25', '34', '64', '90']


# ─── 三元表达式 ───

def test_ternary():
    code = '令 Y 为 若 真 则 "是" 否则 "否"。输出 Y。'
    assert run(code) == ['是']

def test_ternary_false():
    code = '令 Y 为 若 假 则 "是" 否则 "否"。输出 Y。'
    assert run(code) == ['否']

def test_ternary_nested():
    code = '令 X 为 0。令 Y 为 若 X 大于 0 则 "正" 否则 若 X 等于 0 则 "零" 否则 "负"。输出 Y。'
    assert run(code) == ['零']

def test_ternary_in_output():
    code = '输出 若 真 则 "是" 否则 "否"。'
    assert run(code) == ['是']

def test_ternary_arithmetic():
    code = '令 X 为 10。令 Y 为 若 X 大于 0 则 X 乘 2 否则 0。输出 Y。'
    assert run(code) == ['20']


# ─── 一元负号 ───

def test_unary_minus_literal():
    code = '令 X 为 -5。输出 X。'
    assert run(code) == ['-5']

def test_unary_minus_expr():
    code = '令 X 为 -(3 加 2)。输出 X。'
    assert run(code) == ['-5']

def test_unary_minus_nested():
    code = '令 X 为 -(-(3))。输出 X。'
    assert run(code) == ['3']

def test_unary_minus_in_expression():
    code = '令 X 为 10 加 -3。输出 X。'
    assert run(code) == ['7']


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
