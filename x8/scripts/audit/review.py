#!/usr/bin/env python3
"""Replay PDF-checked literal corrections after OCR Markdown reconstruction."""
from pathlib import Path
import json
import re

LOG = Path(__file__).with_name('reviewed-fixes.json')

def apply_review(text, paper):
    if not LOG.exists():
        return text
    records = json.loads(LOG.read_text())
    round2_path = LOG.with_name('round2-review.json')
    round2 = json.loads(round2_path.read_text()) if round2_path.exists() else {}
    records.extend(round2.get('corrections', []))
    for record in [x for x in records if x['paper'] == paper]:
        pattern = rf'(?ms)(^## 第 {record["question"]} 题\n)(.*?)(?=^## 第 \d+ 题\n|\Z)'
        def replace(match):
            body = match[2]
            if record['old'] not in body:
                assert record['new'] in body, (paper, record['question'], record['old'])
                return match[0]
            return match[1] + body.replace(record['old'], record['new'])
        text, count = re.subn(pattern, replace, text)
        assert count == 1, (paper, record['question'])
    text = re.sub(r'(?<=[一-龥])\s*<!-- PDF 第 \d+ 页 -->\s*(?=[一-龥])', '', text)
    text = re.sub(r'(?m)^一[.、]?单项选择题', '一、单项选择题', text)
    if paper in round2.get('completed_papers', []):
        text = text.replace('已完成第一轮逐页内容校对', '已完成第二轮全文差异复核与原图重点校对').replace('OCR初稿，尚未逐字精校', '已完成第二轮全文差异复核与原图重点校对')
    return text.replace('OCR初稿，尚未逐字精校；请结合原卷核对关键措辞。', '已完成第一轮逐页内容校对；关键措辞仍可结合原卷复核。').rstrip() + '\n'
