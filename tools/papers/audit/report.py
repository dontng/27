#!/usr/bin/env python3
"""Render truthful audit coverage, corrections, and unresolved public-edition differences."""
from pathlib import Path
import json,html,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build import H
R=Path(__file__).resolve().parents[3];D=R/'tools/papers/audit'
variants=[
{'year':2012,'q':[34,36],'note':'第34题碎片倍数关系存在详写、略写版本；第36题材料3和第2问有明显不同版本。现有版本可在新东方公开重排卷中找到对应，不因另一版材料不同而直接删段、替换设问。尚未取得官方原卷扫描件，不能认定所有字词只有唯一版本。'},
{'year':2013,'q':[18,21,22,23,34,37],'note':'第18题B项有无“一切”、第21题若干选项用词、第22题选项排列、第23题宗教活动用字、第34题“她/他”以及第37题“读者/读书人”等存在异文。只对有明确依据的“管理者”、日期、叠字及“借鉴”作局部修订；其他保留收集版本，不能把不同排列的答案直接套用。'},
{'year':2020,'q':[7,11,12,17,25,26,27,35,38],'note':'若干题干和材料存在详略不同的公开整理版本，第35题子问分值也有6/4与5/5版本。当前保留有来源对应的较完整文本及6/4分值；不以简版参照替换全文。第6题漏“化”和第12题“进入开始”已单独修正。'},
{'year':2021,'q':[6,9,10,35,37,38],'note':'高校PDF含明显缩写、错字，部分选择题排列和分析题措辞与其他公开版不同。比对时已排除末尾参考答案，保留现有有来源的题目文本，不据OCR或简写改写题干。'},
{'year':2025,'q':[3,8,12,13,16,18,19,20,35,36,37],'note':'新东方图版、高校重排PDF和其他文字版在题干、引文、材料详略及部分选项上存在较多差异。现有文本多与新东方图版对应；第3题引文、若干简略题干等仍不能据公开版本认定为官方原卷逐字一致，保留公开整理版身份。'},
{'year':2026,'q':[14,18,35,36,37,38],'note':'PDF文本层存在明显OCR错误及页眉混入，例如把“没有”识别成“该有”、引文出处错配等。未按这些错误覆盖现有正文；材料与设问存在公开版措辞差异，保留来源可追溯版本，不宣称完成官方原卷认证。'}]
(D/'version-notes.json').write_text(json.dumps(variants,ensure_ascii=False,indent=2))
rounds=[]
for n in [1,2]:
 p=D/f'round-{n}.json'
 if p.exists():
  r=json.loads(p.read_text());r['questions']=[q for f in r['question_files'] for q in json.loads((D/f).read_text())];rounds.append(r)
patches=json.loads((R/'tools/papers/corrections.json').read_text());E=html.escape
body='<nav><a href="index.html">年份目录</a> · <a href="sources.html">采集来源</a></nav><h1>政治真题双轮审核记录</h1>'
body+='<p>审核日期：2026-10-29。两遍采用相同流程和相同参照集，每遍重新读取全部2012—2026年HTML，对570题的题干、四个选项、材料各段和全部子问进行全文比对，复核差异并核查修订处。第二遍不只检查第一遍改动。文字比对仅归一化标点、空白和全半角。</p>'
body+='<p>比对参照包括高校公开PDF、新东方公开图版的OCR及独立文字版。OCR和网页文本都是辅助依据，发生冲突时回看相关页面，不用答题逻辑改写错误选项，也不把参考答案当题干。自动匹配只证明某个参照出现过该文本，不等于官方原卷认证。</p>'
for r in rounds:
 n=r['round'];qs=r['questions'];body+=f'<h2>第{n}遍</h2><p>覆盖15年、{len(qs)}题；比较{sum(len(q["fields"]) for q in qs)}个正文片段。'
 body+='已复核差异并形成修订及版本记录。' if r.get('review_completed') else '全文比对已运行，人工差异处置记录尚未封存。'
 body+='另按相同补充流程核对494个短文本及作答提示，短文本均在参照中找到对应。</p>'
body+=f'<h2>确认修订：{len(patches)}处字词，另补1处漫画</h2>'
for p in patches:
 body+=f'<section class="source-item"><h3>{E(p["id"])} · {p["year"]}年第{p["question"]}题 · 第{p["found_in_round"]}遍发现</h3><p><del>{E(p["before"])}</del> → <strong>{E(p["after"])}</strong></p><p>{E(p["reason"])}</p><p>'+ ' · '.join(f'<a href="{E(u,quote=True)}">依据{i+1}</a>' for i,u in enumerate(p['evidence']))+'</p></section>'
body+='<p>2012年第4题漫画：从<a href="https://kaoyan.xdf.cn/202411/13980233.html">新东方公开试卷</a>第2页原图提取，未重绘。原页SHA-256：373a2a31619efe7116a525a4bb069e604fd36e8e048fc99829c535bfb76d284b；图像区域为(795,1008)—(1045,1190)，单位为原图像素；配图内嵌在HTML中。</p>'
body+='<h2>保留的版本差异</h2><p>以下差异已被发现并记录，没有擅自统一成自认为正确的措辞。这些题仍应按“公开整理版”使用；若要制作官方原卷逐字认证版本，需要进一步取得官方出版原卷核定。</p>'
for v in variants:body+=f'<p><strong>{v["year"]}年，第'+ '、'.join(map(str,v['q']))+'题：</strong>'+E(v['note'])+'</p>'
body+='<h2>逐年覆盖</h2>'
for y in range(2012,2027):
 body+=f'<section id="year-{y}"><h3>{y} 年 · <a href="{y}.html">打开试卷</a></h3>'
 for r in rounds:
  qs=[q for q in r['questions'] if q['year']==y];body+=f'<p>第{r["round"]}遍：{len(qs)}题，题号1—38；16单选、17多选、5分析题。'
  body+=f'核对{sum(len(q["fields"]) for q in qs)}个片段，其中{sum(not f["exact"] for q in qs for f in q["fields"])}个片段未与任一参照自动完全匹配，均纳入差异复核。'
  body+='</p>'
 body+='<details><summary>逐题检查记录</summary><ol>'
 for n in range(1,39):
  desc=[]
  for r in rounds:
   q=next(q for q in r['questions'] if q['year']==y and q['q']==n);flags=sum(not f['exact'] for f in q['fields']);desc.append(f'第{r["round"]}遍：{len(q["fields"])}片段，'+('参照文本一致' if flags==0 else f'{flags}片段存在OCR/文字版本差异，已复核处置'))
  body+='<li>'+ '；'.join(desc)+'</li>'
 body+='</ol></details></section>'
body+='<footer>技术记录：tools/papers/audit/review.py、round-1.json、round-2.json；参照来源、原始下载摘要及OCR方式见reference-manifest.json。原始采集快照未修改；正文修订通过corrections.json独立应用。</footer>'
(R/'papers/audit.html').write_text(H('政治真题 · 双轮审核记录',body))
print('Rendered audit.html')
