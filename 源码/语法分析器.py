"""奇语言 语法分析器（递归下降）

转发层——具体实现在：
- 表达式解析器.py：ExprParser（关键字解析、表达式优先级解析）
- 语句解析器.py：StmtParser(ExprParser)（语句解析、块解析）

铁律：
1. 关键字由语法分析器根据上下文判断，词法分析器只输出 IDENT
2. 句号。= DOT 为唯一语句终止符
3. 每个 parse_xxx() 方法从当前 token 开始，返回对应 AST 节点
"""
from 语句解析器 import StmtParser as Parser  # noqa: F401
from 表达式解析器 import ParseError  # noqa: F401
