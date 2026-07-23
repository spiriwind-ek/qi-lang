#!/usr/bin/env python3
"""奇语言交互式式 Shell"""
import sys
import os
import readline

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '源码'))

from 词法分析器 import Lexer
from 语法分析器 import Parser
from 虚拟机 import VM
from 编译器 import Compiler

HISTORY_FILE = os.path.expanduser('~/.qi_history')


def setup_readline():
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)
    import atexit
    atexit.register(readline.write_history_file, HISTORY_FILE)


class 交互式执行器:
    """持久的执行器，变量跨行保留"""
    def __init__(self):
        self.vm = VM()  # VM 保留全局变量表
        self._declared = set()  # 跨行已声明的全局变量名
    
    def run(self, source):
        from 格式化奇 import normalize_punct, _cn_number_preprocess
        src = normalize_punct(source)
        src = _cn_number_preprocess(src)  # 中文数字→阿拉伯
        tokens = Lexer(src).tokenize()
        ast = Parser(tokens).parse()
        # 传递跨行已声明的全局变量集合，使重复声明用 SET_GLOBAL 而非 DEFINE_GLOBAL
        compiler = Compiler(globals_set=self._declared)
        chunk = compiler.compile(ast)
        self.vm.run(chunk)
        sys.stdout.write('\n')
        sys.stdout.flush()


def run_source(source):
    # 去掉退出命令及其后的内容
    for cmd in ('退出', '退出。', '退出.', 'quit'):
        if cmd in source:
            source = source[:source.index(cmd)]
    source = source.strip()
    if not source:
        return
    from 格式化奇 import normalize_punct, _cn_number_preprocess
    src = normalize_punct(source)
    src = _cn_number_preprocess(src)
    交互式执行器().run(src)


def _read_multiline(first_line: str) -> str:
    """读取多行缩进块（空行结束）"""
    lines = [first_line]
    while True:
        try:
            line = input("... ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():  # 空行 → 结束
            break
        lines.append(line)
    return '\n'.join(lines)


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
    print("奇语言 Shell v0.2.0-beta")
    print("输入代码执行，输入 退出 结束")
    print()

    shell = 交互式执行器()
    while True:
        try:
            raw = input("qi> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw.strip():
            continue

        if raw.strip() in ('退出', '退出。', '退出.'):
            break

        # 多行模式：行以：结尾 → 缩进块
        if raw.rstrip().endswith('：'):
            source = _read_multiline(raw)
        else:
            source = raw.strip()

        try:
            shell.run(source)
        except Exception as e:
            print(f"错误: {e}")


if __name__ == '__main__':
    main()
