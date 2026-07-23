"""关键字映射表 — 语法分析器根据上下文判断"""
from 记号 import TokenType


# 始终关键字（在任何位置出现都是关键字）
ALWAYS = {
    '的': TokenType.MEMBER_ACCESS,
    '为': TokenType.ASSIGN,
    '。': TokenType.DOT,
    '：': TokenType.COLON,
    '；': TokenType.SEMI,
    '、': TokenType.ENUM,
    '（': TokenType.LPAREN,
    '）': TokenType.RPAREN,
    '【': TokenType.LBRACK,
    '】': TokenType.RBRACK,
}

# 跟在 DOT/COLON/SEMI 后或文件开头时是关键字
STMT_START = {
    '令': TokenType.LET,
    '设': TokenType.SET,
    '若': TokenType.IF,
    '再若': TokenType.ELIF,
    '否则': TokenType.ELSE,
    '当': TokenType.WHILE,
    '重复': TokenType.REPEAT,
    '返回': TokenType.RETURN,
    '输出': TokenType.OUTPUT,
    '读': TokenType.INPUT,
    '结构': TokenType.STRUCT,
    '包括': TokenType.INCLUDE,
    '对': TokenType.IN,
    '调': TokenType.INVOKE,
}

# 跟在特定前驱后时是关键字
AFTER_PREV = {
    TokenType.MEMBER_ACCESS: {
        '长度': TokenType.LENGTH,
        '每个': TokenType.EACH,
    },
    TokenType.IDENT: {
        '含': TokenType.CONTAINS,
        '每个': TokenType.EACH,
    },
    TokenType.STRUCT: {
        '含': TokenType.CONTAINS,
    },
}

# 跟在 LET 后时是类型或声明关键字
AFTER_LET = {
    '整数': TokenType.TYPE_INT,
    '小数': TokenType.TYPE_FLOAT,
    '文本': TokenType.TYPE_STR,
    '布尔': TokenType.TYPE_BOOL,
    '空': TokenType.TYPE_VOID,
    '无': TokenType.TYPE_NULL,
    '列': TokenType.TYPE_LIST,
    '整数列': TokenType.TYPE_LIST,
    '小数列': TokenType.TYPE_LIST,
    '文本列': TokenType.TYPE_LIST,
    '结构': TokenType.STRUCT,  # 令 结构 P 含：...
}

# 在表达式位置时是关键字
EXPR_KEYWORDS = {
    '真': TokenType.TRUE,
    '假': TokenType.FALSE,
    '无': TokenType.TYPE_NULL,
    '则': TokenType.THEN,
    '时': TokenType.THEN,
    '次': TokenType.TIMES,
    '若': TokenType.IF,       # 三元表达式
    '再若': TokenType.ELIF,   # 三元表达式
    '否则': TokenType.ELSE,   # 三元表达式
}

# 二元运算符（在两个表达式之间）
BIN_OPS = {
    '加': TokenType.ADD,
    '减': TokenType.SUB,
    '乘': TokenType.MUL,
    '除': TokenType.DIV,
    '等于': TokenType.EQ,
    '不等于': TokenType.NE,
    '大于': TokenType.GT,
    '小于': TokenType.LT,
    '大于等于': TokenType.GE,
    '小于等于': TokenType.LE,
    '且': TokenType.AND,
    '或': TokenType.OR,
    '抑或': TokenType.XOR,
}

# 一元运算符（在表达式前）
UNARY_OPS = {
    '非': TokenType.NOT,
}
