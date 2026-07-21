import sys
sys.path.insert(0, '源码')
from 解释器 import Interpreter

# ─── 基础测试 ───

def test_var_and_print():
    code = '令 整数 X 为 10。输出 X。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['10'], f"Expected ['10'], got {result}"
    print("  ✓ test_var_and_print")

def test_arithmetic():
    code = '令 整数 X 为 3加2。输出 X。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['5'], f"Expected ['5'], got {result}"
    print("  ✓ test_arithmetic")

def test_string_concat():
    code = '令 文本 X 为 "hello"加" world"。输出 X。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['hello world'], f"Expected ['hello world'], got {result}"
    print("  ✓ test_string_concat")

def test_comparison():
    code = '令 整数 X 为 5。若 X 大于 0 则：\n    输出 "正"。\n否则：\n    输出 "负"。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['正'], f"Expected ['正'], got {result}"
    print("  ✓ test_comparison")

def test_multi_stmt():
    code = '令 整数 X 为 1。设 X 为 2。输出 X。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['2'], f"Expected ['2'], got {result}"
    print("  ✓ test_multi_stmt")


# ─── 条件循环测试 ───

def test_while_loop():
    """当 X 小于 10 时：设 X 为 X加1。"""
    code = '令 整数 X 为 0。当 X 小于 10 时：设 X 为 X加1。输出 X。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['10'], f"Expected ['10'], got {result}"
    print("  ✓ test_while_loop")

def test_while_loop_with_output():
    """while 循环：多次调用函数"""
    code = ('令 整数 X 为 0。'
            '当 X 小于 3 时：设 X 为 X加1。'
            '输出 X。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['3'], f"Expected ['3'], got {result}"
    print("  ✓ test_while_loop_with_output")


# ─── 计数循环测试 ───

def test_repeat_loop():
    """重复 3 次：输出 "就绪"。"""
    code = '重复 3 次：输出 "就绪"。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['就绪', '就绪', '就绪'], f"Expected 3x '就绪', got {result}"
    print("  ✓ test_repeat_loop")

def test_repeat_loop_with_expr():
    """重复循环使用表达式作为次数"""
    code = '令 整数 N 为 3。重复 N 次：输出 "好"。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['好', '好', '好'], f"Expected 3x '好', got {result}"
    print("  ✓ test_repeat_loop_with_expr")


# ─── 函数定义与调用测试 ───

def test_func_decl_and_call():
    """令 整数 求和 为（整数 甲、整数 乙）：返回 甲 加 乙。"""
    code = ('令 整数 求和 为（整数 甲、整数 乙）：\n'
            '    返回 甲 加 乙。\n'
            '令 整数 总计 为 求和（3、5）。\n'
            '输出 总计。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['8'], f"Expected ['8'], got {result}"
    print("  ✓ test_func_decl_and_call")

def test_func_with_string():
    """函数拼接字符串"""
    code = ('令 文本 问候 为（文本 名字）：\n'
            '    返回 "你好" 加 名字。\n'
            '令 文本 结果 为 问候（"小明"）。\n'
            '输出 结果。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['你好小明'], f"Expected ['你好小明'], got {result}"
    print("  ✓ test_func_with_string")

def test_func_void_return():
    """无返回值的函数"""
    code = ('令 空 打印 为（整数N）：\n'
            '    输出 N。\n'
            '打印（42）。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['42'], f"Expected ['42'], got {result}"
    print("  ✓ test_func_void_return")

def test_func_multiple_calls():
    """多次调用同一函数"""
    code = ('令 整数 双倍 为（整数X）：\n'
            '    返回 X乘2。\n'
            '令 整数 A 为 双倍（3）。\n'
            '令 整数 B 为 双倍（7）。\n'
            '输出 A。\n'
            '输出 B。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['6', '14'], f"Expected ['6', '14'], got {result}"
    print("  ✓ test_func_multiple_calls")

def test_func_recursive():
    """递归函数：阶乘"""
    code = ('令 整数 F 为（整数N）：若 N 小于等于 1 则：返回 1。否则：返回 N乘F（N减1）。\n'
            '令 整数 结果 为 F（5）。\n'
            '输出 结果。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['120'], f"Expected ['120'], got {result}"
    print("  ✓ test_func_recursive")


# ─── 组合测试 ───

def test_while_with_func():
    """循环中调用函数"""
    code = ('令 整数 平方 为（整数X）：返回 X乘X。'
            '令 整数 I 为 1。'
            '当 I 小于等于 5 时：设 I 为 I加1。'
            '输出 平方（5）。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['25'], f"Expected ['25'], got {result}"
    print("  ✓ test_while_with_func")

def test_nested_if_in_while():
    """循环中的嵌套条件"""
    code = ('令 整数 X 为 0。'
            '当 X 小于 10 时：设 X 为 X加1。'
            '输出 X。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['10'], f"Expected ['10'], got {result}"
    print("  ✓ test_nested_if_in_while")


# ─── 列表测试 ───

def test_list_decl():
    """令 整数列 库存 为 [10、20、30]。"""
    code = '令 整数列 库存 为 [10、20、30]。输出 库存[1]。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['10'], f"Expected ['10'], got {result}"
    print("  ✓ test_list_decl")

def test_list_access_1based():
    """数组下标1-based，库存[2] 应返回 20"""
    code = '令 整数列 库存 为 [10、20、30]。输出 库存[2]。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['20'], f"Expected ['20'], got {result}"
    print("  ✓ test_list_access_1based")

def test_list_length():
    """库存的长度 应返回 3"""
    code = '令 整数列 库存 为 [10、20、30]。输出 库存的长度。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['3'], f"Expected ['3'], got {result}"
    print("  ✓ test_list_length")

def test_list_full_example():
    """完整示例：声明列表、访问元素、获取长度"""
    code = '令 整数列 库存 为 [10、20、30]。输出 库存[1]。输出 库存[2]。输出 库存[3]。输出 库存的长度。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['10', '20', '30', '3'], f"Expected ['10','20','30','3'], got {result}"
    print("  ✓ test_list_full_example")


# ─── 结构体测试 ───

def test_struct_decl_and_member_access():
    """令 结构 学生 含：文本 姓名、整数 年龄。令 学生 小明 为 学生含（"小明"、18）。输出 小明的姓名。"""
    code = '令 结构 学生 含：文本 姓名、整数 年龄。令 学生 小明 为 学生含（"小明"、18）。输出 小明的姓名。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['小明'], f"Expected ['小明'], got {result}"
    print("  ✓ test_struct_decl_and_member_access")

def test_struct_member_access_int():
    """小明的年龄 应返回 18"""
    code = '令 结构 学生 含：文本 姓名、整数 年龄。令 学生 小明 为 学生含（"小明"、18）。输出 小明的年龄。'
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['18'], f"Expected ['18'], got {result}"
    print("  ✓ test_struct_member_access_int")

def test_struct_multiple_instances():
    """多个结构体实例"""
    code = ('令 结构 学生 含：文本 姓名、整数 年龄。'
            '令 学生 小明 为 学生含（"小明"、18）。'
            '令 学生 小红 为 学生含（"小红"、20）。'
            '输出 小明的姓名。'
            '输出 小红的年龄。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['小明', '20'], f"Expected ['小明', '20'], got {result}"
    print("  ✓ test_struct_multiple_instances")


# ─── 混合测试 ───

def test_list_and_struct_together():
    """列表和结构体混合使用"""
    code = ('令 整数列 库存 为 [10、20、30]。'
            '令 结构 学生 含：文本 姓名、整数 年龄。'
            '令 学生 小明 为 学生含（"小明"、18）。'
            '输出 库存[1]。'
            '输出 小明的姓名。'
            '输出 库存的长度。')
    interp = Interpreter()
    result = interp.run(code)
    assert result == ['10', '小明', '3'], f"Expected ['10', '小明', '3'], got {result}"
    print("  ✓ test_list_and_struct_together")


# ─── 运行所有测试 ───

if __name__ == '__main__':
    print("=== 基础测试 ===")
    test_var_and_print()
    test_arithmetic()
    test_string_concat()
    test_comparison()
    test_multi_stmt()

    print("\n=== 条件循环测试 ===")
    test_while_loop()
    test_while_loop_with_output()

    print("\n=== 计数循环测试 ===")
    test_repeat_loop()
    test_repeat_loop_with_expr()

    print("\n=== 函数定义与调用测试 ===")
    test_func_decl_and_call()
    test_func_with_string()
    test_func_void_return()
    test_func_multiple_calls()
    test_func_recursive()

    print("\n=== 组合测试 ===")
    test_while_with_func()
    test_nested_if_in_while()

    print("\n=== 列表测试 ===")
    test_list_decl()
    test_list_access_1based()
    test_list_length()
    test_list_full_example()

    print("\n=== 结构体测试 ===")
    test_struct_decl_and_member_access()
    test_struct_member_access_int()
    test_struct_multiple_instances()

    print("\n=== 混合测试 ===")
    test_list_and_struct_together()

    print("\n✅ ALL TESTS PASSED")
