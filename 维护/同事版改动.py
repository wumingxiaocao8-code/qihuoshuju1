"""发布新版本.ps1 复制完文件后跑：把作者版有、同事版不要的规则改掉（11-07 加）。找不到要改的那一行就报错停下，不发布。
现在改的：
  - 有「腿2」时色块直接关（作者版 ru ag br cu）→ 同事版不关，照通用的写「小」
  - fu 小针 → 同事版不用（11-08 起作者版也关了，这条留着保险）
  - 说明.md 开头加一段写清楚不一样的地方
用法：python 同事版改动.py <仓库里的 开盘tick 文件夹>"""
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
T = Path(sys.argv[1])
RULES = [
    ("竞价浮层.py", r"^OFF_WHEN_LEG2 = [^\r\n]*",
     'OFF_WHEN_LEG2 = ()  # 同事版：有「腿2」不直接关，照通用的写「小」（作者版 ru ag br cu 关）；发布时由 维护/同事版改动.py 改'),
    ("竞价判断.py", r"^SMALL = \{[^\r\n]*",
     'SMALL = {}  # 同事版：不用燃料油小针（11-08 起作者版也关了）；发布时由 维护/同事版改动.py 改'),
]
NOTE = ("> **同事版和作者版不一样的地方**（发布时自动改的）：有「腿2」时色块一律写「小」，不会因为品种直接「关」。"
        "下面正文如果写到这一条，以这里为准。")


def read(p: Path) -> str:
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write_atomic(p: Path, s: str) -> None:
    """先写同目录临时文件再替换，写到一半出错也不会留下空文件（11-07 审查）。"""
    tmp = p.with_name(p.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    os.replace(tmp, p)


def add_note(s: str) -> str:
    if NOTE in s:
        return s
    nl = "\r\n" if "\r\n" in s else "\n"
    first, rest = s.split(nl, 1)
    return first + nl + nl + NOTE + nl + rest


# 先把所有文件都改好放在内存里，全部找得到要改的行才一起写回；有一处找不到就一个都不动
out: dict[Path, str] = {}
for name, pat, new in RULES:
    p = T / name
    s = out.get(p) or read(p)
    s2, n = re.subn(pat, lambda m: new, s, count=1, flags=re.M)
    if n != 1:
        sys.exit(f"✘ {name} 里找不到要改的那一行（{pat}），先看看作者版是不是改了写法；文件都没动")
    out[p] = s2
p = T / "说明.md"
out[p] = add_note(out.get(p) or read(p))
for p, s in out.items():
    write_atomic(p, s)
print("✔ 同事版改动：腿2 不直接关、没有 fu 小针、说明.md 加了说明")
