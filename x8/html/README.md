# 肖八 HTML 试卷

打开[index.html](index.html)进入八套目录。每套均为独立HTML，样式和脚本已内嵌，正文阅读不依赖外部资源。原卷、Markdown和校对记录的链接使用项目内相对路径。

字体族与 `papers/html` 保持一致：宋体正文、黑体标题；按照设备已有字体依次匹配 SimSun、Songti SC 等。调整正文显示字号、字重、行距和标题层次，保持纯黑白试卷样式，不模拟肖八扫描件字形，不通过描边处理文字。

生成命令：`python3 x8/scripts/build_html.py`。需Python 3及beautifulsoup4。全部304题与校订Markdown逐题逐字核验，共1056个选项标签和40道材料分析题；结果保存在[scripts/html-verification.json](../scripts/html-verification.json)。

本环境的浏览器无法打开本地文件，浏览器交互、手机实机显示及浏览器打印分页尚未验证。已用离线HTML排版器检查第一、八套页面的正文、材料和末页；离线排版器不执行选项分列脚本，不能代替浏览器检查。自适应分列与留白逻辑复用现有真题脚本。
