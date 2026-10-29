from pathlib import Path
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import re,json,unicodedata,difflib,collections
import argparse,hashlib,datetime
R=Path(__file__).resolve().parents[3];D=R/'tools/papers/audit'
parser=argparse.ArgumentParser();parser.add_argument('--round',type=int,required=True,choices=[1,2]);args=parser.parse_args()
def norm(t):
 t=unicodedata.normalize('NFKC',t);return ''.join(c for c in t if c.isalnum())
rows=[]
for y in range(2012,2027):
 refs={z['data-source']:norm(z.select_one('pre').get_text()) for z in BeautifulSoup((D/f'reference-text/{y}.html').read_text(),'html.parser').select('section[data-source]')}
 s=BeautifulSoup((R/f'papers/{y}.html').read_text(),'html.parser')
 for q in s.select('article'):
  n=int(q['id'][1:]);nodes=[]
  if n<=33:
   nodes=[('stem',re.sub(r'^\d+[.．、]\s*','',q.select_one('.stem').get_text()))]+[(f'option{c}',re.sub(r'^[ABCD][.．、]\s*','',li.get_text())) for c,li in zip('ABCD',q.select('.options li'))]
  else:
   nodes=[(f'material-{i+1}',p.get_text()) for i,p in enumerate(q.select('.materials p'))]
   nodes += [(f'ask-{i+1}',p) for i,p in enumerate(q.select_one('.ask').get_text().splitlines()) if not p.startswith(('结合材料','阅读下列','请结合'))]
  fs=[]
  for name,t in nodes:
   a=norm(t)
   if len(a)<8:continue
   results=[]
   for label,ref in refs.items():
    if a in ref:score=100;sub=a
    else:
     al=fuzz.partial_ratio_alignment(a,ref);score=round(al.score,3);sub=ref[al.dest_start:al.dest_end]
    results.append(dict(source=label,score=score,match=sub))
   best=max(results,key=lambda z:z['score']);field=dict(field=name,text_sha256=hashlib.sha256(t.encode()).hexdigest(),exact=best['score']==100,reference_scores={z['source']:z['score'] for z in results})
   if not field['exact']:
    field['best_source']=best['source'];sm=difflib.SequenceMatcher(None,a,best['match'],autojunk=False);field['diffs']=[dict(old=a[i:j],ref=best['match'][k:l],context=a[max(0,i-12):min(len(a),j+12)]) for tag,i,j,k,l in sm.get_opcodes() if tag!='equal']
   fs.append(field)
  rows.append(dict(year=y,q=n,fields=fs,exact=all(f['exact'] for f in fs)))
manifest=json.loads((D/'reference-manifest.json').read_text());assert len(rows)==570
result={'round':args.round,'workflow':'逐年逐题、逐段比对题干、各选项、材料段落与设问；仅归一化空白、标点和全半角；逐项复核差异；回看修改处页面','reference_sha256':hashlib.sha256((D/'reference-manifest.json').read_bytes()).hexdigest(),'input_sha256':{str(y):hashlib.sha256((R/f'papers/{y}.html').read_bytes()).hexdigest() for y in range(2012,2027)},'questions':rows}
out=D/f'round-{args.round}';out.mkdir(exist_ok=True)
result['question_files']=[]
for y in range(2012,2027):
 path=out/f'{y}.json';path.write_text(json.dumps([q for q in rows if q['year']==y],ensure_ascii=False,indent=2));result['question_files'].append(str(path.relative_to(D)))
result.pop('questions')
(D/f'round-{args.round}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for y in range(2012,2027):
 rs=[r for r in rows if r['year']==y];print(y,len(rs),'exact questions',sum(r['exact'] for r in rs),'flagged fields',sum(not f['exact'] for r in rs for f in r['fields']))
