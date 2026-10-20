# 分析题材料与答案

保存肖秀荣教授官方 2027《背诵手册》带背视频片尾的题干材料和参考答案。

## 阅读入口

- [Day01 · 太阳黑子与望远镜](bank/day01.md) · [原视频](https://www.bilibili.com/video/BV17xpv6QEFA/)
- [Day02 · 票根经济](bank/day02.md) · [原视频](https://www.bilibili.com/video/BV1F4pj6uEQp/)
- [Day03 · 宽容失败与创新](bank/day03.md) · [原视频](https://www.bilibili.com/video/BV1aGpR6AERK/)
- [Day04 · 市场需求与传统产业转型](bank/day04.md) · [原视频](https://www.bilibili.com/video/BV1vnWA6fEbb/)
- [Day05 · 森林价值与因地制宜绿化](bank/day05.md) · [原视频](https://www.bilibili.com/video/BV1EWp26XEmb/)
- [Day06 · 以藕塑骨与科技创新](bank/day06.md) · [原视频](https://www.bilibili.com/video/BV1rDJy61EM5/)
- [Day07 · 科幻与社会现实](bank/day07.md) · [原视频](https://www.bilibili.com/video/BV1EhJX6aETJ/)
- [Day08 · 航天科技服务生产生活](bank/day08.md) · [原视频](https://www.bilibili.com/video/BV1wLJq64EA2/)
- [Day09 · 厚的读薄、薄的读厚](bank/day09.md) · [原视频](https://www.bilibili.com/video/BV1yunn6JExr/)
- [Day10 · 供需协同与产品创新](bank/day10.md) · [原视频](https://www.bilibili.com/video/BV17mnc6QEe4/)

已归档 10/10 期；当前清单全部完成。

## 目录约定

`bank/dayNN.md` 只展示两张原图：题干材料、参考答案。图片保存在 `bank/images/`；日期与 Day 编号分别记录，停更一天不会错位。`explain/` 暂只保留空目录，理解与解析的写法尚未确定，不自动生成内容。

## 图片口径

选择播放器可用的最高画质并关闭弹幕，暂停在完整静止页后截图；只裁播放器边框、黑边或空白边，不裁正文，不去水印，不重绘或放大冒充原图。当前播放源为 1920×1080，但首批交付是浏览器窗口截图，宽度 1363 像素，不能称为 1080P 原尺寸抽帧。后续若取得更高清原尺寸帧，应核对内容后替换同名图片并更新记录。

## 接力与更新

1. 先阅读仓库 `AGENTS.md` 和本目录 `sources.json`，读取最新 main。
2. 在官方合集（ID 9292051）检查是否有新一期，按实际 Day 编号及发布时间补入清单；先补旧缺口，禁止凭发布日期推算 Day 编号。
3. 检查片尾全部换页，保存完整材料页与答案页；如果未来一天出现多页，保留全部页并相应调整页面，不能漏页或强行拼成两张。无分析题时如实记录，不拿讲课截图代替。
4. 优先原尺寸抽帧；只能浏览器截图时记录真实分辨率。暂停后确认页眉 Day 和内容，避免片尾自动跳到下一期。截图时间记在 `timestamps`。
5. 运行 `python3 tools/manage_analysis_bank.py` 检查尺寸、文件哈希和图片链接。按仓库署名规则分批发布到 main，并核对远端哈希；只在新增归档、补缺或执行失败时通知用户。
6. 不修改字幕原件、历史讲稿或未成型的 `explain/`。自动检查配置另记录在 `sources.json` 的 `monitoring` 字段；任务是否已启用以自动化工具返回为准。

[来源、时间点、图片校验与进度](sources.json)

## 自动检查状态

已创建并启用：每天北京时间19:00检查一次，持续至2026-11-19。有新增视频则截图、核对、归档并提交；只在新增归档、补缺或执行失败时通知。核对 Day01—Day09 的公开发布时间，九期均为北京时间 19:00:00，官方简介也注明每晚 7 点同步更新，因此按真实更新点执行。逐期发布时间保存在 sources.json。定时检查不保证在视频发布瞬间完成，也不能把计划已启用当成未来每次运行都已成功。
