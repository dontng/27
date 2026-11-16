#!/usr/bin/env python3
"""Publish only analysis-bank files, based on the latest main, with SHA checks."""
import base64
import hashlib
import json
import sys
from pathlib import Path
from work_hosted_apps import HostedAppsClient
from publish_topic_pdfs import unpack

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dontng/27'

def main():
    title = sys.argv[1]
    client = HostedAppsClient()
    connector = None
    cursor = None
    for _ in range(100):
        result = client._rpc('tools/list', {'cursor': cursor} if cursor else {})
        for tool in result.get('tools', []):
            meta = tool.get('_meta', {})
            if meta.get('connector_name') == 'GitHub' and tool.get('name', '').endswith('create_blob'):
                connector = meta['connector_id']
        cursor = result.get('nextCursor', result.get('next_cursor'))
        if connector or not cursor:
            break
    if not connector:
        raise RuntimeError('GitHub connection unavailable')
    def call(name, args):
        return unpack(client.call_tool(connector, name, args))
    def fetch(path):
        return call('fetch', {'url': 'https://api.github.com/repos/' + REPO + '/' + path})
    head = fetch('git/ref/heads/main')['object']['sha']
    parent = fetch('git/commits/' + head)
    remote_tree = fetch('git/trees/' + parent['tree']['sha'] + '?recursive=1')
    remote = {entry['path']: entry['sha'] for entry in remote_tree['tree']}
    paths = [p for p in (ROOT / 'src/analysis').rglob('*') if p.is_file()]
    paths += [ROOT / 'tools/manage_analysis_bank.py', ROOT / 'tools/publish_analysis_bank.py']
    entries = []
    for path in sorted(paths):
        relative = str(path.relative_to(ROOT))
        content = path.read_bytes()
        sha = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if remote.get(relative) == sha:
            continue
        blob = call('create_blob', {'repository_full_name': REPO, 'content': base64.b64encode(content).decode(), 'encoding': 'base64'})
        assert blob['sha'] == sha, relative
        entries.append({'path': relative, 'mode': '100644', 'type': 'blob', 'sha': sha})
        print('Ready ' + relative, flush=True)
    if not entries:
        print('No changes to publish')
        return
    message = title + '\n\nImplemented:\n- 归档已核对的片尾材料与答案，更新仅含原图的bank页面和来源进度\n- 保留explain空目录，记录真实截图尺寸及接力流程\n\nWhy:\n- 支持连续约30天的带背分析题积累并避免漏期和误认原尺寸\n\nVerified:\n- 本批图片已逐页查看，尺寸、SHA256和Markdown图片链接通过本地检查\n- 上传blob逐一核对Git SHA，基于最新main快进发布\n\nGenerated with Codex\nCo-Authored-By: Codex <noreply@openai.com>'
    for attempt in range(3):
        head = fetch('git/ref/heads/main')['object']['sha']
        parent = fetch('git/commits/' + head)
        tree = call('create_tree', {'repository_full_name': REPO, 'base_tree_sha': parent['tree']['sha'], 'tree_elements': entries})
        commit = call('create_commit', {'repository_full_name': REPO, 'parent_sha': parent['sha'], 'tree_sha': tree['sha'], 'message': message})
        try:
            call('update_ref', {'repository_full_name': REPO, 'branch_name': 'main', 'expected_sha': parent['sha'], 'force': False, 'sha': commit['sha']})
            break
        except Exception:
            # Read the actual head after a failed lease; never force-push.
            head = fetch('git/ref/heads/main')['object']['sha']
            if head == commit['sha']:
                break
            if attempt == 2:
                raise
    result = fetch('git/trees/' + commit['sha'] + '?recursive=1')
    remote = {entry['path']: entry['sha'] for entry in result['tree']}
    assert all(remote.get(entry['path']) == entry['sha'] for entry in entries)
    print(json.dumps({'commit': commit['sha'], 'files_changed': len(entries), 'remote_hashes_verified': True}), flush=True)

if __name__ == '__main__':
    main()
