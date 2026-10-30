#!/usr/bin/env python3
"""Build the PDF download index from exports with completed validation."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import H
R=Path(__file__).resolve().parents[2]
validation=json.loads((R/'tools/papers/pdf-validation.json').read_text());end=int(sys.argv[1]) if len(sys.argv)>1 else 2026
rows=[r for r in validation['checks'] if r['year']<=end]
body='<nav><a href="../index.html">HTML试卷目录</a></nav><h1>考研政治真题 · PDF</h1><p class="subtitle">2012—2026 · 按年份下载</p><p>直接从已审核、已排版的HTML打印导出；不含答案及额外答题留白。纸张为A4，保留原有自然分页。</p><div class="years">'
for r in rows:body+=f'<a href="{r["year"]}.pdf"><strong>{r["year"]} 年</strong><small>PDF · {r["pages"]} 页</small></a>'
body+='</div><p class="note">已转换'+str(len(rows))+'套。导出记录和输入、输出摘要见tools/papers/pdf-manifest.json；文字完整性、A4边界及空白页检查见pdf-validation.json。HTML和题目内容保持原样。</p>'
(R/'papers/pdf/index.html').write_text(H('考研政治历年真题 · PDF下载',body))
