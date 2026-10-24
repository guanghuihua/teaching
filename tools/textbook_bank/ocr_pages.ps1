param([string]$InputDirectory,[string]$OutputDirectory,[int]$First=1,[int]$Last=281)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
$taskMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Await-Result($Operation,[type]$ResultType) {
 $task=$taskMethod.MakeGenericMethod($ResultType).Invoke($null,@($Operation)); $task.Wait(); return $task.Result
}
$lang=[Windows.Globalization.Language]::new('zh-Hans-CN')
$engine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
foreach($n in $First..$Last) {
 $name=('{0:D3}' -f $n); $out=Join-Path $OutputDirectory ($name+'.json')
 if(Test-Path -LiteralPath $out){continue}
 $path=Join-Path $InputDirectory ($name+'.png')
 if(!(Test-Path -LiteralPath $path)){continue}
 $file=Await-Result ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
 $stream=Await-Result ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
 $decoder=Await-Result ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
 $bitmap=Await-Result ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
 $result=Await-Result ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
 $lines=@($result.Lines | ForEach-Object {
  $words=@($_.Words | ForEach-Object { @{text=$_.Text;x=$_.BoundingRect.X;y=$_.BoundingRect.Y;width=$_.BoundingRect.Width;height=$_.BoundingRect.Height} })
  @{text=$_.Text;words=$words}
 })
 $record=@{page=$n;width=$bitmap.PixelWidth;height=$bitmap.PixelHeight;engine='Windows.Media.Ocr zh-Hans-CN';text=$result.Text;lines=$lines}
 [IO.File]::WriteAllText($out,($record|ConvertTo-Json -Depth 9),[Text.UTF8Encoding]::new($false))
 $bitmap.Dispose();$stream.Dispose()
 Write-Output ('OCR '+$name+' lines='+$lines.Count)
}
