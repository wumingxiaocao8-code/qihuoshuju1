# 作者用：把家里 期货数据\开盘tick 的最新程序和种子同步进本仓库，写一条更新记录，提交并推到 GitHub。同事不用管这个文件。
# 运行：powershell -ExecutionPolicy Bypass -File 维护\发布新版本.ps1 -Message "这次改了什么（一两句，给同事看）"
# 只发下面列的文件；数据/、开盘复盘.csv、成交、账号、自己的看板.txt 不发（看板.txt 只作为 看板.示例.txt 发）。
# 11-07 按审查改：只暂存白名单里的文件，暂存区有白名单外的就停；每步 git 都看成败；上次推送失败、这次没新改动时直接补推。
param(
    [Parameter(Mandatory = $true)][string]$Message,
    [string]$From = (Join-Path $HOME "Desktop\期货数据\开盘tick")
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false  # git 输出的中文文件名按 UTF-8 读
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$To = Join-Path $Repo "开盘tick"
if (-not (Test-Path (Join-Path $From "竞价判断.py"))) { Write-Host "✘ 找不到 $From\竞价判断.py" -ForegroundColor Red; exit 1 }

function Fail($msg) { Write-Host "✘ $msg" -ForegroundColor Red; Pop-Location -ErrorAction SilentlyContinue; exit 1 }
function Git-Ok { & git -c core.quotepath=false @args; if ($LASTEXITCODE -ne 0) { Fail "git $($args -join ' ') 失败（退出码 $LASTEXITCODE），没发布" } }
function Staged { @(& git -c core.quotepath=false diff --cached --name-only) | Where-Object { $_ } }

$files = @("竞价判断.py", "竞价浮层.py", "关浮层.pyw", "开盘tick.py", "开盘复盘.py", "成交模型.py", "开盘预估.py", "外盘涨跌.py", "主力表.py", "说明.md")  # 成交模型.py：开盘复盘.py 的排队版模拟要用（11-05 加）；主力表.py：换月看成交量、自己下上期所每日行情（11-07 加）
# 允许发布的路径（相对仓库，/ 分隔）；种子按名字匹配
$allow = @($files | ForEach-Object { "开盘tick/$_" }) + @("开盘tick/看板.示例.txt", "更新记录.md")
$allowLike = @("开盘tick/复盘数据/两年回放_*.csv", "开盘tick/复盘数据/腿2盘口_sc.csv")
function Allowed($p) { if ($allow -contains $p) { return $true }; foreach ($w in $allowLike) { if ($p -like $w) { return $true } }; return $false }
function Check-Staged {
    $bad = @(Staged | Where-Object { -not (Allowed $_) })
    if ($bad.Count) { Fail ("暂存区里有不在发布清单里的文件，先处理掉再发布（git restore --staged <文件>）：`n  " + ($bad -join "`n  ")) }
}

Push-Location $Repo
Check-Staged  # 发布前就暂存着别的东西，也不带走

foreach ($f in $files) { Copy-Item (Join-Path $From $f) (Join-Path $To $f) -Force }
Copy-Item (Join-Path $From "看板.txt") (Join-Path $To "看板.示例.txt") -Force
$seeds = @(Get-ChildItem (Join-Path $From "复盘数据") -File | Where-Object { $_.Name -like "两年回放_*.csv" -or $_.Name -eq "腿2盘口_sc.csv" })
foreach ($s in $seeds) { Copy-Item $s.FullName (Join-Path $To "复盘数据\$($s.Name)") -Force }
# 作者版有、同事版不要的规则（有腿2 直接关、fu 小针）在这里改回来（11-07 加，见 维护\同事版改动.py；找不到要改的行时一个文件都不动）
$py = Join-Path $HOME "AppData\Roaming\uv\python\cpython-3.13.16-windows-x86_64-none\python.exe"
& $py (Join-Path $Repo "维护\同事版改动.py") $To
if ($LASTEXITCODE -ne 0) { Fail "同事版改动没做成，没发布" }

$paths = @($allow | Where-Object { $_ -ne "更新记录.md" }) + @($seeds | ForEach-Object { "开盘tick/复盘数据/$($_.Name)" })
Git-Ok add "--" @paths
$changed = @(Staged)
if (-not $changed.Count) {
    # 没有新改动：看看是不是上次提交了但没推上去
    $ahead = & git rev-list --count "@{u}..HEAD"
    if ($LASTEXITCODE -ne 0) { Fail "查不到本地比 GitHub 多几个提交（没有上游分支？）" }
    if ([int]$ahead -eq 0) { Write-Host "没有变化，不用发布"; Pop-Location; exit 0 }
    Write-Host "没有新改动，但有 $ahead 个提交上次没推上去，现在补推："
    Git-Ok log --oneline "@{u}..HEAD"
    Git-Ok push
    Pop-Location
    Write-Host "✔ 已推到 GitHub。同事跟自己的 AI 说「更新开盘指标」即可"
    exit 0
}

# 更新记录.md：在「# 更新记录」说明段后面插一条
$log = Join-Path $Repo "更新记录.md"
$lines = [System.Collections.Generic.List[string]](Get-Content $log -Encoding UTF8)
$at = ($lines | Select-String -Pattern "^## " | Select-Object -First 1).LineNumber - 1
if ($at -lt 0) { $at = $lines.Count }
$lines.InsertRange($at, [string[]]@("## $(Get-Date -Format 'yyyy-MM-dd HH:mm')", "", "- $Message", ""))
[IO.File]::WriteAllLines($log, $lines, (New-Object Text.UTF8Encoding $false))
Git-Ok add "--" "更新记录.md"
Check-Staged

Write-Host "这次要发布的文件："; Git-Ok diff --cached --stat
Git-Ok commit -q -m "$Message"
& git push
if ($LASTEXITCODE -ne 0) { Fail "推送失败，看上面的报错。已经提交在本地了，网络好了照原命令再跑一次就会补推" }
Pop-Location
Write-Host "✔ 已推到 GitHub。同事跟自己的 AI 说「更新开盘指标」即可"
