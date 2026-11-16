#!/usr/bin/env python3
"""Check a style-only rebuild against the reviewed Git revision; never edits questions."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--base',default='568f16a71717292636b748e38550667d58ac2352');a=p.parse_args()
rows=[]
for year in range(2012,2027):
 path=f'papers/{year}.html'
 before=BeautifulSoup(subprocess.check_output(['git','show',f'{a.base}:{path}'],cwd=ROOT),'html.parser')
 after=BeautifulSoup((ROOT/path).read_text(),'html.parser')
 old=[str(q) for q in before.select('article')];new=[str(q) for q in after.select('article')]
 assert len(old)==len(new)==38 and old==new,(year,'question DOM changed')
 assert before.header.get_text()==after.header.get_text(),(year,'header changed')
 rows.append({'year':year,'questions':38,'question_dom_sha256':hashlib.sha256(''.join(new).encode()).hexdigest()})
# Sources contain regenerated output-file hashes. Audit wording must remain unchanged.
for name in ['index','audit']:
 before=BeautifulSoup(subprocess.check_output(['git','show',f'{a.base}:papers/{name}.html'],cwd=ROOT),'html.parser')
 after=BeautifulSoup((ROOT/f'papers/{name}.html').read_text(),'html.parser')
 for doc in [before,after]:
  for node in doc.select('style,script'):node.decompose()
 assert before.get_text()==after.get_text(),(name,'text changed')
for path in ['tools/papers/corrections.json','tools/papers/2012-q4-figure.html']:
 assert subprocess.check_output(['git','show',f'{a.base}:{path}'],cwd=ROOT)==(ROOT/path).read_bytes(),path
print(json.dumps({'base':a.base,'reference_style':'dontng/m2@1430fdbfdfbfd0f50d60d0b84cae468e79a2fc3e','question_count':570,'content_unchanged':True,'papers':rows},ensure_ascii=False,indent=2))
