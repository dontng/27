#!/usr/bin/env python3
"""Rebuild whole-page topic PDFs from pinned, hash-checked source parts.
Requires PyMuPDF and numpy. Run from repository root; --limit enables checkpoints.
"""
import argparse,hashlib,json,math,re,urllib.request,urllib.parse
from pathlib import Path
import fitz,numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'src/pdf';WORK=BASE/'_work'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=70);a=ap.parse_args()
 plan=json.loads((WORK/'plan.json').read_text());inputs=json.loads((WORK/'inputs.json').read_text())
 docs=[]
 for src in inputs['parts']:
  p=ROOT/src['path']
  if not p.exists():
   p.parent.mkdir(parents=True,exist_ok=True)
   with urllib.request.urlopen(src['url'],timeout=120) as r:p.write_bytes(r.read())
  if sha(p)!=src['sha256']:raise ValueError('Source checksum mismatch: '+str(p))
  docs.append(fitz.open(p))
 def page(n):return docs[(n-1)//60][(n-1)%60]
 margins={};cache={};results=[]
 for it in plan:
  dst=BASE/it['path'];present=False
  if it['order']<=a.limit:
   dst.parent.mkdir(parents=True,exist_ok=True);out=fitz.open()
   for n in range(it['pdf_start'],it['pdf_end']+1):
    out.insert_pdf(docs[(n-1)//60],from_page=(n-1)%60,to_page=(n-1)%60)
    pg=out[-1]
    if n not in margins:
     p=page(n);pix=p.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(0,0,p.rect.width,45),alpha=False)
     arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
     red=(arr[:,:,0]>180)&(arr[:,:,1]<150)&(arr[:,:,2]<150)
     rows=np.where(red.sum(axis=1)>pix.width*.2)[0]
     margins[n]=max(0,min(20,float(rows[0])/2-.5)) if len(rows) else 20
    h=margins[n]
    if h:pg.draw_rect(fitz.Rect(0,0,pg.rect.width,h),color=None,fill=(1,1,1),overlay=True)
   out.set_metadata({'title':f"{it['number']} {it['title']}",'subject':f"上册；原PDF第{it['pdf_start']}-{it['pdf_end']}页；整页提取；页眉群号视觉遮盖"})
   temp=dst.with_suffix('.tmp.pdf');out.save(temp,garbage=4,deflate=True);out.close();temp.replace(dst)
   reopened=fitz.open(dst)
   assert len(reopened)==it['pdf_end']-it['pdf_start']+1
   for j,n in enumerate(range(it['pdf_start'],it['pdf_end']+1)):
    orig=page(n);pg=reopened[j]
    assert pg.mediabox==orig.mediabox and pg.cropbox==orig.cropbox
    if n not in cache:
     pix=orig.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
     cache[n]=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3).copy()
    pix=pg.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
    arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
    cut=math.ceil(margins[n])+1
    assert np.array_equal(arr[cut:],cache[n][cut:]),(it['path'],n)
    if margins[n]>=2:assert arr[:math.floor(margins[n])-1,1:-2].min()==255
   reopened.close();present=True
  results.append({**it,'generated':present,'pages':it['pdf_end']-it['pdf_start']+1,**({'sha256':sha(dst),'git_blob_sha':hashlib.sha1(b'blob '+str(dst.stat().st_size).encode()+b'\0'+dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size,'verified_page_count_and_boxes':True,'verified_pixels_outside_margin':True} if present else {})})
 (WORK/'validation.json').write_text(json.dumps({'completed':sum(x['generated'] for x in results),'total':70,'checks':results,'watermark_overlay_heights_pt':margins},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'generated':sum(x['generated'] for x in results),'total':70,'minimum_overlay_height':min(margins.values()),'size_bytes':sum(x.get('bytes',0) for x in results)},ensure_ascii=False))
if __name__=='__main__':run()
