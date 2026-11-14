#!/usr/bin/env python3
"""Export the current standalone HTML beside itself, without altering source text.
WeasyPrint renders the existing print CSS. Since it does not execute JS, option
columns use the same 4/2/1 fit rule as tools/papers/exam.js, with widths measured
by the renderer using the selected print font, rather than character counts.
"""
from pathlib import Path
import argparse,hashlib,html,json,logging,re,unicodedata
from bs4 import BeautifulSoup
from weasyprint import HTML,CSS,__version__
import fitz
ROOT=Path(__file__).resolve().parents[2];X8=ROOT/'x8';FOLDER=X8/'html'
logging.getLogger('weasyprint').setLevel(logging.ERROR)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s)if c.isalnum())
def option_widths(soup):
 options=[li.get_text()for li in soup.select('.options li')]
 font_vars='\n'.join(re.findall(r'--font-(?:serif|hei):[^;]+;',soup.style.get_text()))
 css=':root{'+font_vars+'} @page{size:4000px 100000px;margin:0}body{margin:0}p{margin:0;white-space:pre;font:500 11pt/1.65 var(--font-serif)}'
 source='<html lang="zh-CN"><meta charset="utf-8"><style>'+css+'</style><body>'+''.join(f'<p id="m{i}">'+html.escape(text)+'</p>'for i,text in enumerate(options))+'</body></html>'
 doc=HTML(string=source).render();widths={}
 for page in doc.pages:
  for box in page._page_box.descendants():
   if type(box).__name__=='TextBox'and box.element is not None:
    ident=box.element.get('id','')
    if ident.startswith('m'):widths[int(ident[1:])]=widths.get(int(ident[1:]),0)+box.width
 assert len(widths)==132,len(widths)
 return [widths[i]for i in range(132)]
def export(paper):
 src=FOLDER/f'xiao8-{paper:02}.html';target=src.with_suffix('.pdf');before=sha(src);soup=BeautifulSoup(src.read_text(),'html.parser');widths=option_widths(soup);counts={1:0,2:0,4:0}
 width=176*96/25.4-2*(11*96/72);gap=6*96/25.4
 for i,group in enumerate(soup.select('.options')):
  required=max(widths[4*i:4*i+4])+6
  columns=next(n for n in [4,2,1]if n==1 or required<=(width-(n-1)*gap)/n)
  group['style']=f'grid-template-columns:repeat({columns},minmax(0,1fr))'
  counts[columns]+=1
 # Fonts, page margins, body proportions and print rules are read from the HTML.
 HTML(string=str(soup),base_url=src.as_uri()).write_pdf(str(target))
 assert sha(src)==before,'Export changed the source HTML'
 doc=fitz.open(target);pdf_text='';outside=[];page_stats=[]
 for i,page in enumerate(doc,1):
  assert abs(page.rect.width-595.28)<1 and abs(page.rect.height-841.89)<1,(paper,i,'not A4')
  blocks=page.get_text('dict')['blocks'];lines=[];bottom=0
  for b in blocks:
   for line in b.get('lines',[]):
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox'];text=span['text']
     if y0>800:continue # CSS running page-number footer
     if text.strip()and(x0<40 or x1>page.rect.width-40 or y0<20 or y1>800):outside.append((i,text))
     lines.append(text);bottom=max(bottom,y1)
  text=''.join(lines);assert len(norm(text))>20,(paper,i,'blank page');pdf_text+=text
  page_stats.append({'page':i,'body_bottom_pt':round(bottom,2),'body_characters':len(norm(text))})
 assert not outside,(paper,'out-of-bounds text',outside)
 pdf_text=norm(pdf_text);fragments=0
 for q in soup.select('article'):
  for el in q.select('.source-copy'):
   needle=norm(el.get_text());assert needle in pdf_text,(paper,q['id'],'missing text',needle[:50]);fragments+=1
 row={'paper':paper,'html':str(src.relative_to(ROOT)),'pdf':str(target.relative_to(ROOT)),'html_sha256':before,'pdf_sha256':sha(target),'pages':len(doc),'a4':True,'html_unchanged':True,'text_fragments_checked':fragments,'missing_fragments':0,'out_of_bounds_spans':0,'option_columns':counts,'page_stats':page_stats}
 print(json.dumps({k:v for k,v in row.items()if k not in ['page_stats','html_sha256','pdf_sha256']},ensure_ascii=False),flush=True)
 return row
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('papers',type=int,nargs='*',default=list(range(1,9)));args=a.parse_args()
 p=X8/'scripts/pdf-export.json';old=json.loads(p.read_text())if p.exists()else {};rows={r['paper']:r for r in old.get('papers',[])}
 for n in args.papers:assert 1<=n<=8;rows[n]=export(n)
 result={'engine':'WeasyPrint','engine_version':__version__,'source':'current x8/html HTML and its embedded print CSS','option_fitting':'same 4/2/1 rule as papers exam.js; widths measured in print font by renderer','browser_export':False,'papers':[rows[n]for n in sorted(rows)]}
 p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
