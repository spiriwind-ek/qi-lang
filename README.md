# 奇语言（Qi）

用中文实现程序的编写。

## 快速开始

```bash
# 运行文件
python main.py examples/hello.qi

# 交互式Shell
python qish.py

# 格式化代码
python src/qifmt.py your_code.qi
```

## 目录结构

```
qi-lang/
├── src/                # 源代码
├── tests/              # 测试
├── examples/           # 示例
│   ├── hello.qi
│   ├── math.qi
│   ├── math_utils.qi
│   └── test_include.qi
├── docs/               # 文档
│   ├── SYNTAX.md       # 语法规范
│   ├── TUTORIAL.md     # 完整教程
│   ├── API.md          # API参考
│   ├── FAQ.md          # 常见问题
│   ├── ERRORS.md       # 错误信息
│   └── EXAMPLES.md     # 示例集合
├── main.py             # 文件执行入口
├── qish.py             # 交互式Shell
├── README.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## 语法概览

```
令 整数 X 为 10。                          // 变量声明
设 X 为 20。                               // 变量赋值
输出 X。                                   // 输出

若 X 大于 0 则：输出 "正数"。否则：输出 "负数"。 // 条件
当 X 小于 10 时：设 X 为 X 加 1。          // 循环

令 整数 求和 为（整数 A、整数 B）：返回 A 加 B。 // 函数
令 整数列 列表 为 [1、2、3]。               // 列表
令 结构 学生 含：文本 姓名、整数 年龄。      // 结构体
```

## 文档

- [语法规范](docs/SYNTAX.md)
- [完整教程](docs/TUTORIAL.md)
- [API参考](docs/API.md)
- [常见问题](docs/FAQ.md)
- [错误信息](docs/ERRORS.md)
- [示例集合](docs/EXAMPLES.md)

## 测试

```bash
python tests/test_lexer.py
python tests/test_interpreter.py
python tests/test_turing.py
```
