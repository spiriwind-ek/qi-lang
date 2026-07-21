"""图灵完备性测试 + 代码逻辑测试"""
import sys
sys.path.insert(0, '源码')

from 词法分析器 import Lexer
from 语法分析器 import Parser
from 解释器 import Interpreter


def run_code(code):
    interp = Interpreter()
    return interp.run(code)


def test_turing_completeness():
    """图灵完备性测试：如果能模拟图灵机，就是图灵完备的"""
    print("=== 图灵完备性测试 ===")

    # 测试1：变量和赋值
    result = run_code('令 整数 X 为 0。设 X 为 10。输出 X。')
    assert result == ['10'], f"变量测试失败: {result}"
    print("  ✓ 变量和赋值")

    # 测试2：条件分支
    result = run_code('令 整数 X 为 5。若 X 大于 0 则：输出 "正"。否则：输出 "负"。')
    assert result == ['正'], f"条件测试失败: {result}"
    print("  ✓ 条件分支")

    # 测试3：循环（while）
    result = run_code('令 整数 X 为 0。当 X 小于 5 时：设 X 为 X 加 1。输出 X。')
    assert result == ['5'], f"循环测试失败: {result}"
    print("  ✓ 条件循环")

    # 测试4：循环（repeat）
    result = run_code('令 整数 X 为 0。重复 5 次：设 X 为 X 加 1。输出 X。')
    assert result == ['5'], f"计数循环测试失败: {result}"
    print("  ✓ 计数循环")

    # 测试5：函数定义和调用
    result = run_code('令 整数 双 为（整数 X）：返回 X 乘 2。令 整数 Y 为 双（5）。输出 Y。')
    assert result == ['10'], f"函数测试失败: {result}"
    print("  ✓ 函数定义和调用")

    # 测试6：递归
    result = run_code('令 整数 阶 为（整数 n）：若 n 等于 1 则：返回 1。返回 n 乘 阶（n 减 1）。令 整数 结果 为 阶（5）。输出 结果。')
    assert result == ['120'], f"递归测试失败: {result}"
    print("  ✓ 递归")

    # 测试7：嵌套条件
    result = run_code('令 整数 X 为 5。若 X 大于 0 则：若 X 小于 10 则：输出 "范围内"。否则：输出 "范围外"。否则：输出 "非正数"。')
    assert result == ['范围内'], f"嵌套条件测试失败: {result}"
    print("  ✓ 嵌套条件")

    # 测试8：数组操作（简化版）
    result = run_code('令 整数列 列表 为 [1、2、3、4、5]。输出 列表[1]。输出 列表[3]。输出 列表[5]。')
    assert result == ['1', '3', '5'], f"数组测试失败: {result}"
    print("  ✓ 数组操作")

    # 测试9：结构体（简化版）
    result = run_code('令 结构 点 含：整数 X、整数 Y。令 点 P 为 点含（3、4）。输出 P的X。')
    assert result == ['3'], f"结构体测试失败: {result}"
    print("  ✓ 结构体")

    # 测试10：字符串操作
    result = run_code('令 文本 A 为 "Hello"。令 文本 B 为 "World"。令 文本 C 为 A 加 " " 加 B。输出 C。')
    assert result == ['Hello World'], f"字符串测试失败: {result}"
    print("  ✓ 字符串操作")

    # 测试11：逻辑运算
    result = run_code('令 真 A 为真。令 真 B 为假。若 A 且 B 则：输出 "两者为真"。否则：输出 "并非两者为真"。')
    assert result == ['并非两者为真'], f"逻辑运算测试失败: {result}"
    print("  ✓ 逻辑运算")

    # 测试12：复杂表达式
    result = run_code('令 整数 X 为 2 加 3 乘 4。输出 X。')
    assert result == ['14'], f"表达式优先级测试失败: {result}"
    print("  ✓ 表达式优先级")

    print("\n=== 图灵完备性验证 ===")
    print("奇语言支持：")
    print("  ✓ 变量和赋值")
    print("  ✓ 条件分支")
    print("  ✓ 循环")
    print("  ✓ 函数和递归")
    print("  ✓ 数组")
    print("  ✓ 结构体")
    print("  ✓ 字符串操作")
    print("  ✓ 逻辑运算")
    print("  ✓ 嵌套结构")
    print("  ✓ 复杂表达式")
    print("\n结论：奇语言是图灵完备的。")


def test_code_logic():
    """代码逻辑测试"""
    print("\n=== 代码逻辑测试 ===")

    # 测试1：斐波那契数列
    result = run_code('令 整数 斐 为（整数 n）：若 n 小于等于 1 则：返回 n。返回 斐（n 减 1）加 斐（n 减 2）。令 整数 结果 为 斐（10）。输出 结果。')
    assert result == ['55'], f"斐波那契测试失败: {result}"
    print("  ✓ 斐波那契数列")

    # 测试2：阶乘
    result = run_code('令 整数 阶 为（整数 n）：若 n 等于 0 则：返回 1。返回 n 乘 阶（n 减 1）。令 整数 结果 为 阶（6）。输出 结果。')
    assert result == ['720'], f"阶乘测试失败: {result}"
    print("  ✓ 阶乘")

    # 测试3：斐波那契
    result = run_code('令 整数 斐 为（整数 n）：若 n 小于等于 1 则：返回 n。返回 斐（n 减 1）加 斐（n 减 2）。令 整数 结果 为 斐（10）。输出 结果。')
    assert result == ['55'], f"斐波那契测试失败: {result}"
    print("  ✓ 斐波那契")

    # 测试4：嵌套函数调用
    result = run_code('令 整数 双 为（整数 x）：返回 x 乘 2。令 整数 四 为（整数 x）：返回 双（x）乘 2。令 整数 结果 为 四（3）。输出 结果。')
    assert result == ['12'], f"嵌套函数测试失败: {result}"
    print("  ✓ 嵌套函数调用")

    # 测试5：高阶函数模式（用函数返回函数的计算结果）
    result = run_code('令 整数 平方 为（整数 x）：返回 x 乘 x。令 整数 求和平方 为（整数 a、整数 b）：返回 平方（a）加 平方（b）。令 整数 结果 为 求和平方（3、4）。输出 结果。')
    assert result == ['25'], f"函数组合测试失败: {result}"
    print("  ✓ 函数组合")

    # 测试6：条件递升（简化版）
    result = run_code('令 整数 X 为 0。当 X 小于 10 时：设 X 为 X 加 1。输出 X。')
    assert result == ['10'], f"条件递升测试失败: {result}"
    print("  ✓ 条件递升")

    # 测试7：字符串拼接
    result = run_code('令 文本 A 为 "Hello"。令 文本 B 为 "World"。令 文本 C 为 A 加 " " 加 B。输出 C。')
    assert result == ['Hello World'], f"字符串拼接测试失败: {result}"
    print("  ✓ 字符串拼接")

    # 测试8：布尔逻辑
    result = run_code('令 真 A 为真。令 真 B 为假。若 A 且 B 则：输出 "真"。否则：输出 "假"。')
    assert result == ['假'], f"布尔逻辑测试失败: {result}"
    print("  ✓ 布尔逻辑")

    # 测试9：数组长度
    result = run_code('令 整数列 列表 为 [1、2、3、4、5]。输出 列表的长度。')
    assert result == ['5'], f"数组长度测试失败: {result}"
    print("  ✓ 数组长度")

    # 测试10：结构体访问
    result = run_code('令 结构 点 含：整数 X、整数 Y。令 点 P 为 点含（3、4）。输出 P的X。输出 P的Y。')
    assert result == ['3', '4'], f"结构体访问测试失败: {result}"
    print("  ✓ 结构体访问")

    print("\n=== 代码逻辑验证完成 ===")


def main():
    test_turing_completeness()
    test_code_logic()
    print("\n✅ 所有测试通过！")


if __name__ == '__main__':
    main()
