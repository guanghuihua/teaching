# 原生PPTX排版源文件

科组日常修改请直接打开上一级 `PPTX成品/` 中的共享PPTX。本目录用于重建，不要求授课教师安装开发环境。

- `生成课件.mjs`：使用 `@oai/artifact-tool` 导入高中园原PPT模板，编排34页原生文字、自由曲线、点、线与表格；写出 `build/pptx/draft.pptx` 及文本、动画配置。
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
