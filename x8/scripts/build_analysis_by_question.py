#!/usr/bin/env python3
"""Build the five cross-paper views of the Xiao 8 analysis questions."""

import argparse
import re
from pathlib import Path


X8 = Path(__file__).resolve().parents[1]
WRITING = X8 / "analysis-writing"
SUBJECTS = {
    34: "马原",
    35: "新思想",
    36: "史纲",
    37: "思法",
    38: "当代",
}


def read_sections(path, heading_pattern):
    text = path.read_text(encoding="utf-8")
    sections = {}
    headings = list(re.finditer(f"^{heading_pattern}$", text, re.MULTILINE))
    for index, match in enumerate(headings):
        number = int(match[1])
        if number not in SUBJECTS:
            continue
        if number in sections:
            raise ValueError(f"{path}: duplicate question {number}")
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = re.split(r"^---[ \t]*$", text[match.end():end], maxsplit=1, flags=re.MULTILINE)[0]
        sections[number] = (match[0], body.strip())
    if sections.keys() != SUBJECTS.keys():
        raise ValueError(f"{path}: expected questions 34–38, found {list(sections)}")
    return sections


def build_views():
    views = {
        number: [
            f"# 肖八第 {number} 题 · {subject}（八套对照）\n\n"
            "<!-- 由 x8/scripts/build_analysis_by_question.py 生成，请修改对应的原卷或分卷作答。 -->\n\n"
            "[返回分析题目录](README.md)\n\n"
            "展开原卷材料，读完两问并列出要点，再展开分卷作答核对。\n\n"
            + " · ".join(f"[第 {paper} 套](#第-{paper}-套)" for paper in range(1, 9))
        ]
        for number, subject in SUBJECTS.items()
    }

    for paper in range(1, 9):
        filename = f"x8-{paper:02}.md"
        original = read_sections(X8 / "md" / filename, r"### 第 (\d+) 题")
        writing = read_sections(WRITING / filename, r"## 第 (\d+) 题 · .+")
        for number in SUBJECTS:
            _, question = original[number]
            material, marker, prompts = question.partition("\n**设问：**\n")
            heading, answer = writing[number]
            page = re.search(r"（(PDF 第 [^）]+)）$", heading)
            if (
                not marker
                or re.findall(r"^\*\*（([12])）\*\*", prompts, re.MULTILINE) != ["1", "2"]
                or re.findall(r"^### （([12])）", answer, re.MULTILINE) != ["1", "2"]
                or page is None
            ):
                raise ValueError(f"{filename}: incomplete question or answer for {number}")
            title = heading.split(" · ", 1)[1].split("｜", 1)[0]
            prompts = re.sub(r"[ \t]*\n(?=\*\*（2）\*\*)", "\n\n", prompts.strip())
            views[number].append(
                f"## 第 {paper} 套\n\n"
                f"**{title}** · "
                f"[原卷第 {number} 题](../md/{filename}#第-{number}-题) · "
                f"[分卷作答]({filename}) · 参考答案 {page[1]}\n\n"
                "<details>\n<summary>展开原卷材料</summary>\n\n"
                f"{material.strip()}\n\n</details>\n\n"
                f"**设问：**\n\n{prompts}\n\n"
                "<details>\n<summary>展开两问作答与防丢分提醒</summary>\n\n"
                f"{answer}\n\n</details>"
            )

    return {
        WRITING / f"q{number}.md": "\n\n".join(sections) + "\n"
        for number, sections in views.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check that all five files are up to date")
    args = parser.parse_args()

    for path, content in build_views().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                parser.exit(1, f"{path.name} is out of date. Run this script without --check.\n")
        else:
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
