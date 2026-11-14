# 肖八 HTML 试卷

打开[index.html](index.html)进入八套目录。每套均为独立HTML，样式和脚本已内嵌，正文阅读不依赖外部资源。原卷、Markdown和校对记录的链接使用项目内相对路径。

字体族与 `papers/html` 保持一致：宋体正文、黑体标题；按照设备已有字体依次匹配 SimSun、Songti SC 等。调整正文显示字号、字重、行距和标题层次，保持纯黑白试卷样式，不模拟肖八扫描件字形，不通过描边处理文字。

生成命令：`python3 x8/scripts/build_html.py`。需Python 3及beautifulsoup4。全部304题与校订Markdown逐题逐字核验，共1056个选项标签和40道材料分析题；结果保存在[scripts/html-verification.json](../scripts/html-verification.json)。

本环境的浏览器无法打开本地文件，浏览器交互、手机实机显示及浏览器打印分页尚未验证。已用离线HTML排版器检查第一、八套页面的正文、材料和末页；离线排版器不执行选项分列脚本，不能代替浏览器检查。自适应分列与留白逻辑复用现有真题脚本。

## 同目录排版PDF

八份同名PDF已由当前HTML导出，直接放在HTML旁边：

- [第1套 PDF](xiao8-01.pdf) · [HTML](xiao8-01.html)
- [第2套 PDF](xiao8-02.pdf) · [HTML](xiao8-02.html)
- [第3套 PDF](xiao8-03.pdf) · [HTML](xiao8-03.html)
- [第4套 PDF](xiao8-04.pdf) · [HTML](xiao8-04.html)
- [第5套 PDF](xiao8-05.pdf) · [HTML](xiao8-05.html)
- [第6套 PDF](xiao8-06.pdf) · [HTML](xiao8-06.html)
- [第7套 PDF](xiao8-07.pdf) · [HTML](xiao8-07.html)
- [第8套 PDF](xiao8-08.pdf) · [HTML](xiao8-08.html)

[下载八套排版PDF合包](xiao8-typeset-pdfs.zip)。第一、二套各9页，其余各10页，共78页。这里的PDF是重新排版的试卷；原扫描件保留在 `../PDF/`。

导出命令：`python3 x8/scripts/export_pdf.py`。使用当前HTML内嵌打印样式，A4纵向；离线排版器不执行JavaScript，导出脚本按现有选项分列的4/2/1规则，使用打印字体实测文字宽度后分列。未修改HTML内容或样式。字体由HTML字体栈在导出环境中匹配，与其他设备浏览器可能存在细微字形或分页差异。

已检查全部78页缩略图，并查看首页、材料题样页；逐段文字与HTML匹配，没有空白页或越界文字。导出来源哈希、PDF哈希及逐页统计见[scripts/pdf-export.json](../scripts/pdf-export.json)。
