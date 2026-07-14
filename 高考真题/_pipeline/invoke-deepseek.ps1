param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$Model = "deepseek-v4-flash"
)

$ErrorActionPreference = "Stop"

if (-not $env:DEEPSEEK_API_KEY) {
    throw "DEEPSEEK_API_KEY is not set."
}

$source = Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8
$systemPrompt = @'
你是高中数学试卷数字化编辑。请把用户提供的高考数学原卷与解析版提取文本整理成严格 JSON。

要求：
1. 忠实还原题目，不改编、不重新命题，不添加来源中没有的条件。
2. 修复 PDF 文本层造成的数学符号乱码，把公式写成可直接放入 LaTeX 数学环境的字符串。
   每一个数学片段都必须包含完整的数学定界符 `$...$`，包括题干、选项、答案和解析中的集合、区间、坐标、单个变量及公式。
   严禁在数学环境外直接出现 `\\frac`、`\\sqrt`、`\\ge`、`\\le`、`\\cup`、`\\cap`、下标 `_` 或上标 `^`。
3. 删除店铺、微信、网站水印和重复页眉页脚。
4. 输出来源中的全部题目，不得假定题目总数；选择题保留全部选项，多选题类型为 multiple_choice。
5. 解析只整理来源中的【分析】【详解】，不要自行扩写。原文没有内容时保持空字符串。
6. 图片题不要臆造图片内容。在 assets 中写原卷 PAGE 标记对应的 source_page 和 description；不要把图片内容转写成 TikZ。
7. 不能由上下文可靠确认的字符不得猜测：先采用最可信结果，同时把题号和疑点写入 review_notes。
8. 所有反斜杠必须符合 JSON 转义规则。只输出 JSON 对象，不要 Markdown 代码围栏。

JSON 结构：
{
  "title": "试卷标题",
  "year": 2024,
  "paper": "新课标全国I卷",
  "sections": [
    {
      "title": "一、单项选择题",
      "instructions": "本题说明",
      "questions": [
        {
          "number": 1,
          "type": "single_choice|multiple_choice|fill_blank|solution",
          "points": 5,
          "stem_latex": "题干",
          "choices": ["A选项", "B选项", "C选项", "D选项"],
          "answer_latex": "答案",
          "analysis_latex": "分析",
          "solution_latex": "详解",
          "assets": []
        }
      ]
    }
  ],
  "review_notes": [
    {"question": 1, "issue": "具体疑点"}
  ]
}
'@

$userPrompt = @"
下面依次给出带 PAGE 标记的原卷文本层和解析版文本层。请输出 JSON，并利用解析版中的推导修复原卷公式乱码。assets 的 source_page 必须引用原卷的 PAGE 编号，而不是解析版页码。

===== SOURCE START =====
$source
===== SOURCE END =====
"@

$body = @{
    model = $Model
    messages = @(
        @{ role = "system"; content = $systemPrompt }
        @{ role = "user"; content = $userPrompt }
    )
    response_format = @{ type = "json_object" }
    thinking = @{ type = "disabled" }
    max_tokens = 120000
    stream = $false
} | ConvertTo-Json -Depth 12

$headers = @{
    Authorization = "Bearer $($env:DEEPSEEK_API_KEY)"
    "Content-Type" = "application/json"
}

$lastError = $null
for ($attempt = 1; $attempt -le 3; $attempt++) {
    try {
        $response = Invoke-RestMethod `
            -Uri "https://api.deepseek.com/chat/completions" `
            -Method Post `
            -Headers $headers `
            -Body ([Text.Encoding]::UTF8.GetBytes($body)) `
            -TimeoutSec 900

        $content = $response.choices[0].message.content
        if ([string]::IsNullOrWhiteSpace($content)) {
            throw "DeepSeek returned empty content."
        }

        # Windows PowerShell 5 may decode an UTF-8 response as ISO-8859-1 when
        # the server omits a charset. The transformation is reversible.
        if ($content -match "Ã|å|æ|ç|è") {
            $latin1 = [Text.Encoding]::GetEncoding(28591)
            $content = [Text.Encoding]::UTF8.GetString($latin1.GetBytes($content))
        }

        $null = $content | ConvertFrom-Json
        $outputDirectory = Split-Path -Parent $OutputPath
        if ($outputDirectory) {
            New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
        }
        Set-Content -LiteralPath $OutputPath -Value $content -Encoding UTF8

        $usagePath = [IO.Path]::ChangeExtension($OutputPath, ".usage.json")
        $response.usage | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $usagePath -Encoding UTF8
        exit 0
    }
    catch {
        $lastError = $_
        if ($attempt -lt 3) {
            Start-Sleep -Seconds (5 * $attempt)
        }
    }
}

throw $lastError
