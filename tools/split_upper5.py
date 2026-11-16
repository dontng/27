#!/usr/bin/env python3
"""Build the upper-volume fifth section only; lower-volume drafts are excluded."""
from pathlib import Path
import hashlib,json,math
import fitz,numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'src/pdf';WORK=BASE/'_work/upper5'
def run():
 data=json.loads((WORK/'plan.json').read_text());src=ROOT/data['source']['path'];raw=src.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==data['source']['sha256']
 source=fitz.open(src);checks=[];cache={};heights={}
 for item in data['topics']:
  out=fitz.open();out.insert_pdf(source,from_page=item['pdf_start']-181,to_page=item['pdf_end']-181)
  for j,pg in enumerate(out):
   n=item['pdf_start']+j;original=source[n-181]
   if n not in heights:
    pix=original.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(0,0,original.rect.width,45),alpha=False);a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
    red=(a[:,:,0]>180)&(a[:,:,1]<150)&(a[:,:,2]<150);rows=np.where(red.sum(axis=1)>pix.width*.2)[0]
    heights[n]=max(0,min(20,float(rows[0])/2-.5)) if len(rows) else 20
   if heights[n]:pg.draw_rect(fitz.Rect(0,0,pg.rect.width,heights[n]),color=None,fill=(1,1,1),overlay=True)
  out.set_metadata({'title':item['number']+' '+item['title'],'subject':f"上册第五部分；原PDF第{item['pdf_start']}-{item['pdf_end']}页；整页提取，页边群号视觉遮盖"})
  dst=BASE/item['path'];dst.parent.mkdir(parents=True,exist_ok=True);out.save(dst,garbage=4,deflate=True);out.close();doc=fitz.open(dst)
  assert len(doc)==item['pdf_end']-item['pdf_start']+1
  for j,pg in enumerate(doc):
   n=item['pdf_start']+j;original=source[n-181];assert pg.mediabox==original.mediabox and pg.cropbox==original.cropbox
   if n not in cache:
    pix=original.get_pixmap(alpha=False);cache[n]=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3).copy()
   pix=pg.get_pixmap(alpha=False);a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
   assert np.array_equal(a[math.ceil(heights[n])+1:],cache[n][math.ceil(heights[n])+1:])
  doc.close();b=dst.read_bytes();checks.append({**item,'pages':item['pdf_end']-item['pdf_start']+1,'sha256':hashlib.sha256(b).hexdigest(),'git_blob_sha':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'page_count_boxes_and_unmasked_pixels_verified':True})
 coverage=set(n for x in checks for n in range(x['pdf_start'],x['pdf_end']+1));assert coverage==set(range(201,237))
 (WORK/'validation.json').write_text(json.dumps({'total':18,'generated':18,'unique_source_pages':36,'exported_pages':sum(x['pages'] for x in checks),'lower_volume_used':False,'checks':checks,'overlay_heights_pt':heights},ensure_ascii=False,indent=2)+'\n')
 print('Generated and verified 18 PDFs; lower-volume data excluded.')
if __name__=='__main__':run()
