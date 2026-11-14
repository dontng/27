#!/usr/bin/env python3
"""Check reviewed Markdown structure, PDF page links and content hashes."""
from pathlib import Path
import hashlib,json,re
import fitz
X8=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 rows=[]
 corrections=json.loads((X8/'scripts/audit/reviewed-fixes.json').read_text())
 round2=json.loads((X8/'scripts/audit/round2-review.json').read_text())
 first_round_count=len(corrections)
 corrections.extend(round2['corrections'])
 assert round2['completed_papers']==list(range(1,9))
 for n in range(1,9):
  md=X8/f'xiao8-{n:02}.md';pdf=X8/f'PDF/xiao8-{n:02}.pdf';text=md.read_text();pages=len(fitz.open(pdf))
  numbers=[int(x) for x in re.findall(r'^## 第 (\d+) 题$',text,re.M)]
  assert numbers==list(range(1,39)),(n,numbers)
  chunks=re.split(r'^## 第 \d+ 题\n',text,flags=re.M)[1:]
  for q,chunk in enumerate(chunks,1):
   for opening,closing in [('“','”'),('‘','’'),('《','》')]:
    assert chunk.count(opening)==chunk.count(closing),(n,q,opening,closing)
   if q<=33:assert re.findall(r'^([ABCD])\. ',chunk,re.M)==list('ABCD'),(n,q)
   links=re.findall(r'\[原卷 PDF 第 (\d+) 页\]\(PDF/(xiao8-\d+.pdf)#page=(\d+)\)',chunk)
   assert len(links)==1,(n,q,links)
   p,name,anchor=links[0];assert name==pdf.name and p==anchor and 1<=int(p)<=pages,(n,q,links)
  assert 'OCR初稿' not in text,n
  rows.append({'paper':n,'pages':pages,'questions':len(numbers),'option_labels':132,'question_page_links':38,'correction_records':sum(x['paper']==n for x in corrections),'pdf_sha256':sha(pdf),'markdown_sha256':sha(md)})
 return {'status':'passed','scope':'structure and replay output; not a guarantee of zero OCR errors','total_pages':sum(x['pages'] for x in rows),'total_questions':304,'total_option_labels':1056,'correction_records':len(corrections),'first_round_records':first_round_count,'second_round_records':len(round2['corrections']),'question_quote_pairs_balanced':True,'papers':rows}
if __name__=='__main__':
 result=verify();(Path(__file__).with_name('verification.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
