from pathlib import Path
from bs4 import BeautifulSoup
import unicodedata,json,re,hashlib
R=Path(__file__).resolve().parents[3]; D=R/'tools/papers/audit'
def norm(t):return ''.join(c for c in unicodedata.normalize('NFKC',t) if c.isalnum())
for run in [1,2]:
 rows=[]
 for y in range(2012,2027):
  refs={s['data-source']:norm(s.pre.get_text()) for s in BeautifulSoup((D/f'reference-text/{y}.html').read_text(),'html.parser').select('section[data-source]')}
  s=BeautifulSoup((R/f'papers/{y}.html').read_text(),'html.parser')
  for q in s.select('article'):
   for i,p in enumerate(q.select('.stem,.options li,.materials p,.ask')):
    t=re.sub(r'^\d+[.．、]\s*|^[ABCD][.．、]\s*','',p.get_text())
    if p.get('class')==['ask']:continue
    a=norm(t)
    if len(a)>=8:continue
    matches=[k for k,v in refs.items() if a in v]
    rows.append({'year':y,'q':q['id'],'text':t,'reference_matches':matches})
  for q in s.select('.analysis'):
   for line in q.select_one('.ask').get_text().splitlines():
    if line.startswith(('结合材料','阅读下列','请结合')):rows.append({'year':y,'q':q['id'],'text':line,'boilerplate':True})
 (D/f'round-{run}-short-fields.json').write_text(json.dumps({'round':run,'workflow':'逐年逐题补充核对少于8字的短选项、标题、出处及作答提示；相同输入独立执行两次','fields':rows},ensure_ascii=False,indent=2))
 print(run,len(rows),'unmatched',sum(not z.get('reference_matches') and not z.get('boilerplate') for z in rows))
 if run==2:
  for z in rows:
   if not z.get('reference_matches') and not z.get('boilerplate'):print(z)
