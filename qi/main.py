#!/usr/bin/env python3
"""奇语言 CLI 入口——子命令模式"""
import sys
import os

# 兼容两种调用方式：
#   python3 奇.py        → __file__ = 奇.py        → 源码/ 在旁边的 源码/
#   python3 -m qi        → __file__ = qi/__main__.py → 源码/ 在 ../源码/
_this_dir = os.path.dirname(os.path.abspath(__file__))
_root = None
for _p in (_this_dir, os.path.join(_this_dir, '..')):
    _cand = os.path.join(_p, '源码')
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)
        _root = _p
        break
# 加入项目根目录，以便 import qish
if _root and _root not in sys.path:
    sys.path.insert(0, _root)

from 定义加载器 import 源码后缀, 编译后缀, 缓存目录候选


# ── 子命令定义 ─────────────────────────────────────

SUBCOMMANDS = {
    'run':  ('运行', '运行一个 .qi 文件'),
    'fmt':  ('格式化', '格式化奇语言代码'),
    'shell':('交互', '启动交互式 Shell'),
}

_CN_TO_EN = {v[0]: k for k, v in SUBCOMMANDS.items()}


def _解析子命令() -> tuple[str, list[str]] | None:
    if len(sys.argv) < 2:
        return None
    cmd = sys.argv[1]
    rest = sys.argv[2:]
    if cmd in SUBCOMMANDS:
        return (cmd, rest)
    if cmd in _CN_TO_EN:
        return (_CN_TO_EN[cmd], rest)
    return None


# ── 缓存逻辑 ───────────────────────────────────────

def _缓存路径(源码路径: str) -> str | None:
    base = os.path.basename(源码路径)
    root, ext = os.path.splitext(base)
    if ext not in 源码后缀:
        return None
    src_dir = os.path.dirname(源码路径) or '.'
    for d in 缓存目录候选:
        cand_dir = os.path.join(src_dir, d)
        if os.path.isdir(cand_dir):
            for suf in 编译后缀:
                cand = os.path.join(cand_dir, root + suf)
                if os.path.exists(cand):
                    return cand
            return os.path.join(cand_dir, root + 编译后缀[0])
    cache_dir = os.path.join(src_dir, 缓存目录候选[0])
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, root + 编译后缀[0])


def _缓存有效(源码路径: str, 缓存路径: str) -> bool:
    if not os.path.exists(缓存路径):
        return False
    return os.path.getmtime(缓存路径) >= os.path.getmtime(源码路径)


# ── 子命令实现 ─────────────────────────────────────

def _cmd_run(args: list[str]):
    if not args:
        print("用法: qi run <文件.qi>")
        sys.exit(1)
    filename = args[0]

    # 检查后缀
    _, ext = os.path.splitext(filename)
    if ext not in 源码后缀:
        print(f"错误: 不支持的文件后缀 '{ext}'，仅支持: {'、'.join(源码后缀)}")
        sys.exit(1)

    cache_path = _缓存路径(filename)

    # 1. 尝试从缓存加载并执行
    if cache_path and _缓存有效(filename, cache_path):
        try:
            from 字节码 import Chunk
            from 虚拟机 import VM
            with open(cache_path, 'rb') as f:
                chunk = Chunk.deserialize(f.read())
            vm = VM()
            vm.run(chunk)
            return
        except Exception as e:
            print(f"缓存失效，重新编译: {e}")

    # 2. 读取源码
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        # 3. 编译：Lexer → Parser → Compiler
        from 词法分析器 import Lexer
        from 语法分析器 import Parser
        from 编译器 import Compiler, CompileError
        from 表达式解析器 import ParseError

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        compiler = Compiler()
        chunk = compiler.compile(ast)

        # 4. 编译成功后写缓存（即使运行时失败，编译缓存也有效）
        if cache_path:
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'wb') as f:
                    f.write(chunk.serialize())
            except Exception as e:
                print(f"缓存写入失败: {e}", file=sys.stderr)

        # 5. 执行字节码
        from 虚拟机 import VM
        vm = VM()
        vm.run(chunk)

    except (ParseError, CompileError) as e:
        from 错误报告 import format_error_safe
        print(format_error_safe(e, source), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        from 错误报告 import format_error_safe
        print(format_error_safe(e, source), file=sys.stderr)
        sys.exit(1)


def _cmd_fmt(args: list[str]):
    if not args:
        print("用法: qi fmt <文件.qi>")
        sys.exit(1)
    filename = args[0]
    in_place = '-i' in args

    with open(filename, 'r', encoding='utf-8') as f:
        raw = f.read()
    try:
        from 格式化奇 import format_qi, FormatError
        formatted = format_qi(raw)
        if in_place:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formatted)
        else:
            print(formatted, end='')
    except FormatError as e:
        print(f"格式化错误: {e}")
        sys.exit(1)


def _cmd_shell(args: list[str]):
    from qi.qish import main as shell_main
    shell_main()


def _cmd_help():
    print("奇语言 v0.2.1-beta")
    print()
    print("用法: qi <子命令> [参数]")
    print()
    for en, (cn, desc) in SUBCOMMANDS.items():
        print(f"  qi {en:<8} / qi {cn:<6}  {desc}")
    print()
    print("示例:")
    print("  qi run hello.qi")
    print("  qi 运行 hello.qi")
    print("  qi fmt hello.qi")
    print("  qi shell")


# ── 主入口 ────────────────────────────────────────

def main():
    parsed = _解析子命令()
    if parsed is None:
        _cmd_help()
        sys.exit(0 if len(sys.argv) == 1 else 1)

    cmd, args = parsed
    match cmd:
        case 'run':   _cmd_run(args)
        case 'fmt':   _cmd_fmt(args)
        case 'shell': _cmd_shell(args)
        case _:
            print(f"未知子命令: {cmd}")
            sys.exit(1)


if __name__ == '__main__':
    main()
