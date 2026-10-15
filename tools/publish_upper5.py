#!/usr/bin/env python3
"""Publish the verified upper-volume fifth section in three resumable batches."""
import base64,fcntl,hashlib,json,re,subprocess,sys,time
from pathlib import Path
from work_hosted_apps import HostedAppsClient
from publish_topic_pdfs import unpack
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'src/pdf';WORK=BASE/'_work/upper5';RUN=ROOT/'.upper5-publish';REPO='dontng/27';RUN.mkdir(exist_ok=True)
def write(p,obj):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def log(s):
 line=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+s;print(line,flush=True)
 with (RUN/'execution.log').open('a') as f:f.write(line+'\n')
def main():
 lock=(RUN/'lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 client=HostedAppsClient();connector=None;cursor=None
 for _ in range(100):
  r=client._rpc('tools/list',{'cursor':cursor} if cursor else {})
  for t in r.get('tools',[]):
   m=t.get('_meta',{})
   if m.get('connector_name')=='GitHub' and t.get('name','').endswith('create_blob'):connector=m['connector_id']
  cursor=r.get('nextCursor',r.get('next_cursor'))
  if connector or not cursor:break
 if not connector:raise RuntimeError('GitHub connection unavailable')
 def call(name,args):
  for attempt in range(4):
   try:return unpack(client.call_tool(connector,name,args))
   except Exception:
    if attempt==3:raise
    log('Retry '+name);time.sleep(min(2**attempt,8))
 def fetch(path):return call('fetch',{'url':'https://api.github.com/repos/'+REPO+'/'+path})
 def read(path):return call('fetch_file',{'repository_full_name':REPO,'path':path})['content']
 cache_path=RUN/'blob-cache.json';cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
 plan=json.loads((WORK/'plan.json').read_text())['topics'];v=json.loads((WORK/'validation.json').read_text());assert len(v['checks'])==18
 # Preserve all existing topic files; do not read or publish lower-volume data.
 tree=fetch('git/trees/main?recursive=1');prior={x['path']:x['sha'] for x in tree['tree'] if x['path'].startswith('src/pdf/') and x['path'].endswith('.pdf') and not x['path'].startswith('src/pdf/05-')}
 assert len(prior)==70
 prior_path=WORK/'prior-70.json'
 if not prior_path.exists():write(prior_path,prior)
 else:prior=json.loads(prior_path.read_text())
 try:state=json.loads(read('src/pdf/_work/upper5/progress.json'));done=state['published']
 except Exception:state={'published':0,'total':18,'batches':[],'lower_volume_used':False};done=0
 while done<18:
  end=min(done+6,18)
  # Fetch shared documents afresh to preserve other work.
  index=read('src/pdf/README.md');index=re.sub(r'\n<!-- upper5:start -->.*?<!-- upper5:end -->\n?', '\n',index,flags=re.S)
  index=index.replace('第五部分不在本次范围内。','第五部分见下方新增目录。')
  lines=['','<!-- upper5:start -->','## 05-思想道德与法治','','上册第五部分共18专题，本提交包含 '+str(end)+'/18；完成后上册合计88份。下册现有文件已由用户确认是错误半成品，本任务不使用、不删除；第六部分等待正确资料。','']
  for x in plan[:end]:lines.append(f"- [{Path(x['path']).name}]({x['path']})：书内{x['book_start']}—{x['book_end']}页，共{x['pdf_end']-x['pdf_start']+1}页。")
  lines+=['','[页码与来源记录](_work/upper5/plan.json) · [校验记录](_work/upper5/validation.json) · [批次记录](_work/upper5/progress.json)','<!-- upper5:end -->','']
  (BASE/'README.md').write_text(index.rstrip()+'\n'+'\n'.join(lines))
  directory=read('src/肖秀荣背诵手册-上册目录.md');ls=directory.splitlines();active=False;n=0
  for i,l in enumerate(ls):
   if l.startswith('## 第五部分'):active=True
   if active and l.startswith('- [ ] 专题'):
    n+=1
    if n<=end and '[专题PDF]' not in l:ls[i]=l+' · [专题PDF](pdf/'+plan[n-1]['path']+')'
  (ROOT/'src/肖秀荣背诵手册-上册目录.md').write_text('\n'.join(ls)+'\n')
  rule=read('AGENTS.md')
  marker='## 资料有效性（2026-10-15用户纠正）'
  if marker not in rule:
   rule+='\n'+marker+'\n\n- references/xiaoxiurong 中现有下册OCR和PDF是用户确认的错误半成品，正确下册尚未上传。不得将这些文件当作有效来源；不擅自删除或替换，等待用户提供正确版本。\n- 当前补充任务仅处理有效上册第五部分18专题；第六部分不自行映射到错误下册，待正确资料明确后再处理。\n'
  (ROOT/'AGENTS.md').write_text(rule)
  state['published']=end;write(WORK/'progress.json',state)
  paths=['AGENTS.md','src/pdf/README.md','src/肖秀荣背诵手册-上册目录.md','tools/split_upper5.py','tools/publish_upper5.py']
  paths += [str(p.relative_to(ROOT)) for p in sorted(WORK.rglob('*')) if p.is_file()]
  paths += ['src/pdf/'+x['path'] for x in plan[done:end]]
  entries=[]
  for rel in dict.fromkeys(paths):
   b=(ROOT/rel).read_bytes();sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
   if sha not in cache:
    got=call('create_blob',{'repository_full_name':REPO,'encoding':'base64','content':base64.b64encode(b).decode()});assert got['sha']==sha;cache[sha]=True;write(cache_path,cache)
   entries.append({'path':rel,'mode':'100644','type':'blob','sha':sha});log('Ready '+rel)
  msg=f'pdf: 补齐上册第五部分第{done+1}—{end}专题\n\nImplemented:\n- 整页拆分思想道德与法治，保留共用页并遮盖页眉群号\n- 更新目录链接、来源边界、校验及批次记录\n- 明确现有下册为无效半成品，不纳入本次处理\n\nWhy:\n- 补齐有效上册并避免误用错误下册\n\nVerified:\n- 18份已核对原书边界、页数、页面尺寸及遮盖区外像素\n- 本批上传blob SHA逐一匹配本地文件\n\nGenerated with Codex\nCo-Authored-By: Codex <noreply@openai.com>'
  for attempt in range(4):
   head=fetch('git/ref/heads/main')['object']['sha'];parent=fetch('git/commits/'+head)
   t=call('create_tree',{'repository_full_name':REPO,'base_tree_sha':parent['tree']['sha'],'tree_elements':entries});c=call('create_commit',{'repository_full_name':REPO,'parent_sha':head,'tree_sha':t['sha'],'message':msg})
   try:call('update_ref',{'repository_full_name':REPO,'branch_name':'main','expected_sha':head,'force':False,'sha':c['sha']});break
   except Exception:
    if fetch('git/ref/heads/main')['object']['sha']==c['sha']:break
    if attempt==3:raise
  remote=fetch('git/trees/'+c['sha']+'?recursive=1');lookup={x['path']:x.get('sha') for x in remote['tree']};assert all(lookup.get(x['path'])==x['sha'] for x in entries);assert all(lookup.get(p)==sha for p,sha in prior.items())
  receipt={'topics':[done+1,end],'commit':c['sha'],'verified_remote':True};state['batches'].append(receipt);write(WORK/'progress.json',state);write(RUN/'state.json',{'published':end,'total':18,'phase':'running','last_commit':c['sha']});log(f'PUBLISHED {end}/18 '+c['sha']);done=end
 # Final audit persists the final batch receipt, not just the earlier ones.
 remote=fetch('git/trees/main?recursive=1');lookup={x['path']:x.get('sha') for x in remote['tree']}
 assert all(lookup.get('src/pdf/'+x['path'])==x['git_blob_sha'] for x in v['checks']);assert all(lookup.get(p)==sha for p,sha in prior.items())
 write(WORK/'publication.json',{'published':18,'previous_70_unchanged':True,'all_18_remote_hashes_verified':True,'lower_volume_used':False,'batches':state['batches']})
 entries=[]
 for rel in ['src/pdf/_work/upper5/progress.json','src/pdf/_work/upper5/publication.json']:
  b=(ROOT/rel).read_bytes();blob=call('create_blob',{'repository_full_name':REPO,'encoding':'base64','content':base64.b64encode(b).decode()});entries.append({'path':rel,'mode':'100644','type':'blob','sha':blob['sha']})
 head=fetch('git/ref/heads/main')['object']['sha'];parent=fetch('git/commits/'+head);t=call('create_tree',{'repository_full_name':REPO,'base_tree_sha':parent['tree']['sha'],'tree_elements':entries})
 msg='pdf: 归档上册第五部分18专题远端校验\n\nImplemented:\n- 保存全部三批提交和最终校验结果\n\nWhy:\n- 完成88份上册专题的可追溯交付\n\nVerified:\n- 新增18份远端SHA一致，原70份SHA保持一致\n- 未使用错误下册\n\nGenerated with Codex\nCo-Authored-By: Codex <noreply@openai.com>'
 c=call('create_commit',{'repository_full_name':REPO,'parent_sha':head,'tree_sha':t['sha'],'message':msg});call('update_ref',{'repository_full_name':REPO,'branch_name':'main','expected_sha':head,'force':False,'sha':c['sha']});assert fetch('git/ref/heads/main')['object']['sha']==c['sha']
 write(RUN/'state.json',{'phase':'complete','published':18,'total':18,'last_commit':c['sha']});log('COMPLETE '+c['sha'])
if __name__=='__main__':
 try:main()
 except Exception as e:
  log('STOPPED '+type(e).__name__);raise
