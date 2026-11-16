#!/usr/bin/env python3
"""Verify exported PDFs against unchanged HTML; uses Poppler and BeautifulSoup."""
from pathlib import Path
import hashlib,json,subprocess,unicodedata,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'tools/papers/pdf-manifest.json').read_text());results=[]
for item in manifest['papers']:
 y=item['year'];pdf=ROOT/item['pdf'];html=ROOT/item['html']
 assert sha(pdf)==item['pdf_sha256'] and sha(html)==item['html_sha256'],y
 xml=subprocess.check_output(['pdftotext','-bbox-layout',str(pdf),'-']);tree=ET.fromstring(xml);ns={'x':'http://www.w3.org/1999/xhtml'}
 pages=tree.findall('.//x:page',ns);assert pages,y
 texts=[];outside=[]
 for n,page in enumerate(pages,1):
  width,height=float(page.attrib['width']),float(page.attrib['height']);assert abs(width-595.28)<1 and abs(height-841.89)<1,(y,n,'not A4')
  words=page.findall('.//x:word',ns);assert len(words)>5,(y,n,'blank page')
  for w in words:
   x0,y0,x1,y1=[float(w.attrib[a]) for a in ['xMin','yMin','xMax','yMax']]
   if y0<800 and (x0<40 or x1>width-40 or y0<20 or y1>height-25):outside.append((n,w.text))
   if y0<800:texts.append(w.text or '')
 assert not outside,(y,outside)
 pdftext=norm(''.join(texts));soup=BeautifulSoup(html.read_text(),'html.parser');missing=[];count=0
 for q in soup.select('article'):
  for el in q.select('.stem,.options li,.materials p,.ask'):
   # Compare individual paragraphs/subquestions; ignore only whitespace/punctuation normalization.
   for text in el.get_text().splitlines():
    fragment=norm(text)
    if not fragment:continue
    count+=1
    if fragment not in pdftext:missing.append({'q':q['id'],'text':text})
 assert not missing,(y,'missing PDF text',missing)
 images=subprocess.check_output(['pdfimages','-list',str(pdf)],text=True).splitlines()
 if y==2012:assert len(images)>2,'2012 cartoon missing'
 row={'year':y,'pages':len(pages),'a4':True,'blank_pages':0,'out_of_bounds_words':0,'text_fragments_checked':count,'missing_fragments':0,'html_unchanged':True};results.append(row);print(y,len(pages),'pages;',count,'text fragments matched',flush=True)
(ROOT/'tools/papers/pdf-validation.json').write_text(json.dumps({'checks':results,'total_papers':len(results),'total_pages':sum(r['pages'] for r in results)},ensure_ascii=False,indent=2)+'\n')
