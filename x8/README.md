# 肖八

八套试卷从《27肖八试题-完整版.pdf》（82页）按整页拆分，未裁正文、未重绘。正式识别结果使用 Markdown；逐页 OCR 和校验数据在 `scripts/_work/` 内保留。

| 套卷 | 原完整版页码 | 页数 | 排版 PDF | 题目 Markdown |
| --- | --- | --- | --- | --- |
| 第一套 | 1—10 | 10 | [x8-01.pdf](pdf/x8-01.pdf) | [x8-01.md](md/x8-01.md) |
| 第二套 | 11—20 | 10 | [x8-02.pdf](pdf/x8-02.pdf) | [x8-02.md](md/x8-02.md) |
| 第三套 | 21—31 | 11 | [x8-03.pdf](pdf/x8-03.pdf) | [x8-03.md](md/x8-03.md) |
| 第四套 | 32—41 | 10 | [x8-04.pdf](pdf/x8-04.pdf) | [x8-04.md](md/x8-04.md) |
| 第五套 | 42—51 | 10 | [x8-05.pdf](pdf/x8-05.pdf) | [x8-05.md](md/x8-05.md) |
| 第六套 | 52—62 | 11 | [x8-06.pdf](pdf/x8-06.pdf) | [x8-06.md](md/x8-06.md) |
| 第七套 | 63—72 | 10 | [x8-07.pdf](pdf/x8-07.pdf) | [x8-07.md](md/x8-07.md) |
| 第八套 | 73—82 | 10 | [x8-08.pdf](pdf/x8-08.pdf) | [x8-08.md](md/x8-08.md) |

八份排版 PDF 和八份同名 Markdown 均已完成（原扫描件 `PDF/` 已移除，保留在 git 历史中）。每套38题（单选16题、多选17题、材料分析5题），共304题。原题、选项、材料和设问全部保留，不新增答案或解析。八套均已完成第一轮逐页内容校订，以及第二轮全文差异复核与原图重点核对。最新结果见[第二轮复核报告](scripts/audit/round2.md)，首轮过程见[第一轮报告](scripts/audit/README.md)。校订不等于逐字零误差。

## 选择题参考答案

[打开八套选择题答案目录](answers/README.md)。从用户提供的答案及解析PDF提取各卷“答案速查表”，每套33题，共264题；按套折叠展示单选、多选，并保留原表截图与PDF页码便于复核。原题区仍不夹入答案，`solutions/` 中的AI独立作答保持单独管理。

## 本人刷题记录

- [选择题排错标准动作与得分手册（SOP）](mc-sop.md)：做题 3 步标准动作、4 把排错刀法、单/多选落笔铁律与 35 分钟刷题流程。
- [分卷逐题排错经验指南（guide/）](guide/README.md)：每套 1 份，一题不跳按 3 步标准动作全解（已完成：[第 1 套指南](guide/x8-01.md)）。
- [进入刷题记录](records/README.md)：直接保存已刷完的 `x8-NN-done.pdf`、官方校准逐题记录与复盘报告（不设轮次子目录），与 `solutions/` 的 AI 候选解答分开管理。

## 真题样式 HTML

[打开八套试卷目录](html/index.html)。八套均从校订后的 Markdown 生成，沿用 `papers` 的 Times New Roman + 宋体正文、黑体标题及试卷布局。正文显示字号为16px，常规400字重；打印为11pt。每套HTML内嵌样式和脚本，可单独打开阅读、打印，也可切换分析题答题留白。

八份新排版PDF保存在 [`pdf/`](pdf) 中；[逐套查看](html/README.md#排版pdf)。

[最新HTML版式复核](scripts/html-layout-review.md)：已修正选项、材料出处与设问的17处打印分页问题，HTML与PDF已同步更新。

## 脚本

- `scripts/export_pdf.py`：读取最新HTML和打印CSS，导出同目录同名PDF，核对全部正文并保存哈希。
- `scripts/build_html.py`：从校订 Markdown 生成八套独立 HTML，逐题核对正文字符及结构；样式来自 `scripts/exam.css`，交互复用 `x8/scripts/exam.js`。
- `scripts/split_pdf.py`：依照已查看的八套卷边界拆分，并逐页比较渲染结果。
- `scripts/split-manifest.json`：输入SHA256、页码范围、各卷校验值及逐页一致性检查。
- `scripts/extract_pdf.py`：识别扫描页并生成同名 Markdown，复用项目已有习题190的标点规范化方法。

```bash
python3 x8/scripts/split_pdf.py /path/to/27肖八试题-完整版.pdf
python3 x8/scripts/extract_pdf.py x8/PDF/x8-0*.pdf --tessdata /path/to/tessdata
```

识别依赖 Python 3.10+、PyMuPDF、Tesseract 5 和 chi_sim 中文模型。逐页保存识别结果与源文件哈希，重复运行可续接未完成页；`--reuse-pages` 只从已有逐页原文重建 Markdown。

## 识别与检查

- 每套题号1—38连续；每套33道选择题各有ABCD四项，共1056个选项标签。
- 全部82页OCR原文存为逐页Markdown：`scripts/_work/x8-NN/raw.md`；正式阅读使用上方同名Markdown。
- 每套的`extraction.json`保留来源SHA256、页码映射、识别版本和低置信度位置；修正表绑定拆分PDF的SHA256，防止套用到其他版本。
- OCR漏掉的题号和①②③④组合题已对照原页修正，具体转写保留在各套修正表中。完整性检查不代表逐字正确，否定词、数字、专名等仍须结合原卷核对。
- `scripts/audit/reviewed-fixes.json`保存本轮逐条校订，重建Markdown时自动回放。
- 原始页TXT和逐页JSON仅作本地缓存，不作为正式入口；换环境时可由已提交的逐页Markdown与识别记录还原缓存。
