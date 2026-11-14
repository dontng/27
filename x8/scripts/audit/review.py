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
    return text.replace('OCR初稿，尚未逐字精校；请结合原卷核对关键措辞。', '已完成第一轮逐页内容校对；关键措辞仍可结合原卷复核。').rstrip() + '\n'
