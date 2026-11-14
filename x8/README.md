# 肖八

八套试卷从《27肖八试题-完整版.pdf》（82页）按整页拆分，未裁正文、未重绘。正式识别结果使用 Markdown；逐页 OCR 和校验数据在 `scripts/_work/` 内保留。

| 套卷 | 原完整版页码 | 页数 | PDF |
| --- | --- | --- | --- |
| 第一套 | 1—10 | 10 | [xiao8-01.pdf](PDF/xiao8-01.pdf) |
| 第二套 | 11—20 | 10 | [xiao8-02.pdf](PDF/xiao8-02.pdf) |
| 第三套 | 21—31 | 11 | [xiao8-03.pdf](PDF/xiao8-03.pdf) |
| 第四套 | 32—41 | 10 | [xiao8-04.pdf](PDF/xiao8-04.pdf) |
| 第五套 | 42—51 | 10 | [xiao8-05.pdf](PDF/xiao8-05.pdf) |
| 第六套 | 52—62 | 11 | [xiao8-06.pdf](PDF/xiao8-06.pdf) |
| 第七套 | 63—72 | 10 | [xiao8-07.pdf](PDF/xiao8-07.pdf) |
| 第八套 | 73—82 | 10 | [xiao8-08.pdf](PDF/xiao8-08.pdf) |

本批先归档八份 PDF，Markdown 正在依据这份完整版重新识别。第一套此前的单独上传版由完整版对应页替换。

## 脚本

- `scripts/split_pdf.py`：依照已查看的八套卷边界拆分，并逐页比较渲染结果。
- `scripts/split-manifest.json`：输入SHA256、页码范围、各卷校验值及逐页一致性检查。
- `scripts/extract_pdf.py`：识别扫描页并生成同名 Markdown，复用项目已有习题190的标点规范化方法。

```bash
python3 x8/scripts/split_pdf.py /path/to/27肖八试题-完整版.pdf
python3 x8/scripts/extract_pdf.py x8/PDF/xiao8-0*.pdf --tessdata /path/to/tessdata
```

识别依赖 Python 3.10+、PyMuPDF、Tesseract 5 和 chi_sim 中文模型。逐页保存识别结果与源文件哈希，重复运行可续接未完成页；`--reuse-pages` 只从已有逐页原文重建 Markdown。
