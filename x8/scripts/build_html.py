#!/usr/bin/env python3
"""Typeset reviewed x8 Markdown with papers' existing exam layout; no OCR rerun."""
from pathlib import Path
import hashlib,html,json,re
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
X8=ROOT/'x8';OUT=X8/'html'
CSS=(X8/'scripts/exam.css').read_text()
JS=(ROOT/'tools/papers/exam.js').read_text()
def E(s):return html.escape(s,quote=True)
def norm(s):return re.sub(r'\s+','',s)
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def clean_blockquote_material(raw):
 lines=[]
 for ln in raw.splitlines():
  s=re.sub(r'^>\s?','',ln).strip()
  if not s:
   lines.append('')
   continue
  s=re.sub(r'^\*\*(材料 \d+)\*\*$',r'### \1',s)
  s=re.sub(r'^——\s*\*([^*]+)\*$',r'\1',s)
  lines.append(s)
 return re.sub(r'\n{3,}','\n\n','\n'.join(lines)).strip()
def parse(paper):
 text=(X8/f'x8-{paper:02}.md').read_text();questions=[]
 for m in re.finditer(r'(?ms)^### 第 (\d+) 题\s*\n(.*?)(?=^### 第 \d+ 题|\n---\s*\n|\Z)',text):
  number=int(m[1]);raw_body=m[2].strip()
  q={'number':number,'page':None}
  if number<=33:
   matches=list(re.finditer(r'(?m)^\*\*([ABCD])\.\*\*\s+',raw_body));assert [a[1] for a in matches]==list('ABCD'),(paper,number)
   stem_raw=raw_body[:matches[0].start()].strip()
   q['stem']=re.sub(r'(?m)  +$','',stem_raw)
   q['options']=[f"{a[1]}. {raw_body[a.end():matches[i+1].start() if i<3 else len(raw_body)].strip()}" for i,a in enumerate(matches)]
   q['body']=q['stem']+'\n\n'+'\n'.join(q['options'])
  else:
   intro=re.match(r'^结合材料回答问题[：:，,；;。]?\s*',raw_body);assert intro,(paper,number)
   q['intro']=intro[0].strip();rest=raw_body[intro.end():].strip()
   ask_hdr=re.search(r'(?m)^\*\*设问：\*\*\s*$',rest);assert ask_hdr,(paper,number)
   mat_raw=rest[:ask_hdr.start()].strip()
   q['material']=clean_blockquote_material(mat_raw)
   asks_raw=rest[ask_hdr.end():].strip()
   asks=list(re.finditer(r'(?m)^\*\*（(\d+)）\*\*\s+',asks_raw));assert len(asks)>=1,(paper,number,len(asks))
   q['asks']=[f"（{a[1]}） {asks_raw[a.end():asks[i+1].start() if i+1<len(asks) else len(asks_raw)].strip()}" for i,a in enumerate(asks)]
   q['body']=q['intro']+'\n\n'+q['material']+'\n\n'+'\n'.join(q['asks'])
  questions.append(q)
 assert [q['number']for q in questions]==list(range(1,39)),(paper,[q['number']for q in questions])
 return questions

def nav(paper):
 return '<nav>'+ (f'<a href="x8-{paper-1:02}.html">← 第{paper-1}套</a>'if paper>1 else '')+'<a href="index.html">八套目录</a>'+ (f'<a href="x8-{paper+1:02}.html">第{paper+1}套 →</a>'if paper<8 else '')+'</nav>'
def shell(title,body,bar=''):
 return '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(title)+'</title><style>'+CSS+'</style></head><body>'+bar+'<main>'+body+'</main><script>'+JS+'</script></body></html>\n'

def paragraphs(text):
 out=[]
 for block in re.split(r'\n\s*\n',text):
  block=block.strip()
  if not block:continue
  label=re.fullmatch(r'### 材料 (\d+)',block)
  if label:out.append('<p class="material-label source-copy">材料 '+label[1]+'</p>');continue
  # A source attribution uses its own right-aligned line, retaining every character.
  parts=re.split(r'(?=摘编自|摘自)',block)
  for part in parts:
   if not part:continue
   klass='source-line source-copy' if re.match(r'摘编自|摘自',part)else 'source-copy'
   out.append('<p class="'+klass+'">'+E(part)+'</p>')
 return ''.join(out)

def section(n):
 title,desc={1:('一、单项选择题','第1—16小题，每小题1分，共16分。下列每小题给出的四个选项中，只有一个选项是最符合题目要求的。'),17:('二、多项选择题','第17—33小题，每小题2分，共34分。下列每小题给出的四个选项中，至少有两个选项是符合题目要求的。多选、少选或错选均不得分。'),34:('三、材料分析题','第34—38小题，每小题10分，共50分。要求结合所学知识分析材料回答问题。')}[n]
 return f'<h2 id="part-{n}">{title}</h2><p class="instruction">{desc}</p>'

def article(q,paper):
 n=q['number'];body=''
 if n<=33:
  blocks=re.split(r'\n\s*\n',q['stem'])
  body='<p class="stem"><strong class="question-number">'+str(n)+'. </strong><span class="source-copy">'+E(blocks[0])+'</span></p>'
  body+=''.join('<p class="statement source-copy">'+E(b)+'</p>' for b in blocks[1:]if b)
  body+='<ol class="options">'+''.join('<li class="source-copy">'+E(o)+'</li>'for o in q['options'])+'</ol>'
 else:
  body=f'<h3>{n}. <span class="source-copy">'+E(q['intro'])+'</span></h3><div class="materials">'+paragraphs(q['material'])+'</div>'
  body+='<div class="ask">'+''.join('<p class="source-copy">'+E(a)+'</p>'for a in q['asks'])+'</div><div class="write-space" aria-label="答题留白"></div>'
 if q["page"]:body+=f'<p class="source-link screen-only"><a href="../PDF/x8-{paper:02}.pdf#page={q["page"]}">原卷第{q["page"]}页</a></p>'
 return f'<article class="{"question" if n<=33 else "analysis"}" id="q{n}">'+body+'</article>'

def canonical(q):return norm(re.sub(r'(?m)^###\s*','',q['body']))
def verify(paper,qs):
 target=OUT/f'x8-{paper:02}.html';s=BeautifulSoup(target.read_text(),'html.parser');articles=s.select('article');assert [a['id']for a in articles]==[f'q{n}'for n in range(1,39)]
 assert len(s.select('.options li'))==132 and len(s.select('.analysis'))==5
 for q,a in zip(qs,articles):
  actual=norm(''.join(t.get_text()for t in a.select('.source-copy')))
  assert actual==canonical(q),(paper,q['number'],'text changed during typesetting')
 assert not s.select('script[src],link[rel="stylesheet"]')
 for a in s.select('a[href]'):
  href=a['href'];f,_,anchor=href.partition('#')
  if f:assert (OUT/f).exists(),href
  if not f and anchor:assert s.find(id=anchor),href
 return {'paper':paper,'source_markdown_sha256':hashlib.sha256((X8/f'x8-{paper:02}.md').read_bytes()).hexdigest(),'html_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'questions':38,'option_labels':132,'analysis_questions':5,'text_round_trip_exact':True,'self_contained':True}

def build():
 base_css=(ROOT/'tools/papers/exam.css').read_text()
 for token in ['--font-serif', '--font-hei']:
  assert re.search(token+r':[^;]+;',CSS)[0]==re.search(token+r':[^;]+;',base_css)[0]
 assert '-webkit-text-stroke' not in CSS
 OUT.mkdir(exist_ok=True);allq={n:parse(n)for n in range(1,9)}
 CN_NUM={1:'一',2:'二',3:'三',4:'四',5:'五',6:'六',7:'七',8:'八'}
 for n,qs in allq.items():
  cn=CN_NUM[n]
  title=f'2027考研政治冲刺8套卷（{cn}）· 思想政治理论'
  bar='<div class="appbar screen-only">'+nav(n)+'<div class="toolbar"><button type="button" onclick="window.print()">打印试卷</button><button type="button" aria-pressed="false" id="space-toggle" onclick="const on=document.body.classList.toggle(\'with-space\');this.setAttribute(\'aria-pressed\',on)">显示／隐藏答题留白</button><a href="../x8-'+f'{n:02}'+'.md">Markdown</a></div></div>'
  body=f'<header><h1>2027考研政治冲刺8套卷（{cn}）</h1><p class="subtitle">思想政治理论</p><div class="meta"><span>科目代码：101</span><span>满分：100 分</span><span>考试时间：180 分钟</span></div></header>'
  body+='<nav class="qnav screen-only" aria-label="题号导航">'+''.join(f'<a href="#q{i}">{i}</a>'for i in range(1,39))+'</nav>'
  for q in qs:
   if q['number']in [1,17,34]:body+=section(q['number'])
   body+=article(q,n)
  body+='<footer><p>根据已完成两轮校对的Markdown排版。题干、选项、材料和设问与Markdown逐字核验一致。</p><p><a href="../PDF/x8-'+f'{n:02}'+'.pdf">查看原扫描卷</a> · <a href="../scripts/audit/round2.md">校对记录</a></p>'+nav(n)+'</footer>'
  (OUT/f'x8-{n:02}.html').write_text(shell(title,body,bar))
 cards=''.join(f'<a href="x8-{n:02}.html"><strong>第{n}套</strong><small>单选16 · 多选17 · 分析5</small></a>' for n in range(1,9))
 (OUT/'index.html').write_text(shell('2027考研政治冲刺8套卷 · 思想政治理论','<header><h1>2027考研政治冲刺8套卷</h1><p class="subtitle">思想政治理论 · 共 8 套</p></header><p>沿用真题考场版式，保留完整题目与材料。选择一套开始作答，也可直接打印。</p><div class="years">'+cards+'</div><p class="screen-only"><a href="../README.md">返回资料目录</a> · <a href="../../papers/html/index.html">历年真题</a></p>'))
 rows=[verify(n,allq[n]) for n in range(1,9)]
 report={'template':'tools/papers/exam.css + tools/papers/exam.js','font_families_unchanged':True,'ink':'#000','body_weight':500,'screen_body_px':16,'print_body_pt':11,'artificial_stroke':False,'papers':rows,'total_questions':304,'total_option_labels':1056,'total_analysis_questions':40}
 (X8/'scripts/html-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('Built 8 standalone HTML papers: 304 questions, 1056 options; exact text round-trip passed.')
if __name__=='__main__':build()
