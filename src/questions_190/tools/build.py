#!/usr/bin/env python3
"""Rebuild the question set from the committed OCR and reviewed corrections.

Run from anywhere: python3 src/questions_190/tools/build.py [--check]
Only the Python standard library is required; existing reference files are inputs.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

VERSION = '1.1'
OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
SOURCE = ROOT / 'references/xiaoxiurong/27肖秀荣-背诵手册【下册】.md'
OPTION = re.compile(r'(?<![A-Za-z])([ABCD])(?:-?[.．、,，]|L(?:[. ]|(?=[\u4e00-\u9fff“]))|[-])\s*')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_source():
    pages = re.split(r'## PDF 第 (\d+) 页\n', SOURCE.read_text())
    blocks = []
    for i in range(1, len(pages), 2):
        page = int(pages[i])
        if not 18 <= page <= 63:
            continue
        text = pages[i + 1].split('二、参考答案')[0]
        # The OCR sometimes concatenates a new stem with the preceding D option.
        text = re.sub(r'\n(?=(?:学习贯彻|习近平|经党中央|202[56]年|《|中国共产党人|当前，|“十五五|制定民族|民族团结|打太极|中共中央|183\.))', '\n\n', text)
        for para in re.split(r'\n\s*\n', text):
            lines = []
            for line in para.splitlines():
                line = line.strip()
                if not line or re.fullmatch(r'[\dA-Za-z .?，。()\[\]一了对副|@{}\\]+', line):
                    continue
                compact = line.replace(' ', '')
                if any(x in compact for x in ['习题190', '习题100', '习古190']) or ('2027' in line and '手册' in line):
                    continue
                if '单项选择题' in line or '多项选择题' in line or line == '一、题目':
                    continue
                if not re.search(r'[\u4e00-\u9fff]', line) and not re.match(r'^[ABCD]', line):
                    continue
                lines.append(line)
            if lines:
                blocks.append((page, '\n'.join(lines)))

    def empty():
        return {'stem': [], 'options': {}, 'pages': set()}

    questions, question, current = [], empty(), 'stem'
    for page, text in blocks:
        # Two option labels were dropped by OCR; both were checked on PDF pages 32/40.
        if text.startswith('持之以恒推进全面从严治党'):
            text = 'C. ' + text
        text = text.replace('5. 一部实施宪法有关规定', 'C. 一部实施宪法有关规定')
        if current == 'D':
            continuation = re.match(r'^(新高度|道路|建设等核心概念|面的重要作用|战略依托|规律|真理|定决心|发展|方针|和平|奋进|体系|代化|国家|界|进程|体制|成果)[。]?$', text)
            if not continuation and len(text) > 5:
                questions.append(question)
                question, current = empty(), 'stem'
        position = 0
        for match in OPTION.finditer(text):
            target = question['stem'] if current == 'stem' else question['options'][current]
            target.append(text[position:match.start()])
            current = match[1]
            assert current not in question['options'], (page, 'duplicate option', current)
            question['options'][current] = []
            position = match.end()
        target = question['stem'] if current == 'stem' else question['options'][current]
        target.append(text[position:])
        question['pages'].add(page)
    questions.append(question)
    assert len(questions) == 193, len(questions)
    for index, question in enumerate(questions):
        question['key'] = f'S{index + 1}' if index < 46 else f'M{index - 45}'
        question['number'] = index + 1 if index < 46 else index - 45
        question['type'] = 'single' if index < 46 else 'multiple'
        question['pages'] = sorted(question['pages'])
        question['stem'] = re.sub(r'\s+', '', ''.join(question['stem']))
        question['options'] = {k: re.sub(r'\s+', '', ''.join(v)) for k, v in question['options'].items()}
    return questions


def normalize(text):
    text = text.replace('(', '（').replace(')', '）').replace('〈', '（')
    text = text.replace(':', '：').replace(',', '，').replace(';', '；').replace('?', '？').replace('!', '！')
    text = text.replace('"十五五', '“十五五').replace('《"一国', '《“一国')
    text = text.replace('"', '”')
    for old, new in {'福社': '福祉', '阑明': '阐明', '一一服务业': '——服务业', '不觉远一一': '不觉远——'}.items():
        text = text.replace(old, new)
    return text


def subject(question):
    n = question['number']
    if question['type'] == 'single':
        if n in {14, 15} or 17 <= n <= 22:
            return '法治'
        return '时政' if n >= 37 else '新思想'
    if 54 <= n <= 60 or 68 <= n <= 71 or 80 <= n <= 87:
        return '法治'
    if n in {106, 107, 116, 125, 126, 127} or n >= 135:
        return '史纲、时政' if n in {142, 143} else '时政'
    return '新思想'


def verify_answer_ocr():
    """Compare a second OCR reading against the visually transcribed answer key."""
    text = (OUT / 'tools/answer-table-ocr.txt').read_text()
    single, multiple = re.split(r'\(\s*二\s*\)\s*多项选择题', text)
    answers = json.loads((OUT / 'tools/answers.json').read_text())
    result = {}
    for kind, text in [('single', single), ('multiple', multiple)]:
        found = {int(n): value for n, value in re.findall(r'(?<!\d)(\d{1,3})[.，,:：]*\s*([ABCD]{1,4})(?=\s|$)', text)}
        found = {n: value for n, value in found.items() if n <= len(answers[kind])}
        missing = sorted(set(range(1, len(answers[kind]) + 1)) - set(found))
        assert missing == ([1, 23, 39] if kind == 'single' else []), (kind, missing)
        assert all(answers[kind][n - 1] == value for n, value in found.items()), kind
        result[kind] = {'matched': len(found), 'ocr_unreadable_checked_on_scan': missing}
    return result


def apply_corrections(questions):
    corrections = json.loads((OUT / 'tools/corrections.json').read_text())
    answers = json.loads((OUT / 'tools/answers.json').read_text())
    assert set(corrections) <= {q['key'] for q in questions}
    counts = Counter()
    for question in questions:
        for field, correction in corrections.get(question['key'], {}).items():
            target = question if field == 'stem' else question['options']
            before = target.get(field, '')
            if isinstance(correction, str):
                after = correction
            else:
                after = before
                for old, new in correction:
                    assert old in after, (question['key'], field, old)
                    after = after.replace(old, new)
            target[field] = after
            counts[question['key']] += 1
        question['stem'] = normalize(question['stem'])
        question['options'] = {k: normalize(v) for k, v in question['options'].items()}
        question['subject'] = subject(question)
        question['answer'] = answers[question['type']][question['number'] - 1]
        assert question['stem'] and set(question['options']) == set('ABCD'), question['key']
        assert all(question['options'].values()), question['key']
        assert re.fullmatch('[ABCD]' if question['type'] == 'single' else '[ABCD]{2,4}', question['answer'])
        assert question['answer'] == ''.join(sorted(set(question['answer'])))
        assert not re.search(r'[A-Za-z*]', question['stem']), question['key']
        for text in [question['stem'], *question['options'].values()]:
            for opening, closing in [('“', '”'), ('‘', '’'), ('（', '）'), ('《', '》')]:
                assert text.count(opening) == text.count(closing), (question['key'], text)
    assert len(answers['single']) == 46 and len(answers['multiple']) == 147
    return counts


def pdf_link(page):
    start = 1 if page <= 60 else 61
    part = '001-060' if page <= 60 else '061-120'
    return f'[PDF 第 {page} 页](../../references/xiaoxiurong/pdf/27肖秀荣-背诵手册【下册】-PDF页{part}.pdf#page={page - start + 1})'


def nav_bar(start_num, last_num, step=10):
    anchors = []
    for i in range(start_num, last_num + 1, step):
        end = min(i + step - 1, last_num)
        anchors.append(f'[{i}—{end}](#第-{i}-题)')
    return ' · '.join(anchors)


def render(title, questions):
    total = len(questions)
    first_num = questions[0]['number']
    last_num = questions[-1]['number']
    kind_text = '单项选择题' if questions[0]['type'] == 'single' else '多项选择题'

    lines = [
        f'# {title}',
        '',
        '[返回习题 190 总索引](README.md)',
        '',
        '> [!TIP]',
        '> **刷题自测指南**：',
        f'> - 本卷共 **{total}** 道{kind_text}，已去除转义杂音，选项对齐排版。',
        '> - **参考答案与出处默认折叠隐藏**，建议先独立作答，选择答案后再点击展开核对。',
        '> - 每道题均已链接至原书高清 PDF 扫描页对应位置，支持一键溯源查证。',
        '',
        f'**题号快速跳转**：{nav_bar(first_num, last_num, 10)}',
        '',
        '---',
        ''
    ]

    for q in questions:
        n = q['number']
        stem = q['stem']
        optA = q['options']['A']
        optB = q['options']['B']
        optC = q['options']['C']
        optD = q['options']['D']
        ans = q['answer']
        subj = q['subject']
        links = '、'.join(pdf_link(p) for p in q['pages'])

        lines += [
            f'## 第 {n} 题',
            '',
            stem,
            '',
            f'A. {optA}',
            f'B. {optB}',
            f'C. {optC}',
            f'D. {optD}',
            '',
            '<details>',
            '<summary><b>点击查看【答案与出处】</b></summary>',
            '',
            f'**答案：{ans}**',
            f'**科目：{subj}**',
            f'**出处：**{links}',
            '',
            '</details>',
            '',
            '---',
            ''
        ]
    return '\n'.join(lines)


def build():
    questions = parse_source()
    corrected = apply_corrections(questions)
    outputs = {
        '01-单选题1-46.md': render('单项选择题 1—46', questions[:46]),
        '02-多选题1-70.md': render('多项选择题 1—70', questions[46:116]),
        '03-多选题71-147.md': render('多项选择题 71—147', questions[116:]),
    }
    inputs = [SOURCE] + sorted((ROOT / 'references/xiaoxiurong/pdf').glob('*下册*PDF页0*.pdf'))
    report = {
        'generator_version': VERSION,
        'source_sha256': {str(path.relative_to(ROOT)): sha256(path) for path in inputs},
        'processing_inputs_sha256': {str(path.relative_to(OUT)): sha256(path) for path in sorted((OUT / 'tools').iterdir()) if path.is_file()},
        'counts': {'single': 46, 'multiple': 147, 'total': 193, 'options': 772, 'answers': 193},
        'question_pdf_pages': [18, 63],
        'answer_pdf_pages': [63, 64],
        'visual_review': '2026-10-29第二轮：逐页对照PDF第18—64页审核193题正文、772项选项和193项参考答案；差异及证据见audit/README.md。核对范围是扫描件转录忠实度，不是逐题独立验证政治事实。',
        'independent_answer_ocr_comparison': verify_answer_ocr(),
        'corrected_question_count': len(corrected),
        'questions': [{'key': q['key'], 'pdf_pages': q['pages'], 'answer': q['answer'], 'subject': q['subject']} for q in questions],
        'output_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in outputs.items()},
    }
    outputs['validation.json'] = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare committed output with a fresh in-memory build; do not write files.')
    args = parser.parse_args()
    outputs = build()
    for name, content in outputs.items():
        path = OUT / name
        if args.check:
            assert path.read_text() == content, f'outdated output: {name}'
        else:
            path.write_text(content)
    print('OK: 46 single + 147 multiple = 193 questions; 772 options; 193 matched answers.')


if __name__ == '__main__':
    main()
