"""错误报告：带源码上下文的错误信息格式化

用法：
  from 错误报告 import format_error_safe
  
  try:
      ...
  except (ParseError, CompileError, LexerError) as e:
      print(format_error_safe(e, source))
"""

import sys


def _get_error_line_info(e) -> tuple[int, int]:
    """从异常对象中提取行号和列号"""
    # LexerError: line, col 直接挂载
    if hasattr(e, 'line') and hasattr(e, 'col'):
        return e.line, e.col
    # ParseError: token 上挂 line/col
    if hasattr(e, 'token'):
        return e.token.line, e.token.col
    # CompileError: line 直接挂载
    if hasattr(e, 'line') and e.line > 0:
        return e.line, 0
    return 0, 0


def format_error(msg: str, source: str, line: int, col: int = 0) -> str:
    """格式化错误信息，带源码上下文

    输出示例：
      第3行第10列: 期望 ASSIGN，得到 MUL
          |
       3  | 令 整数 X 为 10
          |           ^
    """
    if not source or line <= 0:
        return msg

    lines = source.split('\n')
    if line > len(lines):
        return msg

    # 行号宽度（对齐用）
    width = len(str(line + 1))
    pad = ' ' * width

    ctx_parts = [f"  {pad}│"]
    
    # 上下文行（错误行前一行）
    if line > 1:
        prev_line = lines[line - 2]
        ctx_parts.append(f"  {str(line - 1).rjust(width)} │ {prev_line}")
    
    # 错误行
    error_line = lines[line - 1]
    ctx_parts.append(f"  {str(line).rjust(width)} │ {error_line}")
    
    # 指针
    if col > 0 and col <= len(error_line) + 1:
        ctx_parts.append(f"  {pad} │ {' ' * (col - 1)}^")

    return f"{msg}\n" + '\n'.join(ctx_parts)


def format_error_safe(e: Exception, source: str = '') -> str:
    """安全格式化异常，提取 line/col 并显示源码上下文"""
    msg = str(e)
    line, col = _get_error_line_info(e)
    if line > 0 and source:
        return format_error(msg, source, line, col)
    return msg
