#!/usr/bin/env python3
"""奇语言交互式Shell (qish)"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


def main():
    interp = Interpreter()
    print("奇语言 Shell v0.0.1")
    print("输入代码执行，输入 退出 结束")
    print()

    while True:
        try:
            line = input("qi> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        line = line.strip()
        if not line:
            continue

        # 退出命令（支持带句号和不带句号）
        if line in ('退出', '退出。', '退出。'):
            break

        try:
            tokens = Lexer(line).tokenize()
            ast = Parser(tokens).parse()
            interp.execute(ast)
            if interp.output:
                for out in interp.output:
                    print(out)
                interp.output = []
        except Exception as e:
            print(f"错误: {e}")


if __name__ == '__main__':
    main()
