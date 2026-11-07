"""发布新版本.ps1 复制完文件后跑：把作者版有、同事版不要的规则改掉（11-07 加）。找不到要改的那一行就报错停下，不发布。
现在改的：
  - 有「腿2」时色块直接关（作者版 ru ag br cu）→ 同事版不关，照通用的写「小」
  - fu 小针 → 同事版不用
  - 说明.md 开头加一段写清楚这两处不一样
用法：python 同事版改动.py <仓库里的 开盘tick 文件夹>"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
T = Path(sys.argv[1])
RULES = [
    ("竞价浮层.py", r"^OFF_WHEN_LEG2 = [^\r\n]*",
     'OFF_WHEN_LEG2 = ()  # 同事版：有「腿2」不直接关，照通用的写「小」（作者版 ru ag br cu 关）；发布时由 维护/同事版改动.py 改'),
    ("竞价判断.py", r"^SMALL = \{[^\r\n]*",
     'SMALL = {}  # 同事版：不用燃料油小针（作者版 fu 12 档）；发布时由 维护/同事版改动.py 改'),
]
NOTE = ("> **同事版和作者版不一样的地方**（发布时自动改的）：有「腿2」时色块一律写「小」，不会因为品种直接「关」；"
        "没有燃料油「小针」。下面正文如果写到这两条，以这里为准。")


def rw(p: Path, fn) -> None:
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read()
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(fn(s))


for name, pat, new in RULES:
    def sub(s, pat=pat, new=new, name=name):
        s2, n = re.subn(pat, lambda m: new, s, count=1, flags=re.M)
        if n != 1:
            sys.exit(f"✘ {name} 里找不到要改的那一行（{pat}），先看看作者版是不是改了写法")
        return s2
    rw(T / name, sub)


def add_note(s: str) -> str:
    if NOTE in s:
        return s
    nl = "\r\n" if "\r\n" in s else "\n"
    first, rest = s.split(nl, 1)
    return first + nl + nl + NOTE + nl + rest


rw(T / "说明.md", add_note)
print("✔ 同事版改动：腿2 不直接关、没有 fu 小针、说明.md 加了说明")
