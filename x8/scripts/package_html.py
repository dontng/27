#!/usr/bin/env python3
"""Bundle standalone HTML papers; keep original PDFs in their existing repo paths."""
from pathlib import Path
import re,zipfile
ROOT=Path(__file__).resolve().parents[2]
folder=ROOT/'x8/html'
with zipfile.ZipFile(folder/'xiao8-html.zip','w',zipfile.ZIP_DEFLATED)as z:
 for p in sorted(folder.glob('*.html')):
  s=p.read_text()
  def replace(m):
   rel=m[1];path,mark,anchor=rel.partition('#');target=(folder/path).resolve().relative_to(ROOT).as_posix()
   return 'href="https://github.com/dontng/27/blob/main/'+target+(mark+anchor if mark else '')+'"'
  s=re.sub(r'href="(\.\./[^"]+)"',replace,s)
  z.writestr(p.name,s)
 z.writestr('README.md','# 肖八HTML试卷\n\n解压后打开index.html。八套HTML均内嵌样式和脚本，可以独立阅读、打印；套卷之间保留跳转。原PDF、Markdown及校对记录的辅助链接指向GitHub项目，需要联网查看。\n\n字体沿用papers，调整正文比例、字重层次与行距。逐题文字与二轮校订Markdown一致。浏览器交互与手机实机显示未在当前环境实测。\n')
print(folder/'xiao8-html.zip')
