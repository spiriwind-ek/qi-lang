#!/usr/bin/env python3
"""奇语言交互式Shell (qish)"""
import sys
import os
import readline

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from 词法分析器 import Lexer
from 语法分析器 import Parser
from 解释器 import Interpreter

# 历史记录文件
HISTORY_FILE = os.path.expanduser('~/.qi_history')


def setup_readline():
    """配置 readline：行编辑、历史命令"""
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)
    import atexit
    atexit.register(readline.write_history_file, HISTORY_FILE)


def run_source(source):
    """执行一段源代码"""
    interp = Interpreter()
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    interp.execute(ast)
    for out in interp.output:
        print(out)


def main():
    # 管道模式：一次性读取所有输入
    if not sys.stdin.isatty():
        source = sys.stdin.read()
        if source.strip():
            try:
                run_source(source)
            except Exception as e:
                print(f"错误: {e}")
                sys.exit(1)
        return

    # 交互模式
    setup_readline()
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

        if line in ('退出', '退出。', '退出.'):
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
