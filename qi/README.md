gitt/cangjntib/linux_x86_64_cjnatibpcre2-8.so.0: no version information available (required by git)
# Qi Language v0.1.2-alpha

Write code in Chinese, as natural as writing an article.

## Quick Start

```bash
# Run a file
python 奇.py .qi

# Interactive Shell (bytecode VM by default)
python 交互式奇解析器.py

# Format code
python 化奇.py your_code.qi
```

## Syntax Examples

```
令 整数 X 为 10。令 文本 名字 为 "奇语言"。
输出 X 加 5。                  15

若 X 大于 0 则：输出 "正"。否则：输出 "负"。  Condition
当 X 小于 3 时：设 X 为 X 加 1；输出 X。     Loop

令 整数 求和 为（整数 甲、整数 乙）：返回 甲 加 乙。Function
令 整数列 列表 为 [1、2、3]。                    List
令 结构 学生 含：文本 姓名、整数 年龄。           Struct
设 小明的年龄 为 19。                             Member access
令 Y 为 若 X 大于 0 则 "正" 否则 "负"。           Ternary

输出 文本库的长度("hello")。                      Standard library
```

## Core Features

| Feature | Description |
|---------|-------------|
| Context Keywords | Keywords can be used as variable names (`长度`, `文本库` no longer conflict) |
| Static Types | `令 整数 X 为 10` |
| Chinese Operators | `加`, `减`, `乘`, `除`, `且`, `或`, `抑或` |
| Block Structure | `：` starts, `。` ends, `；` chains multiple statements |
| Bytecode VM | Stack-based virtual machine (enabled by default in interactive shell) |
| Standard Library | Basic, Text, List, File modules |
| Structs | `令 结构 学生 含：文本 姓名、整数 年龄` |
| Lists | `令 整数列 X 为 [1、2、3]` (1-based indexing) |
| Functions | Recursive support, functions as values |
| Ternary Expressions | `若 条件 则 A 否则 B` |
| File Extensions | `.q奇` (source), `.qi奇头` (headers) |

## Standard Library

| Module | Functions |
|--------|-----------|
| Basic | `数值化`, `文字化`, `取模`, `最大值`, `最小值` |
| Text | `长度`, `截取`, `查找`, `替换`, `转大写`, `转小写`, `去留白` |
| List | `排序`, `反转`, `去重`, `拥有`, `长度` |
| File | `打开`, `读取`, `写入`, `关闭` (VFS abstraction) |

```
文本库的长度("hello")     → 5
基础库的数值化("123")      → 123
列表库的排序([3、1、2])    → [1、2、3]
```

## Project Structure

```
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docs
│   ├── api.md
│   ├── changelog.md
│   ├── dev_guide.md
│   ├── errors.md
│   ├── examples.md
│   ├── faq.md
│   ├── syntax.md
│   └── tutorial.md
├── examples
│   ├── array.qi
│   ├── binary_tree.qi
│   ├── cube.qi
│   ├── enum_expr.qi
│   ├── fibonacci.qi
│   ├── func_binary_tree.qi
│   ├── functional.qi
│   ├── hello.qi
│   ├── loops.qi
│   ├── math.qi
│   ├── math_utils.qi
│   ├── prop_binary_tree.qi
│   ├── sort.qi
│   ├── struct_binary_tree.qi
│   └── variables.qi
├── main.py
├── qish.py
├── README.md
├── src
└── tests
```

## Tests

```bash
python 测试.py         # 32 tests
python 机测试.py       # 22 tests
python 库测试.py       # 18 tests
python 器测试.py       # Integration tests
python 分析器测试.py   # 10 tests
python 化奇测试.py     # 10 tests
python 分析器测试.py   # 8 tests
python 完备性测试.py   # Turing completeness
```

## Documentation

- [Syntax Reference](dontax.md)
- [Tutorial](dotorial.md)
- [Examples](doamples.md)
- [FAQ](doq.md)
- [Error Reference](dorors.md)
- [API Reference](doi.md)
- [Developer Guide](dov_guide.md)
- [Changelog](doangelog.md)

## Keywords Reference

Qi uses Chinese keywords. Here's a quick reference:

| Chinese | English | Usage |
|---------|---------|-------|
| 令 | let | Variable declaration |
| 设 | set | Variable assignment |
| 若 | if | Condition |
| 再若 | elif | Else if |
| 否则 | else | Else |
| 当 | while | Loop |
| 重复 | repeat | Counted loop |
| 返回 | return | Return |
| 输出 | print | Output |
| 读取 | input | Input |
| 结构 | struct | Struct definition |
| 对 | for | For each |
| 每项 | each | Each item |
| 于 | in | In |
| 包括 | include | Module import |
| 真 | true | Boolean true |
| 假 | false | Boolean false |
| 为 | = | Assignment operator |
| 的 | . | Member access |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
