# mini-Scheme 解释器

本项目按照课程提供的 `spec.md`，借助 AI 完成解释器实现、调试与测试。
使用 Python 3.10 或更高版本，无需安装第三方库，入口为 `src/main.py`。

支持算术与比较、条件分支、变量定义、函数与递归、词法作用域与闭包、
列表与点对，以及字符串和输出操作。

## 运行

在仓库根目录运行示例：

```text
python src/main.py example/01_arithmetic.scm
```

传入多个文件时，它们共享全局环境：

```text
python src/main.py file1.scm file2.scm
```

没有文件参数时，从标准输入读取 Scheme 程序。
如果本机命令名为 `python3`，将以上命令中的 `python` 替换为 `python3`。

## 验证

课程提供的验收测试：

```text
python autograder.pyz python src/main.py
```

补充测试：

```text
python -m unittest discover -s tests -v
```

当前版本已通过全部 12 组验收测试和 19 项补充测试。
补充测试检查负数及大整数除法、闭包与递归、并行 let 绑定、
点对和结构相等、字符串转义、短路求值、输入输出以及多文件共享环境。

## 目录与模块

| 文件或目录 | 职责 |
| --- | --- |
| `src/main.py` | 命令行入口，读取程序并输出顶层结果 |
| `src/lexer.py` | 词法分析，处理注释和字符串转义 |
| `src/parser.py` | 语法分析，处理引用简写和点对 |
| `src/values.py` | 符号、空表、点对、过程与闭包等值类型 |
| `src/environment.py` | 变量绑定及词法环境查找 |
| `src/evaluator.py` | 特殊形式求值与过程调用 |
| `src/primitives.py` | 算术、比较、列表、谓词及输出等内置过程 |
| `src/printer.py` | 值的打印格式 |
| `tests/` | 补充测试 |
| `example/` | 课程提供的六个示例程序 |
| `spec.md` | 课程提供的语言规范 |
| `autograder.pyz` | 课程提供的验收工具 |

课程起始仓库：https://github.com/woo114515/minischeme-starter

