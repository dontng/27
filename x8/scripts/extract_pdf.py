#!/usr/bin/env python3
"""Extract scanned papers into x8/xiao8-NN.md; keep raw OCR under scripts/_work.
Requires PyMuPDF, Tesseract 5 and chi_sim traineddata. Run from any directory.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import fitz

ROOT = Path(__file__).resolve().parents[2]
X8 = ROOT / 'x8'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ocr_page(pdf, number, dpi, tessdata):
    with fitz.open(pdf) as doc:
        page = doc[number]
        native = page.get_text(sort=True)
        if len(native.strip()) > 80:
            return native, {'method': 'native', 'low_confidence': []}
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'page.png'
            page.get_pixmap(dpi=dpi).save(image)
            cmd = ['tesseract', str(image), str(Path(tmp) / 'ocr'), '-l', 'chi_sim', '--psm', '6']
            if tessdata:
                cmd += ['--tessdata-dir', str(tessdata)]
            cmd += ['-c', 'tessedit_create_txt=1', '-c', 'tessedit_create_tsv=1']
            subprocess.run(cmd, check=True, capture_output=True, env=dict(os.environ, OMP_THREAD_LIMIT='1'))
            text = (Path(tmp) / 'ocr.txt').read_text()
            with (Path(tmp) / 'ocr.tsv').open() as f:
                words = list(csv.DictReader(f, delimiter='\t'))
            low = [{'text': w['text'], 'confidence': float(w['conf']),
                    'box': [int(w[k]) for k in ('left', 'top', 'width', 'height')]}
                   for w in words if w.get('text', '').strip() and 0 <= float(w['conf']) < 60]
            return text, {'method': 'tesseract', 'low_confidence': low}


def normalize(text):
    # Use the existing question bank's established punctuation normalization.
    spec = importlib.util.spec_from_file_location('questions_190_builder', ROOT / 'src/questions_190/tools/build.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder.normalize(text)


def build_markdown(pdf, work, dpi):
    with fitz.open(pdf) as doc:
        count = len(doc)
    correction_file = X8 / 'scripts' / f'{pdf.stem}-corrections.json'
    corrections = json.loads(correction_file.read_text()) if correction_file.exists() else {}
    if corrections:
        assert corrections['source_sha256'] == sha256(pdf), 'Corrections belong to another PDF'
    all_raw, parts, page_records = [], [], []
    for index in range(count):
        text = (work / 'pages' / f'{index + 1:02d}.txt').read_text()
        metadata = json.loads((work / 'pages' / f'{index + 1:02d}.json').read_text())
        page_records.append({'page': index + 1, 'characters': len(text), **metadata})
        all_raw.append(f'## PDF 第 {index + 1} 页\n\n{text}')
        lines = [line.strip() for line in text.splitlines()]
        # Running headers are separate OCR lines; keep all question/material lines.
        lines = [line for line in lines if not ('考研' in line and '政治' in line)
                 and not re.fullmatch(r'[\d\s必]+', line)]
        # Detect question starts on original OCR lines, never inside the stem or a year.
        prepared = []
        for line in lines:
            line = normalize(re.sub(r'\s+', '', line))
            line = re.sub(r'^([人八入])\.', 'A.', line)
            line = re.sub(r'^([abcd])[.，、]', lambda m: m[1].upper() + '.', line)
            line = re.sub(r'^([ABCD])(?=[“《\u4e00-\u9fff])', r'\1.', line)
            match = re.match(r'^(\d{1,2})([.．、，。:：]|(?=[“《]))', line)
            if match and 1 <= int(match[1]) <= 38:
                line = f'\n@@QUESTION:{int(match[1])}@@' + line[match.end():]
            prepared.append(line)
        compact = ''.join(prepared)
        for source, target in corrections.get('pages', {}).get(str(index + 1), []):
            assert source in compact, (index + 1, source)
            compact = compact.replace(source, target)
        compact = re.sub(r'(?<![A-Za-z])([ABCD])(?:[.．、，…]+|(?=[“《\u4e00-\u9fff]))', r'\n\n\1. ', compact)
        compact = re.sub(r'@@QUESTION:(\d+)@@', r'\n\n\1. ', compact)
        compact = re.sub(r'(材料[123]|（[123]）)', r'\n\n\1 ', compact)
        parts.append(f'\n<!-- PDF 第 {index + 1} 页 -->\n' + compact)
    question_text = '\n'.join(parts)
    detected = [int(n) for n in re.findall(r'(?m)^\s*(\d{1,2})\s*[.．、]\s*', question_text)]
    question_text = re.sub(r'(?m)^\s*(\d{1,2})\s*[.．、]\s*', r'\n## 第 \1 题\n\n', question_text)
    current_page, refs = 1, []
    for match in re.finditer(r'<!-- PDF 第 (\d+) 页 -->|^## 第 (\d+) 题$', question_text, re.M):
        if match[1]:
            current_page = int(match[1])
        else:
            refs.append((match.end(), int(match[2]), current_page))
    for position, number, page in reversed(refs):
        question_text = question_text[:position] + f'\n\n[原卷 PDF 第 {page} 页](PDF/{pdf.name}#page={page})' + question_text[position:]
    # Reviewed transcriptions repair circled-number combinations that OCR cannot read reliably.
    for number, reviewed in corrections.get('reviewed_questions', {}).items():
        pattern = rf'(?ms)(^## 第 {number} 题\n)(.*?)(?=^## 第 \d+ 题\n|\Z)'
        def replace_reviewed(match):
            link = re.search(r'\[原卷 PDF 第 \d+ 页\]\([^\n]+\)', match[2])
            assert link, number
            return match[1] + '\n' + link[0] + '\n\n' + reviewed.strip() + '\n\n'
        question_text, replaced = re.subn(pattern, replace_reviewed, question_text)
        assert replaced == 1, (pdf.name, number, replaced)
    question_text = re.sub(r'(?m)^材料([123]) ', r'### 材料 \1\n\n', question_text)
    paper = int(pdf.stem.rsplit('-', 1)[1])
    header = (f'# 肖八第{paper}套卷 · 题目\n\n[返回肖八目录](README.md) · [查看原卷 PDF](PDF/{pdf.name})\n\n'
              '> 仅提取原题、选项、材料和设问，不新增答案或解析。OCR初稿，尚未逐字精校；请结合原卷核对关键措辞。\n\n'
              '**题号跳转：**[单选1—16](#第-1-题) · [多选17—33](#第-17-题) · [材料分析34—38](#第-34-题)\n\n')
    destination = X8 / f'{pdf.stem}.md'
    destination.write_text(header + question_text + '\n')
    # Raw fulltext is Markdown as in references/xiaoxiurong, not a TXT reading entry.
    (work / 'raw.md').write_text(f'# {pdf.stem} 逐页OCR原文\n\n' + '\n\n'.join(all_raw))
    chunks = re.split(r'(?m)^## 第 \d+ 题\n', question_text)[1:]
    option_issues = []
    for i, chunk in enumerate(chunks, 1):
        if i <= 33:
            labels = re.findall(r'(?m)^([ABCD])\. ', chunk)
            if labels != list('ABCD'):
                option_issues.append({'position': i, 'labels': labels})
    manifest = {'source': pdf.relative_to(ROOT).as_posix(), 'sha256': sha256(pdf), 'page_count': count,
                'dpi': dpi, 'language': 'chi_sim', 'tesseract': subprocess.check_output(['tesseract', '--version'], text=True).splitlines()[0],
                'pymupdf': fitz.VersionBind, 'status': 'OCR draft; not proofread word by word',
                'detected_question_numbers': detected, 'questions_1_to_38_complete': detected == list(range(1, 39)),
                'option_issues': option_issues, 'question_pages': [{'number': n, 'page': p} for _, n, p in refs],
                'pages': page_records}
    (work / 'extraction.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return {'paper': paper, 'pages': count, 'numbers': detected, 'option_issues': option_issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path, nargs='+')
    parser.add_argument('--tessdata', type=Path)
    parser.add_argument('--dpi', type=int, default=300)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--reuse-pages', action='store_true')
    args = parser.parse_args()
    jobs, papers = [], []
    for pdf in args.pdf:
        pdf = pdf.resolve()
        work = X8 / 'scripts' / '_work' / pdf.stem
        (work / 'pages').mkdir(parents=True, exist_ok=True)
        marker = work / 'source.sha256'
        source_hash = sha256(pdf)
        if marker.exists():
            assert marker.read_text().strip() == source_hash, 'Cached OCR belongs to another PDF'
        if (work / 'extraction.json').exists():
            prior = json.loads((work / 'extraction.json').read_text())
            assert prior['sha256'] == source_hash, 'Stored extraction belongs to another PDF'
            # Committed raw Markdown and metadata are sufficient to restore per-page caches.
            if (work / 'raw.md').exists():
                chunks = re.split(r'(?m)^## PDF 第 (\d+) 页\n\n', (work / 'raw.md').read_text())
                for j in range(1, len(chunks), 2):
                    page_number = int(chunks[j])
                    txt = work / 'pages' / f'{page_number:02d}.txt'
                    metadata = work / 'pages' / f'{page_number:02d}.json'
                    if not txt.exists():
                        txt.write_text(chunks[j + 1].rstrip() + '\n')
                    if not metadata.exists():
                        meta = prior['pages'][page_number - 1]
                        metadata.write_text(json.dumps({k: v for k, v in meta.items() if k not in ('page', 'characters')}, ensure_ascii=False) + '\n')
        marker.write_text(source_hash + '\n')
        papers.append((pdf, work))
        with fitz.open(pdf) as doc:
            for i in range(len(doc)):
                if (work / 'pages' / f'{i + 1:02d}.txt').exists() and (work / 'pages' / f'{i + 1:02d}.json').exists():
                    continue
                if args.reuse_pages:
                    raise ValueError(f'Missing cached page: {pdf.name} {i + 1}')
                jobs.append((pdf, work, i))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(ocr_page, pdf, i, args.dpi, args.tessdata): (pdf, work, i) for pdf, work, i in jobs}
        for future in concurrent.futures.as_completed(futures):
            pdf, work, i = futures[future]
            text, meta = future.result()
            (work / 'pages' / f'{i + 1:02d}.txt').write_text(text)
            (work / 'pages' / f'{i + 1:02d}.json').write_text(json.dumps(meta, ensure_ascii=False) + '\n')
            print(f'{pdf.stem}: page {i + 1} saved', flush=True)
    for pdf, work in papers:
        print(json.dumps(build_markdown(pdf, work, args.dpi), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
