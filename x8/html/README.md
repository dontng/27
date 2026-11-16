# 肖八 HTML 试卷

打开[index.html](index.html)进入八套目录。每套均为独立HTML，样式和脚本已内嵌，正文阅读不依赖外部资源。原卷、Markdown和校对记录的链接使用项目内相对路径。

字体族与 `papers/html` 保持一致：宋体正文、黑体标题；按照设备已有字体依次匹配 SimSun、Songti SC 等。调整正文显示字号、字重、行距和标题层次，保持纯黑白试卷样式，不模拟肖八扫描件字形，不通过描边处理文字。

生成命令：`python3 x8/scripts/build_html.py`。需Python 3及beautifulsoup4。全部304题与校订Markdown逐题逐字核验，共1056个选项标签和40道材料分析题；结果保存在[scripts/html-verification.json](../scripts/html-verification.json)。

本环境的浏览器无法打开本地文件，浏览器交互、手机实机显示及浏览器打印分页尚未验证。已用离线HTML排版器检查第一、八套页面的正文、材料和末页；离线排版器不执行选项分列脚本，不能代替浏览器检查。自适应分列与留白逻辑复用现有真题脚本。

## 排版PDF

八份同名PDF已由当前HTML导出，存放在 [`../pdf/`](../pdf)：

- [第1套 PDF](../pdf/x8-01.pdf) · [HTML](x8-01.html)
- [第2套 PDF](../pdf/x8-02.pdf) · [HTML](x8-02.html)
- [第3套 PDF](../pdf/x8-03.pdf) · [HTML](x8-03.html)
- [第4套 PDF](../pdf/x8-04.pdf) · [HTML](x8-04.html)
- [第5套 PDF](../pdf/x8-05.pdf) · [HTML](x8-05.html)
- [第6套 PDF](../pdf/x8-06.pdf) · [HTML](x8-06.html)
- [第7套 PDF](../pdf/x8-07.pdf) · [HTML](x8-07.html)
- [第8套 PDF](../pdf/x8-08.pdf) · [HTML](x8-08.html)

这里的PDF是按真实考场版式由当前HTML直接导出的；原扫描件 `PDF/` 已移除并保留在 git 历史中。

导出命令：`python3 x8/scripts/export_pdf.py`。使用当前HTML内嵌打印样式，A4纵向；离线排版器不执行JavaScript，导出脚本按现有选项分列的4/2/1规则，使用打印字体实测文字宽度后分列。未修改HTML内容或样式。字体由HTML字体栈在导出环境中匹配，与其他设备浏览器可能存在细微字形或分页差异。

已检查全部79页缩略图，并查看首页、材料题样页；逐段文字与HTML匹配，没有空白页或越界文字。导出来源哈希、PDF哈希及逐页统计见[scripts/pdf-export.json](../scripts/pdf-export.json)。

## 版式复核更新

已完成[八套版式复核](../scripts/html-layout-review.md)，修正17处打印分页问题。当前HTML、同目录PDF及合包同步更新；四种宽度的离线模拟通过，Safari/Chrome真实浏览器测试仍未完成。
