#!/usr/bin/env python3
"""奇语言解释器入口"""
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from 词法分析器 import Lexer
from 语法分析器 import Parser
from 解释器 import Interpreter
from 配置 import 所有后缀


def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <文件名>")
        sys.exit(1)

    filename = sys.argv[1]
    # 文件后缀检测
    _, ext = os.path.splitext(filename)
    if ext and ext not in 所有后缀:
        print(f"错误: 不支持的文件后缀 '{ext}'，支持: {', '.join(所有后缀)}")
        sys.exit(1)

    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        interp = Interpreter()
        interp.run(source)
        for line in interp.output:
            print(line)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
