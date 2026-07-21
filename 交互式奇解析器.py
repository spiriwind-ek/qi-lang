#!/usr/bin/env python3
"""奇语言交互式奇解析器 (qish)"""
import sys
import os
import readline

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '源码'))

from 词法分析器 import Lexer
from 语法分析器 import Parser
from 解释器 import Interpreter

HISTORY_FILE = os.path.expanduser('~/.qi_history')


def setup_readline():
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)
    import atexit
    atexit.register(readline.write_history_file, HISTORY_FILE)


def run_source(source):
    result = Interpreter(use_vm=True).run(source)
    for out in result:
        print(out)


def main():
    if not sys.stdin.isatty():
        source = sys.stdin.read()
        if source.strip():
            try:
                run_source(source)
            except Exception as e:
                print(f"错误: {e}")
                sys.exit(1)
        return

    setup_readline()
    print("奇语言 Shell v0.1.2-alpha")
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
            result = Interpreter(use_vm=True).run(line)
            if result:
                for out in result:
                    print(out)
        except Exception as e:
            print(f"错误: {e}")


if __name__ == '__main__':
    main()
