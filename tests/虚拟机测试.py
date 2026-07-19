"""字节码 VM 测试"""
import sys
sys.path.insert(0, 'src')

from 解释器 import Interpreter


def run_vm(code):
    """用 VM 执行代码"""
    return Interpreter(use_vm=True).run(code)


# ─── Phase 1: 字面量 + 算术 + 比较 ───

def test_literal_number():
    assert run_vm('输出 42。') == ['42']
    print("  ✓ test_literal_number")

def test_literal_string():
    assert run_vm('输出 "hello"。') == ['hello']
    print("  ✓ test_literal_string")

def test_literal_bool():
    assert run_vm('输出 真。') == ['True']
    assert run_vm('输出 假。') == ['False']
    print("  ✓ test_literal_bool")

def test_arithmetic():
    assert run_vm('输出 3 加 5。') == ['8']
    assert run_vm('输出 10 减 3。') == ['7']
    assert run_vm('输出 4 乘 2。') == ['8']
    assert run_vm('输出 10 除 2。') == ['5']
    print("  ✓ test_arithmetic")

def test_comparison():
    assert run_vm('输出 5 大于 3。') == ['True']
    assert run_vm('输出 5 小于 3。') == ['False']
    assert run_vm('输出 5 等于 5。') == ['True']
    assert run_vm('输出 5 不等于 3。') == ['True']
    print("  ✓ test_comparison")

def test_string_concat():
    assert run_vm('输出 "hello"加" world"。') == ['hello world']
    print("  ✓ test_string_concat")

# ─── Phase 2: 变量 ───

def test_var_decl_and_print():
    assert run_vm('令 整数 X 为 10。输出 X。') == ['10']
    print("  ✓ test_var_decl_and_print")

def test_var_assign():
    assert run_vm('令 整数 X 为 1。设 X 为 2。输出 X。') == ['2']
    print("  ✓ test_var_assign")

def test_type_inference():
    assert run_vm('令 X 为 10。输出 X。') == ['10']
    assert run_vm('令 X 为 "hello"。输出 X。') == ['hello']
    assert run_vm('令 X 为真。输出 X。') == ['True']
    print("  ✓ test_type_inference")

# ─── Phase 3: 控制流 ───

def test_if_true():
    code = '令 整数 X 为 5。若 X 大于 0 则：输出 "正"。否则：输出 "负"。'
    assert run_vm(code) == ['正']
    print("  ✓ test_if_true")

def test_if_false():
    code = '令 整数 X 为 -1。若 X 大于 0 则：输出 "正"。否则：输出 "负"。'
    assert run_vm(code) == ['负']
    print("  ✓ test_if_false")

def test_while_loop():
    code = '令 整数 X 为 0。当 X 小于 3 时：设 X 为 X 加 1。输出 X。'
    assert run_vm(code) == ['3']
    print("  ✓ test_while_loop")

def test_repeat_loop():
    code = '重复 3 次：输出 "好"。'
    assert run_vm(code) == ['好', '好', '好']
    print("  ✓ test_repeat_loop")

# ─── Phase 4: 列表 + 结构体 ───

def test_list_decl():
    code = '令 整数列 库存 为 [10、20、30]。输出 库存[1]。'
    assert run_vm(code) == ['10']
    print("  ✓ test_list_decl")

def test_list_length():
    code = '令 整数列 库存 为 [10、20、30]。输出 库存的长度。'
    assert run_vm(code) == ['3']
    print("  ✓ test_list_length")

def test_struct():
    code = '令 结构 学生 含：文本 姓名、整数 年龄。令 学生 小明 为 学生含（"小明"、18）。输出 小明的姓名。'
    assert run_vm(code) == ['小明']
    print("  ✓ test_struct")

# ─── Phase 5: 函数 ───

def test_func_simple():
    code = '令 整数 双倍 为（整数X）：返回 X乘2。令 整数 Y 为 双倍（5）。输出 Y。'
    assert run_vm(code) == ['10']
    print("  ✓ test_func_simple")

def test_func_add():
    code = '令 整数 求和 为（整数 甲、整数 乙）：返回 甲 加 乙。输出 求和（3、5）。'
    assert run_vm(code) == ['8']
    print("  ✓ test_func_add")

def test_func_fibonacci():
    code = '''令 整数 斐 为（整数 n）：
    若 n 小于等于 1 则：返回 n。
    返回 斐（n 减 1）加 斐（n 减 2）。
令 整数 结果 为 斐（10）。输出 结果。'''
    assert run_vm(code) == ['55']
    print("  ✓ test_func_fibonacci")

def test_func_factorial():
    code = '''令 整数 阶 为（整数 n）：
    若 n 等于 0 则：返回 1。
    返回 n 乘 阶（n 减 1）。
令 整数 结果 为 阶（6）。输出 结果。'''
    assert run_vm(code) == ['720']
    print("  ✓ test_func_factorial")

def test_func_void():
    code = '令 空 打印 为（整数N）：输出 N。打印（42）。'
    assert run_vm(code) == ['42']
    print("  ✓ test_func_void")

# ─── Phase 6: 标准库 ───

def test_stdlib_basic():
    assert run_vm('输出 文字库的长度("hello")。') == ['5']
    print("  ✓ test_stdlib_basic")

# ─── 主入口 ───

if __name__ == '__main__':
    import traceback
    passed = 0
    failed = 0
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            try:
                func()
                passed += 1
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                traceback.print_exc()
                failed += 1
    print(f"\nVM 测试: {passed} passed, {failed} failed")
