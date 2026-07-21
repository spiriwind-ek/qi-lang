# CONTRIBUTING

## 如何贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 开发环境

```bash
# 克隆项目
git clone https://github.com/spiriwind-ek/qi-lang.git

# 运行测试
python tests/test_lexer.py
python tests/test_interpreter.py
python tests/test_turing.py

# 运行格式化工具
python src/qifmt.py examples/hello.qi
```

## 代码规范

- 使用4空格缩进
- 函数名使用snake_case
- 类名使用PascalCase
- 所有公共函数需要docstring

## 提交规范

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 其他

## 问题反馈

请在 GitHub Issues 中提交问题。
