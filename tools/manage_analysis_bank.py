#!/usr/bin/env python3
"""Rebuild the screenshot-only bank and verify every archived image/link."""
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src/analysis'

def main():
    source = json.loads((BASE / 'sources.json').read_text())
    completed = []
    for day in source['videos']:
        number = day['day']
        images = []
        for kind in ('material', 'answer'):
            relative = f'bank/images/day{number:02d}-{kind}.jpg'
            path = BASE / relative
            if not path.exists():
                continue
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', str(path)]))['streams'][0]
            assert probe['width'] >= 1200 and probe['height'] >= 650, relative
            images.append({'kind': kind, 'path': relative, 'width': probe['width'], 'height': probe['height'], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'timestamp_seconds': day.get('timestamps', {}).get(kind)})
        day['images'] = images
        day['status'] = 'archived' if len(images) == 2 else 'pending'
        if day['status'] != 'archived':
            continue
        completed.append(day)
        # Each bank page contains only the original material and answer images.
        text = f'![Day{number:02d} 题干材料](images/day{number:02d}-material.jpg)\n\n![Day{number:02d} 参考答案](images/day{number:02d}-answer.jpg)\n'
        (BASE / f'bank/day{number:02d}.md').write_text(text)
    source['checked_at'] = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
    source['archived_days'] = [day['day'] for day in completed]
    (BASE / 'sources.json').write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 分析题材料与答案', '', '保存肖秀荣教授官方 2027《背诵手册》带背视频片尾的题干材料和参考答案。', '', '## 阅读入口', '']
    for day in completed:
        number = day['day']
        lines.append(f"- [Day{number:02d} · {day['topic']}](bank/day{number:02d}.md) · [原视频]({day['url']})")
    pending = [str(day['day']) for day in source['videos'] if day['status'] != 'archived']
    lines += ['', f"已归档 {len(completed)}/{len(source['videos'])} 期；" + ('待补 Day' + '、'.join(pending) + '。' if pending else '当前清单全部完成。'), '', '## 目录约定', '', '`bank/dayNN.md` 只展示两张原图：题干材料、参考答案。图片保存在 `bank/images/`；日期与 Day 编号分别记录，停更一天不会错位。`explain/` 暂只保留空目录，理解与解析的写法尚未确定，不自动生成内容。', '', '## 图片口径', '', '选择播放器可用的最高画质并关闭弹幕，只裁播放器边框、黑边或空白边，不裁正文，不去水印，不重绘或放大冒充原图。Day01—Day11为1080P播放源的浏览器窗口截图，宽度1363像素；Day12起优先使用1920×1080原始播放流抽帧。各期实际尺寸、方式和哈希以 `sources.json` 为准。', '', '## 接力与更新', '', '1. 先阅读仓库 `AGENTS.md` 和本目录 `sources.json`，读取最新 main。', '2. 在官方合集（ID 9292051）检查是否有新一期，按实际 Day 编号及发布时间补入清单；先补旧缺口，禁止凭发布日期推算 Day 编号。', '3. 检查片尾全部换页，保存完整材料页与答案页；如果未来一天出现多页，保留全部页并相应调整页面，不能漏页或强行拼成两张。无分析题时如实记录，不拿讲课截图代替。', '4. 优先原尺寸抽帧；只能浏览器截图时记录真实分辨率。暂停后确认页眉 Day 和内容，避免片尾自动跳到下一期。截图时间记在 `timestamps`。', '5. 运行 `python3 tools/manage_analysis_bank.py` 检查尺寸、文件哈希和图片链接。按仓库署名规则分批发布到 main，并核对远端哈希；只在新增归档、补缺或执行失败时通知用户。', '6. 不修改字幕原件、历史讲稿或未成型的 `explain/`。自动检查配置另记录在 `sources.json` 的 `monitoring` 字段；任务是否已启用以自动化工具返回为准。', '', '[来源、时间点、图片校验与进度](sources.json)', '']
    if source.get('monitoring', {}).get('status') == 'blocked_by_task_limit':
        lines += ['## 自动检查状态', '', '尚未启用。创建任务时系统返回 `too_many_active_automations`，现有任务数已达 5/5。拟每天北京时间 19:10—23:10 每小时检查一次，至 2026-11-19；需用户指定腾出哪个旧任务的名额后再创建，不能视为已经在后台执行。', '']
    elif source.get('monitoring', {}).get('status') == 'enabled':
        lines += ['## 自动检查状态', '', '已创建并启用：' + source['monitoring']['display_schedule'] + '。有新增视频则截图、核对、归档并提交；只在新增归档、补缺或执行失败时通知。核对 Day01—Day09 的公开发布时间，九期均为北京时间 19:00:00，官方简介也注明每晚 7 点同步更新，因此按真实更新点执行。逐期发布时间保存在 sources.json。定时检查不保证在视频发布瞬间完成，也不能把计划已启用当成未来每次运行都已成功。', '']
    (BASE / 'README.md').write_text('\n'.join(lines))
    for page in BASE.rglob('*.md'):
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', page.read_text()):
            if target.startswith(('http://', 'https://', '#')):
                continue
            assert (page.parent / target.split('#')[0]).exists(), (page, target)
    print(json.dumps({'archived': source['archived_days'], 'pending': pending, 'images_checked': sum(len(d['images']) for d in source['videos']), 'links_checked': True}, ensure_ascii=False))

if __name__ == '__main__':
    main()
