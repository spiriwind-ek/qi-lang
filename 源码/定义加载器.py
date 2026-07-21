"""定义加载器：读取 TOML 语言定义并映射 TokenType"""
import tomllib
from 记号 import TokenType
from pathlib import Path

_dir = Path(__file__).parent


def _load(name):
    with open(_dir / name, 'rb') as f:
        return tomllib.load(f)


def _map(d):
    return {k: getattr(TokenType, v) for k, v in d.items()}


def _flags(d):
    return frozenset({getattr(TokenType, k) for k, v in d.items() if v})


def _types(d):
    return tuple({getattr(TokenType, k) for k, v in d.items() if v})


# ─── 词法定义 ───
词法 = _load('词法定义.toml')
关键字 = _map(词法['关键字'])
类型名 = _map(词法['类型名'])
中文运算符 = _map(词法['中文运算符'])
ASCII运算符 = _map(词法['ASCII运算符'])
标点映射 = {k: (k, getattr(TokenType, v)) for k, v in 词法['标点映射'].items()}

# ─── 语法定义 ───
语法 = _load('语法定义.toml')
语句起始 = _flags(语法['语句起始'])
参数类型 = _types(语法['参数类型'])
声明类型 = _types(语法['声明类型'])
字段类型 = _types(语法['字段类型'])

# ─── 运行时定义 ───
运行时 = _load('运行时定义.toml')
源码后缀 = set(运行时['文件后缀']['源码'])
头文件后缀 = set(运行时['文件后缀']['头文件'])
编译后缀 = 运行时['文件后缀']['编译']  # list，保持 TOML 顺序
所有后缀 = 源码后缀 | 头文件后缀
编译签名 = (运行时['编译缓存']['签名'] + chr(运行时['编译缓存']['版本'])).encode('ascii')
缓存目录候选 = 运行时['编译缓存']['目录']
