# 奇语言 API 参考

## 词法分析器 (Lexer)

### `Lexer(source: str)`

创建词法分析器实例。

**参数：**
- `source`: 源代码字符串

**方法：**
- `tokenize() -> list[Token]`: 返回token列表

**示例：**
```python
from src.lexer import Lexer

tokens = Lexer('令 整数 X 为 10。').tokenize()
for token in tokens:
    print(token)
```

---

## 语法分析器 (Parser)

### `Parser(tokens: list[Token])`

创建语法分析器实例。

**参数：**
- `tokens`: token列表

**方法：**
- `parse() -> Program`: 返回AST程序节点

**示例：**
```python
from src.lexer import Lexer
from src.parser import Parser

tokens = Lexer('令 整数 X 为 10。').tokenize()
ast = Parser(tokens).parse()
```

---

## 解释器 (Interpreter)

### `Interpreter()`

创建解释器实例。

**方法：**
- `run(source: str) -> list[str]`: 执行源代码并返回输出列表

**示例：**
```python
from src.interpreter import Interpreter

interp = Interpreter()
output = interp.run('令 整数 X 为 10。输出 X。')
print(output)  # ['10']
```

---

## 格式化工具 (qifmt)

### `format_qi(raw: str) -> str`

格式化奇语言代码。

**参数：**
- `raw`: 原始代码字符串

**返回：**
- 格式化后的代码字符串

**异常：**
- `FormatError`: 格式化错误

**示例：**
```python
from src.qifmt import format_qi

formatted = format_qi('令整数X为10。输出X。')
print(formatted)
```

---

## 环境 (Environment)

### `Environment(parent: Environment = None)`

创建作用域环境。

**方法：**
- `declare_var(name, value, type_name)`: 声明变量
- `assign_var(name, value)`: 修改变量值
- `get_var(name) -> Any`: 获取变量值
- `get_var_type(name) -> str`: 获取变量类型
- `declare_func(name, func_node)`: 声明函数
- `get_func(name) -> FuncDecl`: 获取函数
- `declare_struct(name, fields)`: 声明结构体
- `get_struct(name) -> list`: 获取结构体
- `child() -> Environment`: 创建子作用域

**示例：**
```python
from src.environment import Environment

env = Environment()
env.declare_var('x', 10, '整数')
print(env.get_var('x'))  # 10
```

---

## Token 类型

| 类型 | 说明 |
|------|------|
| `LET` | 令 |
| `SET` | 设 |
| `IF` | 若 |
| `ELIF` | 再若 |
| `ELSE` | 否则 |
| `WHILE` | 当 |
| `REPEAT` | 重复 |
| `TIMES` | 次 |
| `THEN` | 则/时 |
| `RETURN` | 返回 |
| `INPUT` | 读取 |
| `OUTPUT` | 输出 |
| `TRUE` | 真 |
| `FALSE` | 假 |
| `STRUCT` | 结构 |
| `INCLUDE` | 包括 |
| `TYPE_INT` | 整数 |
| `TYPE_FLOAT` | 小数 |
| `TYPE_STR` | 文本 |
| `TYPE_LIST` | 列（整数列等） |
| `IDENT` | 标识符 |
| `NUMBER` | 数字 |
| `STRING` | 字符串 |
| `ASSIGN` | 为/= |
| `EQ` | 等于/== |
| `GT` | 大于/> |
| `LT` | 小于/< |
| `ADD` | 加/+ |
| `SUB` | 减/- |
| `MUL` | 乘/* |
| `DIV` | 除// |
| `AND` | 且/&& |
| `OR` | 或/\|\| |
| `NOT` | 非/! |
| `DOT` | 。 |
| `SEMI` | 承 |
| `COMMA` | 、 |
| `COLON` | ： |
| `LPAREN` | （ |
| `RPAREN` | ） |
| `LBRACK` | [ |
| `RBRACK` | ] |
| `EOF` | 文件结束 |

---

## AST 节点类型

| 节点 | 说明 |
|------|------|
| `Program` | 程序 |
| `VarDecl` | 变量声明 |
| `VarAssign` | 变量赋值 |
| `BinaryOp` | 二元运算 |
| `UnaryOp` | 一元运算 |
| `IfStatement` | 条件语句 |
| `WhileLoop` | 条件循环 |
| `RepeatLoop` | 计数循环 |
| `FuncDecl` | 函数定义 |
| `FuncCall` | 函数调用 |
| `ReturnStatement` | 返回语句 |
| `ListDecl` | 列表声明 |
| `ListAccess` | 列表访问 |
| `ListLength` | 列表长度 |
| `StructDecl` | 结构体定义 |
| `StructInstantiate` | 结构体实例化 |
| `MemberAccess` | 成员访问 |
| `MemberAssign` | 成员赋值 |
| `IncludeStatement` | 模块导入 |
| `PrintStatement` | 输出语句 |
| `InputStatement` | 输入语句 |
| `Block` | 代码块 |
| `NumberLiteral` | 数字字面量 |
| `StringLiteral` | 字符串字面量 |
| `BoolLiteral` | 布尔字面量 |
| `NullLiteral` | 空值字面量 |
| `Identifier` | 标识符 |
