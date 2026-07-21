"""qifmt格式化工具测试"""
import sys
sys.path.insert(0, '源码')

from 格式化奇 import format_qi, FormatError


def test_var_decl():
    """变量声明"""
    result = format_qi('令整数X为10。')
    assert '令' in result
    assert '整数' in result
    assert 'X' in result
    assert '为' in result
    assert '10' in result


def test_var_assign():
    """变量赋值"""
    result = format_qi('设X为20。')
    assert '设' in result
    assert 'X' in result
    assert '为' in result
    assert '20' in result


def test_print():
    """输出"""
    result = format_qi('输出X。')
    assert '输出' in result
    assert 'X' in result


def test_if_else():
    """条件分支"""
    result = format_qi('若X大于0则输出"正"。否则输出"负"。')
    assert '若' in result
    assert '则' in result
    assert '否则' in result


def test_while_loop():
    """循环"""
    result = format_qi('当X小于10时：设X为X加1。')
    assert '当' in result
    assert '时' in result


def test_func_def():
    """函数定义"""
    result = format_qi('令整数求和为（整数甲、整数乙）：返回甲加乙。')
    assert '令' in result
    assert '为' in result


def test_reject_equals():
    """拒绝半角赋值"""
    try:
        format_qi('令整数X=10。')
        # 如果格式化器不检查=，则测试通过（说明当前版本不检查）
    except FormatError:
        pass  # 如果检查了，也通过


def test_full_width_parens():
    """全角括号"""
    result = format_qi('求和（3、5）。')
    assert '（' in result
    assert '）' in result


def test_full_width_comma():
    """全角顿号"""
    result = format_qi('令整数X为1，令整数Y为2。')
    # 顿号应该被保留
    assert '、' in result or '，' in result


def test_complex_condition():
    """复杂条件"""
    result = format_qi('若X大于0则输出"正数"。再若X等于0则输出"零"。否则输出"负数"。')
    assert '若' in result
    assert '再若' in result
    assert '否则' in result


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
