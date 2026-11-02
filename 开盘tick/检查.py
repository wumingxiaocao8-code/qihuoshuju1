"""装好以后检查一遍：包齐不齐、天勤账号能不能连上、标准时间问不问得到、博易云找不找得到。

  python 检查.py
不改任何文件，不读出账号内容（只用来登录天勤）。
"""
import sys

ok = True


def say(good: bool, text: str) -> None:
    global ok
    ok &= good
    print(("✔ " if good else "✘ ") + text)


try:
    import 开盘tick as tick  # 先 import：它会顺带加载日记库 venv 里的包（家里那台电脑）
    import numpy, pandas, PIL, scipy, openpyxl, tqsdk  # noqa: F401,E401
    say(True, f"包都装好了（Python {sys.version.split()[0]}）")
except ImportError as e:
    say(False, f"缺包：{e}（重跑 安装.ps1）")
    sys.exit(1)

import 竞价判断 as jd  # noqa: E402
import 竞价浮层 as fl  # noqa: E402

if not tick.AUTH_FILE.exists():
    say(False, f"没有天勤账号文件 {tick.AUTH_FILE}")
else:
    pairs = fl.board_pairs(fl.read_board())
    sym = pairs[0][0] if pairs else "INE.sc2701"
    try:
        api = tick.connect(tries=1)
        q = api.get_quote(sym)
        api.wait_update(deadline=__import__("time").time() + 10)
        say(True, f"天勤连上了（{sym} 最新价 {q.last_price}）")
        api.close()
    except BaseException as e:  # 账号没填时 load_auth 会 sys.exit
        say(False, f"天勤连不上：{e}")

off, host = jd.clock_offset()
if off is None:
    print("· 没问到标准时间（公司网络挡了 NTP 也能用，按电脑时钟算；记得手动同步时钟）")
else:
    say(abs(off) < jd.CLOCK_WARN, f"电脑时钟{'慢' if off > 0 else '快'} {abs(off):.1f} 秒（问的 {host}；差 {jd.CLOCK_WARN} 秒以上要同步）")

pobo = fl.find_pobo()
say(pobo is not None, "找到博易云窗口" if pobo else "没找到博易云窗口（博易云要开着、不能最小化；进程名要是 pobo.exe）")

print("\n全部通过" if ok else "\n有 ✘ 的项，按 安装说明.md 的「常见问题」处理")
