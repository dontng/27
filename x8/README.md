# 肖八

八套试卷从《27肖八试题-完整版.pdf》（82页）按整页拆分，未裁正文、未重绘。正式识别结果使用 Markdown；逐页 OCR 和校验数据在 `scripts/_work/` 内保留。

| 套卷 | 原完整版页码 | 页数 | PDF | 题目 Markdown |
| --- | --- | --- | --- | --- |
| 第一套 | 1—10 | 10 | [xiao8-01.pdf](PDF/xiao8-01.pdf) | [xiao8-01.md](xiao8-01.md) |
| 第二套 | 11—20 | 10 | [xiao8-02.pdf](PDF/xiao8-02.pdf) | [xiao8-02.md](xiao8-02.md) |
| 第三套 | 21—31 | 11 | [xiao8-03.pdf](PDF/xiao8-03.pdf) | [xiao8-03.md](xiao8-03.md) |
| 第四套 | 32—41 | 10 | [xiao8-04.pdf](PDF/xiao8-04.pdf) | [xiao8-04.md](xiao8-04.md) |
| 第五套 | 42—51 | 10 | [xiao8-05.pdf](PDF/xiao8-05.pdf) | [xiao8-05.md](xiao8-05.md) |
| 第六套 | 52—62 | 11 | [xiao8-06.pdf](PDF/xiao8-06.pdf) | [xiao8-06.md](xiao8-06.md) |
| 第七套 | 63—72 | 10 | [xiao8-07.pdf](PDF/xiao8-07.pdf) | [xiao8-07.md](xiao8-07.md) |
| 第八套 | 73—82 | 10 | [xiao8-08.pdf](PDF/xiao8-08.pdf) | [xiao8-08.md](xiao8-08.md) |

八份 PDF 和八份同名 Markdown 均已完成。每套38题（单选16题、多选17题、材料分析5题），共304题。原题、选项、材料和设问全部保留，不新增答案或解析。第一套复用此前初步核对的题目转写；其余各套为完整OCR稿，并对题号和圈号组合题做了修正，尚未完成全卷逐字精校。

## 脚本

- `scripts/split_pdf.py`：依照已查看的八套卷边界拆分，并逐页比较渲染结果。
- `scripts/split-manifest.json`：输入SHA256、页码范围、各卷校验值及逐页一致性检查。
- `scripts/extract_pdf.py`：识别扫描页并生成同名 Markdown，复用项目已有习题190的标点规范化方法。

```bash
python3 x8/scripts/split_pdf.py /path/to/27肖八试题-完整版.pdf
python3 x8/scripts/extract_pdf.py x8/PDF/xiao8-0*.pdf --tessdata /path/to/tessdata
```

识别依赖 Python 3.10+、PyMuPDF、Tesseract 5 和 chi_sim 中文模型。逐页保存识别结果与源文件哈希，重复运行可续接未完成页；`--reuse-pages` 只从已有逐页原文重建 Markdown。

## 识别与检查

- 每套题号1—38连续；每套33道选择题各有ABCD四项，共1056个选项标签。
- 全部82页OCR原文存为逐页Markdown：`scripts/_work/xiao8-NN/raw.md`；正式阅读使用上方同名Markdown。
- 每套的`extraction.json`保留来源SHA256、页码映射、识别版本和低置信度位置；修正表绑定拆分PDF的SHA256，防止套用到其他版本。
- OCR漏掉的题号和①②③④组合题已对照原页修正，具体转写保留在各套修正表中。完整性检查不代表逐字正确，否定词、数字、专名等仍须结合原卷核对。
- 原始页TXT和逐页JSON仅作本地缓存，不作为正式入口；换环境时可由已提交的逐页Markdown与识别记录还原缓存。
