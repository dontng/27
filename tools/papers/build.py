#!/usr/bin/env python3
"""Collect public exam questions only; no site answers, analysis, scripts or login content.
Input: https://www.guojiya.cn/exam/neem_politics_{year} (2012..2026).
Requires beautifulsoup4. python tools/papers/build.py --cache /tmp/politics-raw
Each saved exam is a standalone HTML file; audit/source hashes are in sources.html.
Default input: tools/papers/source-cache/*.html (question-only source snapshots).
Original HTTP response hashes are retained in each snapshot comment.
Visual browser QA was attempted but Chromium download was unavailable; no visual approval claimed.
"""
import argparse, hashlib, html, re, urllib.request, json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'papers'
CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f2f1ed;color:#181818;font:17px/1.9 "SimSun","Songti SC","Times New Roman",serif}main{max-width:900px;margin:30px auto;padding:46px 64px;background:white;box-shadow:0 2px 16px #0000000c}h1{font-size:27px;line-height:1.5;text-align:center;margin:12px 0 4px}h2{font-size:21px;margin:36px 0 12px;border-bottom:1px solid #333;padding-bottom:8px}h3{font-size:18px;margin:0 0 14px}.subtitle{text-align:center;letter-spacing:.12em;margin:0 0 22px}.meta{display:flex;justify-content:space-between;border-top:2px solid;border-bottom:1px solid;padding:8px 0;margin:20px 0;font-size:15px}.toolbar,nav{font:14px/1.8 system-ui,sans-serif;display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}.toolbar{margin-bottom:25px}.toolbar a,nav a{color:#404040}button{font:inherit;padding:5px 12px;background:white;border:1px solid #aaa;border-radius:3px;cursor:pointer}p{margin:0 0 10px}.instruction{font-size:15px;margin-bottom:22px}.question{margin:0 0 25px;break-inside:avoid}.stem{white-space:pre-wrap}.options{list-style:none;padding:0 0 0 1.6em;margin:9px 0 0}.options li{padding-left:1.6em;text-indent:-1.6em;margin:3px 0;white-space:pre-wrap}.analysis{margin:30px 0 42px;break-inside:auto}.materials p{text-indent:2em;margin-bottom:12px;white-space:pre-wrap}.materials .material-label{text-indent:0;font-weight:bold}.ask{font-weight:600;white-space:pre-wrap;margin:18px 0}.write-space{display:none;height:240px;background:repeating-linear-gradient(white 0,white 34px,#ccc 35px);margin-top:15px}.with-space .write-space{display:block}.note,footer{font-size:14px;color:#666;line-height:1.8}footer{margin-top:35px;border-top:1px solid #aaa;padding-top:18px}.years{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:28px 0}.years a{display:block;border:1px solid #ccc;padding:18px;color:#222;text-decoration:none}.years small{display:block;color:#666}.source-item{overflow-wrap:anywhere;margin:25px 0}.source-item code{font-size:12px}.qnav{border:1px solid #ddd;padding:12px;margin:20px 0}.qnav a{min-width:20px;text-align:center}.figure{margin:12px auto;text-align:center}.figure img{max-width:100%;background:white}.missing{border:1px dashed #aaa;padding:10px;font-size:14px}a{color:#333}section[id],article[id]{scroll-margin-top:20px}@page{size:A4;margin:18mm 17mm} @media print{body{background:white;font-size:12pt;line-height:1.8}main{max-width:none;margin:0;padding:0;box-shadow:none}.toolbar,.qnav,.screen-only,footer{display:none}h1{font-size:18pt}h2{font-size:14pt;break-after:avoid}h3{break-after:avoid}p{orphans:3;widows:3}.question{margin-bottom:16pt}.analysis{margin-top:22pt}a{text-decoration:none;color:inherit}.meta{font-size:11pt}.instruction{font-size:11pt}}@media(max-width:600px){body{font-size:16px}main{margin:0;padding:25px 20px;box-shadow:none}h1{font-size:23px}.years{grid-template-columns:repeat(2,1fr)}.meta{font-size:13px;gap:15px}.options{padding-left:.6em}}'''
def E(s):return html.escape(s,quote=True)
def H(title,body):return '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(title)+'</title><style>'+CSS+'</style></head><body><main>'+body+'</main></body></html>\n'
def nav(y,years):
 i=years.index(y);return '<nav>'+('' if i==0 else f'<a href="{years[i-1]}.html">← {years[i-1]} 年</a>')+'<a href="index.html">年份目录</a>'+('' if i==len(years)-1 else f'<a href="{years[i+1]}.html">{years[i+1]} 年 →</a>')+'</nav>'
def normalized(s):return re.sub(r'\s+','',s)
def build(cache,years):
 OUT.mkdir(exist_ok=True);records=[]
 for y in years:
  url=f'https://www.guojiya.cn/exam/neem_politics_{y}';p=cache/f'{y}.html'
  if not p.exists():
   cache.mkdir(parents=True,exist_ok=True);p.write_bytes(urllib.request.urlopen(url,timeout=60).read())
  raw=p.read_bytes();s=BeautifulSoup(raw,'html.parser');qs=s.select('[data-question-id]');assert len(qs)==38
  patchfile=ROOT/'tools/papers/corrections.json'
  patches=json.loads(patchfile.read_text()) if patchfile.exists() else []
  for patch in [z for z in patches if z['year']==y]:
   q=qs[patch['question']-1];hits=[t for t in q.find_all(string=True) if patch['before'] in t]
   assert len(hits)==1,(patch['id'],'ambiguous patch')
   hits[0].replace_with(str(hits[0]).replace(patch['before'],patch['after']))
  chunks=[];text_pairs=[];counts=[0,0,0];analysis_scores=[]
  for n,q in enumerate(qs,1):
   assert int(q['data-question-id'].split('_')[-1])==n
   if n in (1,17,34):
    heading={1:'一、单项选择题',17:'二、多项选择题',34:'三、分析题'}[n]
    desc={1:'1—16 题，每题 1 分，共 16 分。每题给出的四个选项中，只有一个选项符合题目要求。',17:'17—33 题，每题 2 分，共 34 分。每题给出的四个选项中，至少有两个选项符合题目要求。多选、少选或错选均不得分。',34:'34—38 题，共 50 分。要求结合所学知识分析材料并回答问题。'}[n]
    chunks.append(f'<h2 id="part-{n}">{heading}</h2><p class="instruction">{desc}</p>')
   if n<=33:
    counts[0 if n<=16 else 1]+=1;stem=q.select_one('p').get_text();opts=[a.select_one('span').get_text() for a in q.select('fieldset label')]
    assert len(opts)==4 and all(o.startswith(c+'.') for o,c in zip(opts,'ABCD'))
    body='<p class="stem">'+E(stem)+'</p>'
    if y==2012 and n==4:
     fig=ROOT/'tools/papers/2012-q4-figure.html'
     body+=fig.read_text() if fig.exists() else '<p class="missing">本题文字来源未附漫画，原图待补；当前保留题干与选项。</p>'
    body+='<ol class="options">'+''.join('<li>'+E(o)+'</li>' for o in opts)+'</ol>'
    chunks.append(f'<article class="question" id="q{n}">{body}</article>');text_pairs.append((stem,opts))
   else:
    counts[2]+=1;title=q.select_one('h3').get_text();score=int(re.search(r'（(\d+) 分）',title)[1]);analysis_scores.append(score)
    paras=[p.get_text() for p in q.select('[aria-label="材料"] p')];ask=q.select_one('[aria-label="作答与参考答案"] > p').get_text()
    assert sum(map(len,paras))>250 and re.search(r'[（(]1[）)]|⑴',ask) and re.search(r'[（(]2[）)]|⑵',ask),(y,n)
    body=f'<h3>{n}. 分析题（{score} 分）</h3><div class="materials">'+''.join('<p'+(' class="material-label"' if re.fullmatch(r'材料[一二三四五12345]?[：:]?|阅读下列材料[：:]?',t) else '')+'>'+E(t)+'</p>' for t in paras)+'</div><p class="ask">'+E(ask)+'</p><div class="write-space" aria-label="答题留白"></div>'
    chunks.append(f'<article class="analysis" id="q{n}">{body}</article>');text_pairs.append((paras,ask))
  assert counts==[16,17,5] and sum(analysis_scores)==50
  toolbar=nav(y,years)+'<div class="toolbar"><button onclick="window.print()">打印试卷</button><button onclick="document.body.classList.toggle(\'with-space\')">显示／隐藏答题留白</button><a href="sources.html#year-'+str(y)+'">来源与校验</a></div>'
  head=f'<header><h1>{y} 年全国硕士研究生招生考试</h1><p class="subtitle">思想政治理论 · 真题整理版</p><div class="meta"><span>科目代码：101</span><span>满分：100 分</span><span>考试时间：180 分钟</span></div></header>'
  qnav='<nav class="qnav" aria-label="题号导航">'+''.join(f'<a href="#q{n}">{n}</a>' for n in range(1,39))+'</nav>'
  foot=f'<footer><p>题目来源：<a href="{url}">过级鸭 · {y} 年考研政治真题</a>。本页收录题干、选项、分析题材料和设问，未收录网站解析。已进行跨来源全文审核；公开整理版本仍存在异文，参见审核记录。</p>'+'<p><a href="audit.html#year-'+str(y)+'">双轮审核记录与版本差异</a></p>'+nav(y,years)+'</footer>'
  target=OUT/f'{y}.html';target.write_text(H(f'{y} 年考研政治真题',toolbar+head+qnav+''.join(chunks)+foot))
  # Independent round-trip: all extracted source strings must survive escaped HTML serialization.
  rendered=BeautifulSoup(target.read_text(),'html.parser');articles=rendered.select('article')
  for q,a in zip(qs,articles):
   strings=([q.select_one('p').get_text()]+[l.select_one('span').get_text() for l in q.select('fieldset label')]) if q.select('fieldset') else [p.get_text() for p in q.select('[aria-label="材料"] p')]+[q.select_one('[aria-label="作答与参考答案"] > p').get_text()]
   for t in strings:assert normalized(t) in normalized(a.get_text()),(y,q['data-question-id'])
  records.append((y,url,hashlib.sha256(raw).hexdigest(),hashlib.sha256(target.read_bytes()).hexdigest(),analysis_scores))
 cards=''.join(f'<a href="{y}.html"><strong>{y} 年</strong><small>单选 16 · 多选 17 · 分析 5</small></a>' for y in years)
 OUT.joinpath('index.html').write_text(H('考研政治历年真题',f'<h1>考研政治历年真题</h1><p class="subtitle">{years[0]}—{years[-1]} · {len(years)} 套 · {38*len(years)} 道题</p><p>按年份整理试卷，保留题干、四个选项、分析题材料与设问。每年一份独立 HTML，下载后可直接在浏览器阅读和打印。</p><div class="years">'+cards+'</div><p class="note">年份按招生考试年度标注，例如 2026 年真题对应 2025 年底举行的考试。2012 年第 4 题漫画已补回。题目已进入双轮全文审核；公开版本异文与修订依据见审核记录。</p><p><a href="sources.html">查看来源与校验记录</a> · <a href="audit.html">查看双轮审核及版本差异</a></p>'))
 items=''.join(f'<section class="source-item" id="year-{y}"><h2>{y} 年</h2><p><a href="{y}.html">试卷</a> · <a href="{u}">文字来源</a></p><p>结构检查：16 单选、17 多选、5 分析题；题号 1—38 连续；132 项选项完整；每道分析题均含材料及至少两个设问。分析题分值：'+ '、'.join(map(str,scores))+'，合计 50 分。</p><p>源网页 SHA-256：<code>'+sh+'</code><br>试卷 HTML SHA-256：<code>'+oh+'</code></p></section>' for y,u,sh,oh,scores in records)
 OUT.joinpath('sources.html').write_text(H('政治真题 · 来源与校验', '<nav><a href="index.html">返回年份目录</a></nav><h1>来源与校验记录</h1><p>采集日期：2026-10-29。保存公开试题内容，不采集网站会员解析或参考答案。生成脚本：tools/papers/build.py；输入为 tools/papers/source-cache 下的逐年 HTML 题目快照（仅保留来源网页的试题容器，原响应摘要见快照注释）；可离线重建或按原网址重新采集。校验涵盖题号、选项数、材料、设问、分值和提取前后文本一致性，不等同于官方原卷认证。另见 <a href="audit.html">双轮全文交叉审核记录</a>。</p><p>2012 年第 4 题漫画已从新东方公开试卷第 2 页提取并内嵌至 HTML。原图来源、提取范围与校验摘要见审核记录。源快照保留最初采集版本，字词修订通过 tools/papers/corrections.json 应用，避免改写原始来源。</p><p>2012 年第 34 题 12 分、第 38 题 8 分：保留源页面分值，并以<a href="https://yz.chsi.com.cn/kyzx/politics/201208/20120827/337816885.html">研招网当年试卷评析</a>交叉核对。2026 年另以<a href="https://static.kaoyan.cn/file/question/2025/12/20/e42f4c7191a84bde7b9688900c790a1a.pdf">中国教育在线考研平台试卷 PDF</a>抽查题型及第 1—9 题，未用参考答案反推题目。</p>'+items))
 print(f'Built {len(years)} papers / {len(years)*38} questions; round-trip checks passed.')
def check():
 years=sorted(int(p.stem) for p in OUT.glob('[0-9][0-9][0-9][0-9].html'))
 for y in years:
  p=OUT/f'{y}.html';s=BeautifulSoup(p.read_text(),'html.parser');assert [int(a['id'][1:]) for a in s.select('article')]==list(range(1,39));assert len(s.select('.options li'))==132
  assert len(s.select('.analysis'))==5
  report=BeautifulSoup((OUT/'sources.html').read_text(),'html.parser').find(id=f'year-{y}')
  assert hashlib.sha256(p.read_bytes()).hexdigest() in report.get_text(),f'{y}: digest mismatch'
  assert not s.select('script[src],link[href],img[src^="http"]')
  patchfile=ROOT/'tools/papers/corrections.json'
  if patchfile.exists():
   for patch in json.loads(patchfile.read_text()):
    if patch['year']==y:
     q=s.find(id='q'+str(patch['question']));assert patch['after'] in q.get_text(),patch['id']
     assert patch['before'] not in q.get_text(),patch['id']
  for a in s.select('a[href]'):
   h=a['href']
   if h.startswith(('http:','https:','#')):continue
   f,_,anchor=h.partition('#');t=OUT/f;assert t.exists(),h
   if anchor:assert BeautifulSoup(t.read_text(),'html.parser').find(id=anchor),h
 print(f'Checked {len(years)} files; all question counts, options and local links passed.')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--cache',type=Path,default=Path(__file__).resolve().parent/'source-cache');a.add_argument('--end',type=int,default=2026);a.add_argument('--check',action='store_true');args=a.parse_args()
 if not args.check:build(args.cache,list(range(2012,args.end+1)))
 check()
