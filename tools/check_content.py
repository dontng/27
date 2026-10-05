"""检查Markdown链接、折叠及结构；不评定知识正确性或学习掌握。"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
links = 0
folds = 0
files = sorted(ROOT.rglob('*.md'))
for path in files:
    content = path.read_text(encoding='utf-8')
    relative = path.relative_to(ROOT)
    # 去掉代码示例，避免把示例中的标签和链接当页面结构。
    visible = re.sub(r'```[^\n]*\n.*?```', '', content, flags=re.S)
    visible = re.sub(r'`[^`\n]+`', '', visible)
    if content.count('```') % 2:
        errors.append(f'{relative}: 代码块未闭合')
    stack = []
    for tag in re.finditer(r'<details(?:\s+open)?\s*>|</details>', visible):
        if tag.group().startswith('</'):
            if not stack:
                errors.append(f'{relative}: 多余details结束标签')
            else:
                stack.pop()
        else:
            stack.append(tag.start())
            folds += 1
    if stack:
        errors.append(f'{relative}: details未闭合')
    for target in re.findall(r'\]\(([^)]+)\)', visible):
        if re.match(r'[a-zA-Z]+:', target) or target.startswith('#'):
            continue
        destination = target.split('#', 1)[0]
        if not (path.parent / destination).exists():
            errors.append(f'{relative}: 链接不存在 {target}')
        links += 1
    if re.search(r'^\s*\|?\s*:?-{3,}:?\s*\|', visible, flags=re.M):
        errors.append(f'{relative}: 教学页面出现Markdown表格')
print(f'{len(files)} Markdown文件，{links} 本地链接，{folds} 折叠；{len(errors)} 错误')
for error in errors:
    print(error)
sys.exit(bool(errors))
