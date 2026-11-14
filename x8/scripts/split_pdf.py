#!/usr/bin/env python3
"""Split the checked 82-page full edition into eight intact papers."""
import argparse
import hashlib
import json
from pathlib import Path
import fitz

BOUNDARIES = [(1, 10), (11, 20), (21, 31), (32, 41), (42, 51), (52, 62), (63, 72), (73, 82)]
X8 = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    source = args.source
    document = fitz.open(source)
    assert len(document) == 82, 'This split map is only for the checked 82-page edition'
    records = []
    for n, (start, end) in enumerate(BOUNDARIES, 1):
        path = X8 / 'PDF' / f'xiao8-{n:02}.pdf'
        paper = fitz.open()
        paper.insert_pdf(document, from_page=start-1, to_page=end-1)
        paper.save(path, garbage=4, deflate=True)
        with fitz.open(path) as check:
            assert len(check) == end-start+1
            for i, page in enumerate(check):
                assert page.get_pixmap().samples == document[start-1+i].get_pixmap().samples
        records.append({'paper': n, 'file': f'x8/PDF/{path.name}', 'source_pages': [start, end],
                        'pages': end-start+1, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'render_matches_source': True})
    manifest = {'source_name': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'source_pages': len(document), 'papers': records}
    (X8 / 'scripts' / 'split-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')

if __name__ == '__main__':
    main()
