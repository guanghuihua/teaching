param([Parameter(Mandatory = $true)][string]$OutputRoot)

$ErrorActionPreference = "Stop"
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)

function Update-PaperJson {
    param([string]$RelativePath, [scriptblock]$Update)
    $path = Join-Path $OutputRoot $RelativePath
    $data = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    & $Update $data
    $data | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
}

Update-PaperJson '2021\2021-新高考II卷\questions.json' {
    param($data)
    $question = @($data.sections.questions) | Where-Object { $_.number -eq 10 }
    $question.solution_latex = @'
设正方体棱长为 $2$。对于 A，连接 $AC$，则 $MN\parallel AC$，而在直角三角形 $OPC$ 中，$OC=\sqrt{2}$，$CP=1$，故 $\tan\angle POC=\frac{1}{\sqrt{2}}$，所以 $MN$ 与 $OP$ 不垂直。对于 B，取 $NT$ 的中点 $Q$，连接 $PQ,OQ$，由 $OQ\perp NT$、$OQ\perp SN$ 可得 $OQ\perp$ 平面 $SNTM$，从而 $OQ\perp MN$；又 $PQ\perp MN$，故 $MN\perp$ 平面 $OPQ$，所以 $MN\perp OP$。对于 C，连接 $BD$，则 $BD\parallel MN$，由 B 中的结论知 $OP\perp BD$，所以 $OP\perp MN$。对于 D，平移 $MN$ 后考查相应异面直线所成角，由长度关系可知该角不是直角。因此正确选项为 BC。
'@
}

Update-PaperJson '2019\2019-全国II卷-文科\questions.json' {
    param($data)
    $question = @($data.sections.questions) | Where-Object { $_.number -eq 19 }
    $question.stem_latex = @'
某行业主管部门为了解本行业中小企业的生产情况，随机调查了 $100$ 个企业，得到这些企业第一季度相对于前一年第一季度产值增长率 $y$ 的频数分布表．
\begin{center}
\begin{tabular}{c|ccccc}
$y$ 的分组 & $[-0.20,0)$ & $[0,0.20)$ & $[0.20,0.40)$ & $[0.40,0.60)$ & $[0.60,0.80)$ \\ \hline
企业数 & $2$ & $24$ & $53$ & $14$ & $7$
\end{tabular}
\end{center}
（1）分别估计这类企业中产值增长率不低于 $40\%$ 的企业比例、产值负增长的企业比例；

（2）求这类企业产值增长率的平均数与标准差的估计值（同一组中的数据用该组区间的中点值为代表）．（精确到 $0.01$）

附：$\sqrt{74}\approx8.602$．
'@
    $question.solution_latex = $question.solution_latex.Replace(']$$=', ']=')
}

Update-PaperJson '2016\2016-全国III卷-理科\questions.json' {
    param($data)
    $question = @($data.sections.questions) | Where-Object { $_.number -eq 13 }
    $question.answer_latex = '\(\frac{3}{2}\)'
}

Update-PaperJson '2024\2024-天津卷\questions.json' {
    param($data)
    $q10 = @($data.sections.questions) | Where-Object { $_.number -eq 10 }
    $q10.stem_latex = '已知 $i$ 是虚数单位，复数 $(\sqrt{5}+i)(\sqrt{5}-2i)=$ \_\_\_\_\_\_．'
    $q10.answer_latex = '$7-\sqrt{5}i$'
    $q10.analysis_latex = '直接利用复数乘法法则计算。'
    $q10.solution_latex = '$(\sqrt{5}+i)(\sqrt{5}-2i)=5-2\sqrt{5}i+\sqrt{5}i-2i^2=7-\sqrt{5}i$。'

    $q11 = @($data.sections.questions) | Where-Object { $_.number -eq 11 }
    $q11.stem_latex = '在 $\left(\frac{3}{x^3}+\frac{x^3}{3}\right)^6$ 的展开式中，常数项为 \_\_\_\_\_\_．'
    $q11.answer_latex = '$20$'
    $q11.analysis_latex = '写出二项展开式的通项，令 $x$ 的指数为零。'
    $q11.solution_latex = '通项为 $T_{r+1}=\binom{6}{r}\left(\frac{3}{x^3}\right)^{6-r}\left(\frac{x^3}{3}\right)^r=\binom{6}{r}3^{6-2r}x^{6r-18}$。令 $6r-18=0$，得 $r=3$，所以常数项为 $\binom{6}{3}=20$。'
}
