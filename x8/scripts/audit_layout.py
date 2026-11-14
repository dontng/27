#!/usr/bin/env python3
"""Audit HTML print grouping and simulate four screen widths with an offline renderer.
This does not drive Safari/Chrome or certify interactive browser behavior.
"""
from pathlib import Path
import sys,re,json,logging,argparse,subprocess,hashlib
from bs4 import BeautifulSoup
from weasyprint import HTML
import tinycss2
from export_pdf import option_widths
ROOT=Path(__file__).resolve().parents[2]
BASE=None
OUT=ROOT/'x8/scripts/_work/layout-audit'
logging.getLogger('weasyprint').setLevel(logging.ERROR)
def source_html(path):
 if BASE:return subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT).decode()
 return path.read_text()
def print_audit(n):
 path=ROOT/f'x8/html/xiao8-{n:02}.html';s=BeautifulSoup(source_html(path),'html.parser');widths=option_widths(s);w=176*96/25.4-2*11*96/72;gap=6*96/25.4
 for i,g in enumerate(s.select('.options')):
  need=max(widths[4*i:4*i+4])+6;cols=next(c for c in[4,2,1]if c==1 or need<=(w-(c-1)*gap)/c);g['style']=f'grid-template-columns:repeat({cols},minmax(0,1fr))'
 meta={};groups=[]
 for q in s.select('article'):
  for i,el in enumerate(q.select('h3,.source-copy')):
   key=f'{q["id"]}-f{i}';el['data-audit-node']=key;meta[key]={'q':q['id'],'kind':' '.join(el.get('class',[]))or el.name,'text':el.get_text()[:60]}
  ask=q.select('.ask p');source=q.select('.materials p');opts=q.select('.options li');head=q.select('h3')
  if ask:groups.append(('ask',[el['data-audit-node']for el in ask]))
  if opts:groups.append(('options',[el['data-audit-node']for el in opts]))
  for i,p in enumerate(source):
   if 'source-line'in p.get('class',[])and i:groups.append(('source-attribution',[source[i-1]['data-audit-node'],p['data-audit-node']]))
   if 'material-label'in p.get('class',[])and i+1<len(source):groups.append(('material-heading',[p['data-audit-node'],source[i+1]['data-audit-node']]))
 doc=HTML(string=str(s),base_url=path.as_uri()).render();boxes={}
 for page,p in enumerate(doc.pages,1):
  for b in p._page_box.descendants():
   if type(b).__name__=='TextBox'and b.element is not None:
    key=b.element.get('data-audit-node')
    if key:boxes.setdefault(key,[]).append({'page':page,'top':round(b.position_y,2),'bottom':round(b.position_y+b.height,2)})
 issues=[]
 for kind,keys in groups:
  if not all(k in boxes for k in keys):continue
  if kind=='options':
   pages=[sorted(set(b['page']for b in boxes[k]))for k in keys]
   if len(set(p for v in pages for p in v))>1:issues.append({'type':kind,'question':meta[keys[0]]['q'],'pages':pages})
  else:
   for a,b in zip(keys,keys[1:]):
    if boxes[a][-1]['page']!=boxes[b][0]['page']:issues.append({'type':kind,'question':meta[a]['q'],'from_page':boxes[a][-1]['page'],'to_page':boxes[b][0]['page'],'text':meta[b]['text']})
 result={'paper':n,'pages':len(doc.pages),'issues':issues}
 print(json.dumps(result,ensure_ascii=False),flush=True);(OUT/f'print-{n:02}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))

def screen_css(css,width):
 def rules(items):
  result=[]
  for rule in items:
   if rule.type=='at-rule':
    if rule.lower_at_keyword=='media':
     media=tinycss2.serialize(rule.prelude)
     if 'print'in media:continue
     tests=re.findall(r'\((max|min)-width:\s*([0-9.]+)px\)',media)
     if all(width<=float(v) if k=='max' else width>=float(v)for k,v in tests):result.append(rules(tinycss2.parse_rule_list(rule.content)))
    elif rule.lower_at_keyword!='page':result.append(tinycss2.serialize([rule]))
   else:result.append(tinycss2.serialize([rule]))
  return '\n'.join(result)
 return rules(tinycss2.parse_stylesheet(css,skip_comments=True,skip_whitespace=True))+f'\n@page{{size:{width}px 100000px;margin:0}}'

def viewport_audit(n):
 path=ROOT/f'x8/html/xiao8-{n:02}.html';source=BeautifulSoup(source_html(path),'html.parser');widths=option_widths(source,'16px');records=[]
 for width in [320,390,768,1120]:
  s=BeautifulSoup(str(source),'html.parser');s.style.string=screen_css(s.style.get_text(),width)
  for i,g in enumerate(s.select('.options')):g['data-audit-group']=str(i)
  doc=HTML(string=str(s),base_url=path.as_uri(),media_type='screen').render();groups={}
  for p in doc.pages:
   for box in p._page_box.descendants():
    if type(box).__name__=='GridBox'and box.element is not None and box.element.get('data-audit-group')is not None:groups[int(box.element.get('data-audit-group'))]=box
  assert len(groups)==33,(n,width,len(groups))
  for i,g in enumerate(s.select('.options')):
   box=groups[i];gap=24;need=max(widths[4*i:4*i+4])+6;cols=next(c for c in[4,2,1]if c==1 or need<=(box.width-(c-1)*gap)/c);g['style']=f'grid-template-columns:repeat({cols},minmax(0,1fr))'
  doc=HTML(string=str(s),base_url=path.as_uri(),media_type='screen').render();outside=[];overlaps=[];seen=[]
  for p in doc.pages:
   for box in p._page_box.descendants():
    if type(box).__name__=='TextBox'and box.text.strip():
     if box.position_x<-.5 or box.position_x+box.width>width+.5:outside.append({'text':box.text[:45],'left':round(box.position_x,2),'right':round(box.position_x+box.width,2)})
     seen.append(box.text)
  record={'paper':n,'viewport_px':width,'offline_simulation':True,'horizontal_overflow_text_boxes':outside,'question_count':len(s.select('article')),'option_count':len(s.select('.options li'))}
  records.append(record);print(n,width,'overflow',len(outside),flush=True)
  if n in[1,8]and width in[390,1120]:
   (OUT/f'screen-{n:02}-{width}.pdf').write_bytes(doc.write_pdf())
 (OUT/f'viewports-{n:02}.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--base',help='Read a historical HTML revision without changing working files')
 parser.add_argument('--print-only',action='store_true')
 parser.add_argument('--screen-only',action='store_true')
 args=parser.parse_args();BASE=args.base
 if BASE:OUT=OUT/BASE[:12]
 OUT.mkdir(parents=True,exist_ok=True)
 for n in range(1,9):
  if not args.screen_only:print_audit(n)
  if not args.print_only:viewport_audit(n)
 print_checks=[json.loads(p.read_text())for p in sorted(OUT.glob('print-*.json'))]
 screen_checks=[x for p in sorted(OUT.glob('viewports-*.json'))for x in json.loads(p.read_text())]
 summary={'method':'offline WeasyPrint layout and simulated screen widths; not browser interaction testing','base_revision':BASE,'print_checks':print_checks,'screen_checks':screen_checks,'print_issue_count':sum(len(r['issues'])for r in print_checks),'screen_overflow_text_boxes':sum(len(r['horizontal_overflow_text_boxes'])for r in screen_checks)}
 name='html-layout-baseline.json'if BASE else 'html-layout-audit.json'
 (ROOT/'x8/scripts'/name).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print('Report',name,flush=True)
