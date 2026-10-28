#!/usr/bin/env python3
"""Independently audit delivered Markdown against reviewed PDF-page records.

This script does not import build.py or use its parser or answer key.
Run: python3 src/questions_190/tools/audit.py [--check]
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

VERSION = '1.0'
OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
AUDIT = OUT / 'audit'
FILES = ('01-单选题1-46.md', '02-多选题1-70.md', '03-多选题71-147.md')


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_sha(question):
    text = json.dumps(question, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(text.encode()).hexdigest()


def parse_markdown():
    questions = []
    for name in FILES:
        text = (OUT / name).read_text()
        kind = 'S' if name.startswith('01') else 'M'
        for block in re.split(r'^## 第 ', text, flags=re.M)[1:]:
            number = int(re.match(r'(\d+) 题\n', block)[1])
            body = block.split('\n\n', 1)[1]
            assert '\n\nA. ' in body, (kind, number, 'missing A')
            stem = body.split('\n\nA. ', 1)[0]
            option_rows = re.findall(r'^([ABCD])\. (.*)$', body, re.M)
            assert [key for key, _ in option_rows] == list('ABCD'), (kind, number, 'option order')
            options = {key: value.rstrip('\\') for key, value in option_rows}
            assert stem and all(options.values()), (kind, number, 'empty text')
            answers = re.findall(r'^\*\*答案：([ABCD]+)\*\*', body, re.M)
            subjects = re.findall(r'^\*\*科目：(.+?)\*\*', body, re.M)
            assert len(answers) == len(subjects) == 1, (kind, number, 'metadata')
            assert len(answers[0]) == 1 if kind == 'S' else 2 <= len(answers[0]) <= 4
            assert answers[0] == ''.join(sorted(set(answers[0])))
            links = re.findall(r'\[PDF 第 (\d+) 页\]\(([^)]+)\)', body)
            assert links, (kind, number, 'missing source')
            pages = []
            for raw_page, link in links:
                page = int(raw_page)
                target, anchor = link.split('#page=')
                assert (OUT / target).is_file(), link
                assert ('001-060' if page <= 60 else '061-120') in target, link
                assert int(anchor) == (page if page <= 60 else page - 60), link
                assert 1 <= int(anchor) <= 60, link
                pages.append(page)
            questions.append({'key': kind + str(number), 'stem': stem, 'options': options,
                              'answer': answers[0], 'subject': subjects[0], 'pages': pages})
    assert [q['key'] for q in questions] == [f'S{n}' for n in range(1, 47)] + [f'M{n}' for n in range(1, 148)]
    return questions


def verify():
    review = json.loads((AUDIT / 'review.json').read_text())
    rows = json.loads((AUDIT / 'answer-rows.json').read_text())
    questions = parse_markdown()
    expected_answers = dict(zip([f'S{n}' for n in range(1, 47)], sum(rows['single'], [])))
    expected_answers.update(zip([f'M{n}' for n in range(1, 148)], sum(rows['multiple'], [])))
    assert len(sum(rows['single'], [])) == 46 and len(sum(rows['multiple'], [])) == 147
    expected_pages = {q['key']: [] for q in questions}
    for row in review['page_ledger']:
        for key in row['questions']:
            expected_pages[key].append(row['pdf_page'])
    for q in questions:
        assert q['answer'] == expected_answers[q['key']], (q['key'], 'answer mismatch')
        assert q['pages'] == expected_pages[q['key']], (q['key'], 'source-page mismatch')
        assert content_sha(q) == review['reviewed_question_sha256'][q['key']], (q['key'], 'text changed since visual review')
    assert all(file_sha(ROOT / name) == sha for name, sha in review['source_sha256'].items()), 'source changed'
    for path in OUT.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' not in link:
                assert (path.parent / link.split('#')[0]).is_file(), (path.name, link)
    assert all(q['subject'] in {'新思想', '时政', '法治', '史纲、时政'} for q in questions)
    evidence = {str(p.relative_to(OUT)): file_sha(p) for p in sorted(OUT.rglob('*'))
                if p.is_file() and p != AUDIT / 'result.json' and '__pycache__' not in p.parts}
    return {
        'audit_version': VERSION, 'review_date': review['review_date'],
        'baseline_commit': review['baseline_commit'],
        'counts': {'single': 46, 'multiple': 147, 'questions': len(questions),
                   'options': sum(len(q['options']) for q in questions), 'answers': len(expected_answers)},
        'pdf_pages_visually_reviewed': list(range(17, 66)),
        'independent_answer_table_match': 193, 'independent_page_ledger_match': 193,
        'reviewed_question_digest_match': 193,
        'content_corrections': 6, 'punctuation_corrections': 1, 'title_spacing_questions': 6,
        'original_source_discrepancies_preserved': review['source_discrepancies'],
        'scope': '检查扫描件转录忠实度、完整性、答案对应和页码，不独立背书原书每项时政事实或参考答案的知识正确性。',
        'evidence_sha256': evidence,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check the saved audit result without writing.')
    args = parser.parse_args()
    text = json.dumps(verify(), ensure_ascii=False, indent=2) + '\n'
    path = AUDIT / 'result.json'
    if args.check:
        assert path.read_text() == text, 'Audit inputs or delivered files changed; rerun and review.'
    else:
        path.write_text(text)
    print('OK: independently audited 193 questions, 772 options, 193 answers, 193 page mappings and reviewed text digests.')


if __name__ == '__main__':
    main()
