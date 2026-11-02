# 原生PPTX排版源文件

科组日常修改请直接打开上一级 `PPTX成品/` 中的共享PPTX。本目录用于重建，不要求授课教师安装开发环境。

- `生成课件.mjs`：使用 `@oai/artifact-tool` 导入高中园原PPT模板，编排34页原生文字、自由曲线、点、线与表格；写出 `build/pptx/draft.pptx` 及文本、动画配置。
- `紧凑版式.mjs`：收紧页内间距，将短题和端点检验排为左右栏，调整图文位置；由生成器调用，保留34页、公式字号与点击顺序。
- `参考课件样式.mjs`：按用户提供的指数函数PPT设置宋体24pt正文、Cambria Math公式、微软雅黑28pt绿色标题、红色解析、蓝色表格及页内间距，不改内容与动画分组。
- `公式转原生OMML.py`：把指定文本框中的 `$...$` 公式转换为可编辑OMML，普通中文显式指定微软雅黑，数学指定Cambria Math。未知TeX命令报错，不以图片替代。
- `加入点击显示.py`：依据对象名称写入原生Appear动画。每组一次点击，组内同时出现，保留原生文字、公式及图形。

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
