"""栈式字节码虚拟机"""
from 字节码 import Chunk, ObjClosure, CallFrame, ObjFunction
from 指令加载器 import OpCode
from 环境 import NativeFunction, RUNTIME_ERROR_MESSAGES


class ObjUpvalue:
    """闭包捕获的 upvalue（用 list 包装实现引用语义）"""
    def __init__(self, initial_value=None):
        self.ref = [initial_value]  # list 包装 = 可变的"指针"
    
    def value(self):
        return self.ref[0]
    
    def set(self, val):
        self.ref[0] = val


class VMRuntimeError(Exception):
    def __init__(self, msg):
        for key, friendly in RUNTIME_ERROR_MESSAGES.items():
            if key in msg:
                super().__init__(f"{msg}\n提示: {friendly}")
                return
        super().__init__(msg)


class VM:
    """栈式字节码虚拟机"""
    
    def __init__(self):
        self.stack: list = []         # 值栈
        self.globals: dict = {}       # 全局变量表
        self.frames: list[CallFrame] = []  # 调用栈
        self.output: list[str] = []   # 输出
        self._init_stdlib()
    
    def _init_stdlib(self):
        """加载标准库到全局变量"""
        try:
            from 标准库 import 标准库
            for name, module in 标准库.items():
                self.globals[name] = module
        except ImportError:
            pass  # 标准库还没建的时候不报错
    
    # ─── 栈操作 ───
    
    def push(self, value):
        self.stack.append(value)
    
    def pop(self) -> object:
        if not self.stack:
            raise VMRuntimeError("栈为空")
        return self.stack.pop()
    
    def peek(self, distance: int = 0) -> object:
        if distance >= len(self.stack):
            raise VMRuntimeError("栈为空")
        return self.stack[-1 - distance]
    
    # ─── 字节码读取 ───
    
    def read_byte(self, frame: CallFrame) -> int:
        b = frame.closure.func.chunk.code[frame.ip]
        frame.ip += 1
        return b
    
    def read_short(self, frame: CallFrame) -> int:
        hi = self.read_byte(frame)
        lo = self.read_byte(frame)
        return (hi << 8) | lo
    
    def read_constant(self, frame: CallFrame):
        idx = self.read_byte(frame)
        return frame.closure.func.chunk.constants[idx]
    
    def current_line(self, frame: CallFrame) -> int:
        """获取当前指令的行号"""
        ip = frame.ip - 1
        chunk = frame.closure.func.chunk
        if 0 <= ip < len(chunk.lines):
            return chunk.lines[ip]
        return 0
    
    # ─── 错误 ───
    
    def runtime_error(self, msg: str):
        """报运行时错误，带调用栈"""
        trace = []
        for i in range(len(self.frames) - 1, -1, -1):
            f = self.frames[i]
            name = f.closure.func.name or "主程序"
            line = self.current_line(f)
            trace.append(f"  【第 {line} 行】在 {name}（）")
        full = f"运行时错误: {msg}\n" + "\n".join(trace)
        raise VMRuntimeError(full)
    
    # ─── 调用 ───
    
    def call(self, closure: ObjClosure, arg_count: int) -> bool:
        """创建调用帧。栈布局：[函数, 参数1, 参数2, ...]"""
        func = closure.func
        if arg_count != func.arity:
            self.runtime_error(
                f"函数 '{func.name}' 期望 {func.arity} 个参数，但收到 {arg_count} 个"
            )
            return False
        if len(self.frames) >= 1024:
            self.runtime_error("调用栈溢出")
            return False
        # slots 指向第一个参数，函数在 slots-1
        frame = CallFrame(
            closure=closure, ip=0,
            slots=len(self.stack) - arg_count
        )
        # 预分配栈空间给局部变量
        needed = frame.slots + func.max_slot
        while len(self.stack) < needed:
            self.stack.append(None)
        self.frames.append(frame)
        return True
    
    def call_value(self, callee, arg_count: int) -> bool:
        """调用一个值（函数或原生函数）"""
        if isinstance(callee, ObjClosure):
            return self.call(callee, arg_count)
        if isinstance(callee, NativeFunction):
            args = []
            for _ in range(arg_count):
                args.insert(0, self.pop())
            self.pop()  # 弹出函数本身
            result = callee.impl(*args)
            self.push(result)
            return True
        self.runtime_error(f"只能调用函数")
        return False
    
    # ─── 主循环 ───
    
    def run(self, chunk: Chunk):
        """执行字节码"""
        # 创建主函数闭包
        main_func = ObjFunction(name=None, arity=0, chunk=chunk, max_slot=chunk.max_slot)
        main_closure = ObjClosure(func=main_func)
        self.frames.append(CallFrame(closure=main_closure, ip=0, slots=0))
        # 预分配主栈空间
        while len(self.stack) < main_func.max_slot:
            self.stack.append(None)
        
        frame = self.frames[-1]
        
        while True:
            instruction = self.read_byte(frame)
            opcode = OpCode(instruction)
            
            if opcode == OpCode.CONSTANT:
                val = self.read_constant(frame)
                self.push(val)
            
            elif opcode == OpCode.NIL:
                self.push(None)
            
            elif opcode == OpCode.TRUE:
                self.push(True)
            
            elif opcode == OpCode.FALSE:
                self.push(False)
            
            elif opcode == OpCode.POP:
                self.pop()
            
            elif opcode == OpCode.DUP:
                self.push(self.peek())
            
            elif opcode == OpCode.DEFINE_GLOBAL:
                name = self.read_constant(frame)
                value = self.peek(0)
                self.globals[name] = value
                self.pop()
            
            elif opcode == OpCode.GET_GLOBAL:
                name = self.read_constant(frame)
                if name not in self.globals:
                    self.runtime_error(f"未定义变量 '{name}'")
                    return
                self.push(self.globals[name])
            
            elif opcode == OpCode.SET_GLOBAL:
                name = self.read_constant(frame)
                if name not in self.globals:
                    self.runtime_error(f"未定义变量 '{name}'")
                    return
                self.globals[name] = self.peek(0)
            
            elif opcode == OpCode.GET_LOCAL:
                slot = self.read_byte(frame)
                self.push(self.stack[frame.slots + slot])
            
            elif opcode == OpCode.SET_LOCAL:
                slot = self.read_byte(frame)
                idx = frame.slots + slot
                while len(self.stack) <= idx:
                    self.stack.append(None)
                self.stack[idx] = self.peek(0)
            
            elif opcode == OpCode.ADD:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    self.push(a + b)
                elif isinstance(a, str) and isinstance(b, str):
                    self.push(a + b)
                else:
                    self.runtime_error(f"类型错误：不能对 {type(a).__name__} 和 {type(b).__name__} 做加法")
                    return
            
            elif opcode == OpCode.SUBTRACT:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    self.push(a - b)
                else:
                    self.runtime_error(f"类型错误：不能对 {type(a).__name__} 和 {type(b).__name__} 做减法")
                    return
            
            elif opcode == OpCode.MULTIPLY:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    self.push(a * b)
                else:
                    self.runtime_error(f"类型错误：不能对 {type(a).__name__} 和 {type(b).__name__} 做乘法")
                    return
            
            elif opcode == OpCode.DIVIDE:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    if b == 0:
                        self.runtime_error("算术除零")
                        return
                    result = a / b
                    if isinstance(a, int) and isinstance(b, int) and result == int(result):
                        result = int(result)
                    self.push(result)
                else:
                    self.runtime_error(f"类型错误：不能对 {type(a).__name__} 和 {type(b).__name__} 做除法")
                    return
            
            elif opcode == OpCode.NEGATE:
                a = self.pop()
                if isinstance(a, (int, float)):
                    self.push(-a)
                else:
                    self.runtime_error(f"类型错误：不能对 {type(a).__name__} 取负")
                    return
            
            elif opcode == OpCode.EQUAL:
                b = self.pop()
                a = self.pop()
                self.push(a == b)
            
            elif opcode == OpCode.GREATER:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    self.push(a > b)
                else:
                    self.runtime_error(f"类型错误：不能比较 {type(a).__name__} 和 {type(b).__name__}")
                    return
            
            elif opcode == OpCode.LESS:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    self.push(a < b)
                else:
                    self.runtime_error(f"类型错误：不能比较 {type(a).__name__} 和 {type(b).__name__}")
                    return
            
            elif opcode == OpCode.NOT:
                a = self.pop()
                self.push(not a)
            
            elif opcode == OpCode.JUMP:
                offset = self.read_short(frame)
                frame.ip += offset
            
            elif opcode == OpCode.JUMP_IF_FALSE:
                offset = self.read_short(frame)
                if not self.is_truthy(self.peek(0)):
                    frame.ip += offset
            
            elif opcode == OpCode.LOOP:
                offset = self.read_short(frame)
                frame.ip -= offset
            
            elif opcode == OpCode.CALL:
                arg_count = self.read_byte(frame)
                callee = self.peek(arg_count)
                if not self.call_value(callee, arg_count):
                    return
                frame = self.frames[-1]  # 切换到新帧
            
            elif opcode == OpCode.CLOSURE:
                func = self.read_constant(frame)
                closure = ObjClosure(func=func)
                for _ in range(func.upvalue_count):
                    is_local = self.read_byte(frame)
                    index = self.read_byte(frame)
                    if is_local:
                        # 捕获当前栈上的局部变量值
                        val = self.stack[frame.slots + index]
                        up = ObjUpvalue(val)
                    else:
                        # 继承外层闭包的 upvalue（共享引用）
                        up = frame.closure.upvalues[index]
                    closure.upvalues.append(up)
                self.push(closure)
            
            elif opcode == OpCode.GET_UPVALUE:
                slot = self.read_byte(frame)
                self.push(frame.closure.upvalues[slot].value())
            
            elif opcode == OpCode.SET_UPVALUE:
                slot = self.read_byte(frame)
                frame.closure.upvalues[slot].set(self.peek(0))
            
            elif opcode == OpCode.RETURN:
                result = self.pop()
                # 先记录当前帧的 slots（指向第一个参数），再 pop 帧
                return_slots = frame.slots
                self.frames.pop()
                if not self.frames:
                    return
                # 清理栈到函数之前（slots-1 指向函数位置）
                self.stack = self.stack[:return_slots - 1]
                self.push(result)
                # 切换到调用者帧
                frame = self.frames[-1]
            
            elif opcode == OpCode.BUILD_LIST:
                count = self.read_byte(frame)
                items = []
                for _ in range(count):
                    items.insert(0, self.pop())
                self.push(items)
            
            elif opcode == OpCode.BUILD_STRUCT:
                count = self.read_byte(frame)
                field_names = self.read_constant(frame)
                obj = {}
                # 弹出值（逆序），与字段名配对
                for i in range(count - 1, -1, -1):
                    val = self.pop()
                    if i < len(field_names):
                        obj[field_names[i]] = val
                self.push(obj)
            
            elif opcode == OpCode.INDEX_GET:
                index = self.pop()
                lst = self.pop()
                if not isinstance(lst, list):
                    self.runtime_error("不是列表")
                    return
                if not isinstance(index, int):
                    self.runtime_error("索引必须是整数")
                    return
                if index < 1 or index > len(lst):
                    self.runtime_error(f"索引 {index} 越界（列表长度 {len(lst)}）")
                    return
                self.push(lst[index - 1])
            
            elif opcode == OpCode.INDEX_SET:
                value = self.pop()
                index = self.pop()
                lst = self.pop()
                if not isinstance(lst, list):
                    self.runtime_error("不是列表")
                    return
                if not isinstance(index, int):
                    self.runtime_error("索引必须是整数")
                    return
                if index < 1 or index > len(lst):
                    self.runtime_error(f"索引 {index} 越界")
                    return
                lst[index - 1] = value
                self.push(value)
            
            elif opcode == OpCode.GET_PROP:
                name = self.read_constant(frame)
                obj = self.pop()
                if not isinstance(obj, dict):
                    self.runtime_error(f"不是结构体")
                    return
                if name not in obj:
                    self.runtime_error(f"未定义成员 '{name}'")
                    return
                self.push(obj[name])
            
            elif opcode == OpCode.SET_PROP:
                name = self.read_constant(frame)
                value = self.pop()
                obj = self.pop()
                if not isinstance(obj, dict):
                    self.runtime_error(f"不是结构体")
                    return
                obj[name] = value
                self.push(value)
            
            elif opcode == OpCode.INVOKE:
                method_name = self.read_constant(frame)
                arg_count = self.read_byte(frame)
                receiver = self.peek(arg_count)
                
                # 模块调用（字典查找）
                if isinstance(receiver, dict):
                    method = receiver.get(method_name)
                    if method is None:
                        self.runtime_error(f"模块中无此方法 '{method_name}'")
                        return
                    if isinstance(method, NativeFunction):
                        args = []
                        for _ in range(arg_count):
                            args.insert(0, self.pop())
                        self.pop()  # 弹出模块
                        result = method.impl(*args)
                        self.push(result)
                    else:
                        self.runtime_error(f"'{method_name}' 不是可调用的方法")
                        return
                elif isinstance(receiver, list):
                    # 列表方法
                    if method_name == '长度':
                        if arg_count != 0:
                            self.runtime_error(f"'长度' 不需要参数")
                            return
                        lst = self.pop()
                        self.push(len(lst))
                    elif method_name == '插入':
                        if arg_count != 2:
                            self.runtime_error(f"'插入' 需要两个参数")
                            return
                        value = self.pop()
                        index = self.pop()
                        lst = self.pop()
                        lst.insert(index - 1, value)
                        self.push(len(lst))
                    elif method_name == '删除':
                        if arg_count != 1:
                            self.runtime_error(f"'删除' 需要一个参数")
                            return
                        index = self.pop()
                        lst = self.pop()
                        removed = lst.pop(index - 1)
                        self.push(removed)
                    else:
                        self.runtime_error(f"列表没有方法 '{method_name}'")
                        return
                elif isinstance(receiver, str):
                    # 字符串方法
                    if method_name == '长度':
                        if arg_count != 0:
                            self.runtime_error(f"'长度' 不需要参数")
                            return
                        s = self.pop()
                        self.push(len(s))
                    else:
                        self.runtime_error(f"字符串没有方法 '{method_name}'")
                        return
                else:
                    self.runtime_error(f"只有模块、列表、字符串支持方法调用")
                    return
            
            elif opcode == OpCode.PRINT:
                val = self.pop()
                s = str(val)
                import sys
                sys.stdout.write(s)
                sys.stdout.flush()
                self.output.append(s)
            
            elif opcode == OpCode.INPUT:
                prompt = self.pop() if self.stack else ""
                try:
                    value = input(str(prompt) if prompt else "")
                except EOFError:
                    value = ""
                self.push(value)
            
            else:
                self.runtime_error(f"未知指令: {opcode.name}")
                return
    
    @staticmethod
    def is_truthy(value) -> bool:
        """判断是否为真值（与 Python 一致：None/0/""/[] 为假）"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True
    
    def get_output(self) -> list[str]:
        return self.output
