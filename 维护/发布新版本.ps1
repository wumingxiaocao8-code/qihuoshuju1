# 作者用：把家里 期货数据\开盘tick 的最新程序和种子同步进本仓库，写一条更新记录，提交并推到 GitHub。同事不用管这个文件。
# 运行：powershell -ExecutionPolicy Bypass -File 维护\发布新版本.ps1 -Message "这次改了什么（一两句，给同事看）"
# 只发下面列的文件；数据/、开盘复盘.csv、成交、账号、自己的看板.txt 不发（看板.txt 只作为 看板.示例.txt 发）。
param(
    [Parameter(Mandatory = $true)][string]$Message,
    [string]$From = (Join-Path $HOME "Desktop\期货数据\开盘tick")
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$To = Join-Path $Repo "开盘tick"
if (-not (Test-Path (Join-Path $From "竞价判断.py"))) { Write-Host "✘ 找不到 $From\竞价判断.py" -ForegroundColor Red; exit 1 }

$files = @("竞价判断.py", "竞价浮层.py", "关浮层.pyw", "开盘tick.py", "开盘复盘.py", "成交模型.py", "开盘预估.py", "外盘涨跌.py", "说明.md")  # 成交模型.py：开盘复盘.py 的排队版模拟要用（11-05 加）
foreach ($f in $files) { Copy-Item (Join-Path $From $f) (Join-Path $To $f) -Force }
Copy-Item (Join-Path $From "看板.txt") (Join-Path $To "看板.示例.txt") -Force
Get-ChildItem (Join-Path $From "复盘数据") -File | Where-Object { $_.Name -like "两年回放_*.csv" -or $_.Name -eq "腿2盘口_sc.csv" } |
    ForEach-Object { Copy-Item $_.FullName (Join-Path $To "复盘数据\$($_.Name)") -Force }

Push-Location $Repo
git add -A
$changed = git diff --cached --name-only
if (-not $changed) { Write-Host "没有变化，不用发布"; Pop-Location; exit 0 }

# 更新记录.md：在「# 更新记录」说明段后面插一条
$log = Join-Path $Repo "更新记录.md"
$lines = [System.Collections.Generic.List[string]](Get-Content $log -Encoding UTF8)
$at = ($lines | Select-String -Pattern "^## " | Select-Object -First 1).LineNumber - 1
if ($at -lt 0) { $at = $lines.Count }
$lines.InsertRange($at, [string[]]@("## $(Get-Date -Format 'yyyy-MM-dd HH:mm')", "", "- $Message", ""))
[IO.File]::WriteAllLines($log, $lines, (New-Object Text.UTF8Encoding $false))
git add -A

Write-Host "这次要发布的文件："; git diff --cached --stat
git commit -q -m "$Message"
git push
$ok = $LASTEXITCODE -eq 0
Pop-Location
if ($ok) { Write-Host "✔ 已推到 GitHub。同事跟自己的 AI 说「更新开盘指标」即可" } else { Write-Host "✘ 推送失败，看上面的报错" -ForegroundColor Red; exit 1 }
