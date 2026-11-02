# 原生PPTX排版源文件

科组日常修改请直接打开上一级 `PPTX成品/` 中的共享PPTX。本目录用于重建，不要求授课教师安装开发环境。

最新共享文件为 `方程的根与函数的零点_科组共用版_复习导入加强版.pptx`，共35页。它在教师当前保存的PPT上局部替换复习页、插入判别式归纳页，保留后续正文与教师修改。下面34页生成器用于重建初始版本，不能覆盖当前共享成品。

- `生成课件.mjs`：使用 `@oai/artifact-tool` 导入高中园原PPT模板，编排34页原生文字、自由曲线、点、线与表格；写出 `build/pptx/draft.pptx` 及文本、动画配置。
- `紧凑版式.mjs`：收紧页内间距，将短题和端点检验排为左右栏，调整图文位置；由生成器调用，保留34页、公式字号与点击顺序。
- `参考课件样式.mjs`：按用户提供的指数函数PPT设置宋体24pt正文、Cambria Math公式、微软雅黑28pt绿色标题、红色解析、蓝色表格及页内间距，不改内容与动画分组。
- `公式转原生OMML.py`：把指定文本框中的 `$...$` 公式转换为可编辑OMML，按配置显式指定中文字体，数学指定Cambria Math。未知TeX命令报错，不以图片替代。
- `加入点击显示.py`：依据对象名称写入原生Appear动画。每组一次点击，组内同时出现，保留原生文字、公式及图形。
- `人教版定理.mjs`、`定理局部排版.mjs`、`定理局部合并.py`：按用户提供的教材照片替换定理文字，保留现有页面其余对象及动画。定理使用 $c$ 并明确它也是方程的解。
- `复习导入排版.mjs`、`复习导入合并.py`：依据用户的《从函数观点看一元二次方程》课件，编排三组方程与图象、判别式与不同零点个数；仅移植新增原生对象，并更新后续印刷页码。

重建需要Node.js、Codex的 `@oai/artifact-tool` 运行库及带 `lxml` 的Python。可用环境变量 `CODEX_RUNTIME_MODULES` 指定Node依赖目录。生成器从当前仓库读取 `教学课件/高中园模板.pptx`，保留其母版与图标，不改原模板。

在课件目录执行对应命令（将 `node`、`python` 换成已配置的解释器）：

```powershell
node ./PPTX源文件/生成课件.mjs
python ./PPTX源文件/公式转原生OMML.py ./build/pptx/draft.pptx ./build/pptx/math.pptx ./build/pptx/math-spec.json
python ./PPTX源文件/加入点击显示.py ./build/pptx/math.pptx ./build/pptx/pptx-ready.pptx ./build/pptx/reveal-spec.json
```

应在原生公式和动画写入后使用演示软件核查，不再通过缺少数学模型的导入导出过程重写成品。改动解析式时，要独立核查曲线、标签和答案；改变对象后要检查动画引用与点击顺序。

重建参考样式版时，先指定用户提供的原始参考PPT：

```powershell
$env:PPTX_STYLE_REFERENCE='C:/Users/17683/Desktop/4.2.2指数函数的图像与性质.pptx'
node ./PPTX源文件/生成课件.mjs
python ./PPTX源文件/公式转原生OMML.py ./build/pptx-reference/draft.pptx ./build/pptx-reference/math.pptx ./build/pptx-reference/math-spec.json
python ./PPTX源文件/加入点击显示.py ./build/pptx-reference/math.pptx ./build/pptx-reference/pptx-ready.pptx ./build/pptx-reference/reveal-spec.json
```

该分支直接复用参考PPT第1页封面和第4页的书本图标、页眉线、校名页脚，清除指数函数原有文字后填入本课内容。原参考PPT不改动、不另行归档，SHA-256为 `2258e9127efc0bc757b1a0be78488defddbee8a166b359ca4bc6963e349e0a5d`。未设置此环境变量时仍可重建原紧凑版。

## 在当前34页PPT上加强复习导入

先将教师当前保存的34页文件复制到忽略目录 `build/pptx-review/source-current.pptx`。不要从旧生成器重建后再替换，以免丢失教师后续修改。以下命令产生35页候选文件：

```powershell
node ./PPTX源文件/复习导入排版.mjs ./build/pptx-review/source-current.pptx ./build/pptx-review/authored.pptx ./build/pptx-review/math-spec.json
python ./PPTX源文件/公式转原生OMML.py ./build/pptx-review/authored.pptx ./build/pptx-review/authored-math.pptx ./build/pptx-review/math-spec.json
python ./PPTX源文件/复习导入合并.py ./build/pptx-review/source-current.pptx ./build/pptx-review/authored-math.pptx ./build/pptx-review/merged.pptx
python ./PPTX源文件/加入点击显示.py ./build/pptx-review/merged.pptx ./build/pptx-review/candidate.pptx ./build/pptx-review/reveals.json
```

新第3页存放在OOXML的 `slide35.xml` 中，放映顺序由演示文稿关系指定，属于正常结构。动画配置中的35表示该部件编号；课堂页码仍为3。完成后应使用WPS或PowerPoint打开、渲染检查，并核对原第3—34页除页码外保持不变。当前成品包含教师自行调整的教材作业，不能用初始作业页覆盖。
