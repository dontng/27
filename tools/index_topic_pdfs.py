#!/usr/bin/env python3
"""Update the navigation and per-commit checkpoint before a verified batch is published."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'src/pdf';WORK=BASE/'_work'
ap=argparse.ArgumentParser();ap.add_argument('--published',type=int,required=True);a=ap.parse_args()
plan=json.loads((WORK/'plan.json').read_text());valid=json.loads((WORK/'validation.json').read_text());checks={x['order']:x for x in valid['checks']}
assert 0<=a.published<=70
for i in range(1,a.published+1):assert checks[i]['generated']
state=json.loads((WORK/'progress.json').read_text());state['published_orders']=list(range(1,a.published+1));state['completed_in_this_tree']=a.published
(WORK/'progress.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
lines=['# 肖秀荣背诵手册上册 · 专题PDF','','[返回上册目录](../肖秀荣背诵手册-上册目录.md) · [使用方案](../answer.md) · [原文资料](../../references/xiaoxiurong/README.md)','','前四部分共70个专题，当前提交包含 **'+str(a.published)+'/70** 份。第五部分不在本次范围内。每份直接复制完整页面；同页跨专题时双方保留，不截图重建、不裁正文、不再次压缩扫描图片。页眉群号以空白边缘遮盖，页码、正文和页面大小保持。遮盖是视觉处理，底层扫描图像仍保留原像素。','','## 页码与文件','','下表为书内印刷页码。原PDF页码、共用页判断及全部70个专题的边界见 [_work/plan.json](_work/plan.json)。跨部分的分隔页不混入专题。']
for sec in range(1,5):
 subset=[x for x in plan if x['section']==sec];folder=subset[0]['path'].split('/')[0]
 lines+=['','## '+folder,'']
 ready=[x for x in subset if x['order']<=a.published]
 if not ready:lines+=['尚未发布。'];continue
 for x in ready:
  lines.append(f"- [{Path(x['path']).name}]({x['path']})：{x['book_start']}—{x['book_end']}页，共{x['pdf_end']-x['pdf_start']+1}页。")
lines+=['','## 接力与复现','','输入文件已在仓库 references/xiaoxiurong/pdf 中保存，不重复上传。[_work/inputs.json](_work/inputs.json) 固定输入版本、路径和SHA-256；[_work/validation.json](_work/validation.json) 记录逐文件校验；[_work/progress.json](_work/progress.json) 记录本提交包含的批次。[_work/previews](_work/previews) 保存逐专题起始页核对图，保留页底标题等边界证据。','','安装 PyMuPDF 和 numpy 后，在仓库根目录执行：','','```bash','python tools/split_xiaoxiurong.py --limit 70','```','','脚本先核对来源校验值，再按清单提取整页并遮盖页边群号，重新打开每份文件核对页数和页面尺寸，逐页比较遮盖区域以外的渲染结果。--limit 可用于分批恢复。校验通过后用 tools/index_topic_pdfs.py 更新索引与进度，再按 AGENTS.md 的署名规则分批提交到main。']
(BASE/'README.md').write_text('\n'.join(lines)+'\n')
