<#
.SYNOPSIS
    漫画/插画批量超分辨率放大 (基于 Real-ESRGAN ncnn-vulkan, GPU 加速)

.DESCRIPTION
    把 input 文件夹里的图片批量放大后输出到 output 文件夹。
    使用 AMD/Intel/NVIDIA 显卡的 Vulkan 加速，无需 Python。

.PARAMETER Model
    放大模型，可选：
      realesrgan-x4plus-anime   (默认，漫画/插画专用，4倍，质量最佳)
      realesr-animevideov3-x2   (动漫风，2倍，速度快)
      realesr-animevideov3-x3   (动漫风，3倍)
      realesr-animevideov3-x4   (动漫风，4倍，速度快)
      realesrgan-x4plus         (通用照片，4倍)

.PARAMETER Scale
    输出倍数 (2/3/4)。默认 4。
    注意：x4plus 系列模型原生 4 倍，设为 2 会先放大再缩小。
    若想要 2 倍最佳效果，请配合 -Model realesr-animevideov3-x2 使用。

.PARAMETER Format
    输出格式：png (默认，无损，推荐) / jpg / webp

.PARAMETER InputDir / OutputDir
    输入/输出文件夹，默认为脚本同目录下的 input / output

.EXAMPLE
    .\upscale.ps1
    # 用默认设置 (漫画模型, 4倍, 输出png) 处理 input 文件夹所有图片

.EXAMPLE
    .\upscale.ps1 -Model realesr-animevideov3-x2 -Scale 2
    # 2 倍放大，速度更快，适合数量多/图已较大的情况
#>

param(
    [string]$Model     = "realesrgan-x4plus-anime",
    [ValidateSet(2,3,4)][int]$Scale = 4,
    [ValidateSet("png","jpg","webp")][string]$Format = "png",
    [string]$InputDir  = "",
    [string]$OutputDir = ""
)

# 注意: 不能用 Stop。realesrgan 把进度信息打到 stderr,
# 在 Stop 模式下 PowerShell 会把它当致命错误中断。改用 Continue + 手动检查。
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 路径默认值
if (-not $InputDir)  { $InputDir  = Join-Path $root "input" }
if (-not $OutputDir) { $OutputDir = Join-Path $root "output" }
$exe = Join-Path $root "bin\realesrgan-ncnn-vulkan.exe"

# 检查
if (-not (Test-Path $exe))      { Write-Host "[错误] 找不到 $exe" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $InputDir)) { Write-Host "[错误] 输入目录不存在: $InputDir" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $OutputDir)){ New-Item -ItemType Directory -Path $OutputDir | Out-Null }

# 收集图片
$exts = @("*.png","*.jpg","*.jpeg","*.webp","*.bmp")
$files = Get-ChildItem -Path $InputDir -Include $exts -File -Recurse:$false
if (-not $files) {
    # -Include 需要路径带通配，兜底再扫一次
    $files = Get-ChildItem -Path $InputDir -File | Where-Object { $_.Extension -match '\.(png|jpg|jpeg|webp|bmp)$' }
}

if (-not $files -or $files.Count -eq 0) {
    Write-Host "[提示] input 文件夹里没有图片。请把待放大的图片放进：" -ForegroundColor Yellow
    Write-Host "       $InputDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " 漫画批量超分放大" -ForegroundColor Cyan
Write-Host "------------------------------------------------------"
Write-Host " 模型 : $Model"
Write-Host " 倍数 : ${Scale}x"
Write-Host " 格式 : $Format"
Write-Host " 输入 : $InputDir"
Write-Host " 输出 : $OutputDir"
Write-Host " 数量 : $($files.Count) 张"
Write-Host "======================================================" -ForegroundColor Cyan

Add-Type -AssemblyName System.Drawing
$swAll = [System.Diagnostics.Stopwatch]::StartNew()
$ok = 0; $fail = 0; $i = 0

foreach ($f in $files) {
    $i++
    $outName = "$($f.BaseName).$Format"
    $outPath = Join-Path $OutputDir $outName

    # 读取原尺寸
    try {
        $img = [System.Drawing.Image]::FromFile($f.FullName)
        $w0 = $img.Width; $h0 = $img.Height; $img.Dispose()
    } catch { $w0 = "?"; $h0 = "?" }

    Write-Host ""
    Write-Host "[$i/$($files.Count)] $($f.Name)  ($w0 x $h0)" -ForegroundColor White
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    # 工具的进度/显卡信息走 stderr，重定向到 null 保持输出干净
    & $exe -i $f.FullName -o $outPath -n $Model -s $Scale -f $Format 2>$null

    $sw.Stop()
    if (Test-Path $outPath) {
        try {
            $img2 = [System.Drawing.Image]::FromFile($outPath)
            $w1 = $img2.Width; $h1 = $img2.Height; $img2.Dispose()
            Write-Host ("      -> {0} x {1}  ({2:N1}s)" -f $w1, $h1, $sw.Elapsed.TotalSeconds) -ForegroundColor Green
        } catch {
            Write-Host ("      -> 完成 ({0:N1}s)" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green
        }
        $ok++
    } else {
        Write-Host "      -> 失败" -ForegroundColor Red
        $fail++
    }
}

$swAll.Stop()
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host (" 完成: {0} 成功 / {1} 失败 / 总耗时 {2:N1}s" -f $ok, $fail, $swAll.Elapsed.TotalSeconds) -ForegroundColor Cyan
Write-Host " 输出目录: $OutputDir" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
