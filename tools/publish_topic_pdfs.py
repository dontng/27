#!/usr/bin/env python3
"""Resumable batch publication through the connected GitHub app in ChatGPT Work.
No credential is stored in this repository. Requires the Work app runtime.
"""
import base64,fcntl,hashlib,json,os,subprocess,sys,time,traceback
from pathlib import Path
from work_hosted_apps import HostedAppsClient
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'src/pdf/_work';REPO='dontng/27'
RUNTIME=ROOT/'.topic-publish';RUNTIME.mkdir(exist_ok=True)
def write(p,value):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def log(message):
 text=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+message
 print(text,flush=True)
 with (RUNTIME/'worker.log').open('a') as f:f.write(text+'\n')
def unpack(r):
 if not isinstance(r,dict):return r
 if r.get('isError'):raise RuntimeError('GitHub tool returned an error')
 if 'encoding' in r:return r
 if r.get('structuredContent') is not None:return unpack(r['structuredContent'])
 content=r.get('content')
 if isinstance(content,str):
  try:return unpack(json.loads(content))
  except json.JSONDecodeError:return r
 if isinstance(content,list):
  for c in content:
   if c.get('type')=='text':
    try:return unpack(json.loads(c['text']))
    except json.JSONDecodeError:pass
 return r
def main():
 lock=(RUNTIME/'worker.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 client=HostedAppsClient();cursor=None;connector=None
 for _ in range(100):
  r=client._rpc('tools/list',{'cursor':cursor} if cursor else {})
  for t in r.get('tools',[]):
   m=t.get('_meta',{})
   if m.get('connector_name')=='GitHub' and t.get('name','').endswith('create_blob'):connector=m['connector_id']
  cursor=r.get('nextCursor',r.get('next_cursor'))
  if connector or not cursor:break
 if not connector:raise RuntimeError('Connected GitHub app unavailable')
 def call(name,args):
  for attempt in range(4):
   try:return unpack(client.call_tool(connector,name,args))
   except Exception:
    if attempt==3:raise
    log('Retry '+name+' after transport/tool error');time.sleep(min(2**attempt,8))
 def fetch(suffix):return call('fetch',{'url':'https://api.github.com/repos/'+REPO+'/'+suffix})
 cache_path=RUNTIME/'blob-cache.json'
 if not cache_path.exists():
  seed=ROOT.parent/'tmp/toc/blob-cache.json';write(cache_path,json.loads(seed.read_text()) if seed.exists() else {})
 cache=json.loads(cache_path.read_text())
 plan=json.loads((WORK/'plan.json').read_text());validation=json.loads((WORK/'validation.json').read_text());checks={x['order']:x for x in validation['checks']}
 assert validation['completed']==70
 # Read the committed checkpoint; never infer remote progress from local generation.
 remote=call('fetch_file',{'repository_full_name':REPO,'path':'src/pdf/_work/progress.json'})
 state=json.loads(remote['content']);published=max(state.get('published_orders',[]),default=0)
 # Preserve receipts from the just-completed connector batches if they are newer than the remote list.
 local=json.loads((WORK/'progress.json').read_text())
 for b in local.get('batches',[]):
  if b not in state.setdefault('batches',[]):state['batches'].append(b)
 log(f'Resumed at {published}/70')
 while published<70:
  end=min(published+10,70);write(WORK/'progress.json',state)
  subprocess.run([sys.executable,str(ROOT/'tools/index_topic_pdfs.py'),'--published',str(end)],check=True)
  state=json.loads((WORK/'progress.json').read_text())
  paths=['src/pdf/README.md','src/pdf/_work/progress.json','tools/publish_topic_pdfs.py','tools/work_hosted_apps.py']
  paths += ['src/pdf/'+x['path'] for x in plan[published:end]]
  entries=[]
  for rel in paths:
   p=ROOT/rel;b=p.read_bytes();sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
   if rel.endswith('.pdf'):
    item=next(x for x in plan if 'src/pdf/'+x['path']==rel)
    assert hashlib.sha256(b).hexdigest()==checks[item['order']]['sha256']
   if sha not in cache:
    got=call('create_blob',{'repository_full_name':REPO,'encoding':'base64','content':base64.b64encode(b).decode()})
    assert got['sha']==sha
    cache[sha]=True;write(cache_path,cache)
   entries.append({'path':rel,'mode':'100644','type':'blob','sha':sha})
   log('Blob ready: '+rel)
   write(RUNTIME/'state.json',{'phase':'uploading','published':published,'target':end,'last_file':rel})
  message=f'pdf: 完成第{published+1}—{end}专题整页拆分与持久化\n\nImplemented:\n- 发布本批专题PDF并更新目录和进度\n- 保存可恢复的发布程序与逐文件检查点\n\nWhy:\n- 按专题复习并避免中断后重复工作\n\nVerified:\n- 逐份核对页数和页面尺寸，遮盖区域外逐页像素一致\n- 本地PDF校验值匹配生成记录，上传blob SHA逐一匹配\n\nGenerated with Codex\nCo-Authored-By: Codex <noreply@openai.com>'
  for lease_attempt in range(4):
   head=fetch('git/ref/heads/main')['object']['sha'];parent=fetch('git/commits/'+head)
   tree=call('create_tree',{'repository_full_name':REPO,'base_tree_sha':parent['tree']['sha'],'tree_elements':entries})
   commit=call('create_commit',{'repository_full_name':REPO,'parent_sha':head,'tree_sha':tree['sha'],'message':message})
   try:
    call('update_ref',{'repository_full_name':REPO,'branch_name':'main','expected_sha':head,'force':False,'sha':commit['sha']})
    break
   except Exception:
    # A timed-out update may already have succeeded. Check before retrying.
    if fetch('git/ref/heads/main')['object']['sha']==commit['sha']:break
    if lease_attempt==3:raise
  remote_tree=fetch('git/trees/'+commit['sha']+'?recursive=1')
  lookup={x['path']:x.get('sha') for x in remote_tree['tree']}
  assert not remote_tree.get('truncated')
  assert all(lookup.get(x['path'])==x['sha'] for x in entries)
  receipt={'orders':[published+1,end],'commit':commit['sha'],'verified_remote':True}
  state.setdefault('batches',[]).append(receipt);state['published_orders']=list(range(1,end+1));state['completed_in_this_tree']=end
  write(WORK/'progress.json',state);write(RUNTIME/'state.json',{'phase':'published','published':end,'last_commit':commit['sha']})
  write(RUNTIME/f'batch-{end:02d}.json',receipt)
  log(f'PUBLISHED {end}/70: '+commit['sha']);published=end
 # Publish a final audit including the last batch receipt and all 70 remote file hashes.
 head=fetch('git/ref/heads/main')['object']['sha'];tree=fetch('git/trees/'+head+'?recursive=1');lookup={x['path']:x.get('sha') for x in tree['tree']}
 for x in plan:assert lookup.get('src/pdf/'+x['path'])==checks[x['order']]['git_blob_sha']
 audit={'published':70,'verified_pdf_count':70,'all_git_blob_shas_match':True,'batches':state['batches'],'verified_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checked_main_commit':head}
 write(WORK/'publication.json',audit)
 paths=['src/pdf/_work/progress.json','src/pdf/_work/publication.json','src/肖秀荣背诵手册-上册目录.md','src/pdf/_work/previews/part-ends.jpg'];elements=[]
 for rel in paths:
  b=(ROOT/rel).read_bytes();blob=call('create_blob',{'repository_full_name':REPO,'encoding':'base64','content':base64.b64encode(b).decode()});elements.append({'path':rel,'mode':'100644','type':'blob','sha':blob['sha']})
 # Refresh main immediately before the final checkpoint as well.
 head=fetch('git/ref/heads/main')['object']['sha'];parent=fetch('git/commits/'+head)
 t=call('create_tree',{'repository_full_name':REPO,'base_tree_sha':parent['tree']['sha'],'tree_elements':elements})
 c=call('create_commit',{'repository_full_name':REPO,'parent_sha':head,'tree_sha':t['sha'],'message':'pdf: 完成70专题远端校验与批次归档\n\nImplemented:\n- 归档全部批次提交和最终远端文件校验\n\nWhy:\n- 提供可追溯的完整交付与恢复记录\n\nVerified:\n- main中70份PDF的Git blob SHA全部匹配本地校验记录\n\nGenerated with Codex\nCo-Authored-By: Codex <noreply@openai.com>'})
 call('update_ref',{'repository_full_name':REPO,'branch_name':'main','expected_sha':head,'force':False,'sha':c['sha']})
 assert fetch('git/ref/heads/main')['object']['sha']==c['sha']
 write(RUNTIME/'state.json',{'phase':'complete','published':70,'last_commit':c['sha'],'all_remote_verified':True});log('COMPLETE '+c['sha'])
if __name__=='__main__':
 try:main()
 except Exception as e:
  log('STOPPED: '+type(e).__name__+'; restart resumes from verified remote checkpoint')
  write(RUNTIME/'error.json',{'type':type(e).__name__,'message':str(e)[:1000]})
  raise
