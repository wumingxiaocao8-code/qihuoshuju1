"""桌面「重新对看板」双击跑的就是这个（11-10 加）：博易云换了图、改好 看板.txt 之后，不用敲命令。
做三件事：把博易云调到最前面（双击桌面图标时它多半被盖住或最小化了）→ 跑 竞价浮层.py --test → 弹窗说结果。
不改 竞价浮层.py 的任何规则：20:56–21:02、8:56–9:02 不让跑、博易云没开、被挡住，都是它自己判断，这里只把它说的话弹出来。
注意：--test 把屏幕上现在的样子存下来当标准，所以要先把博易云的图和 看板.txt 都改好再双击。"""
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import 竞价浮层 as fl  # noqa: E402  看板.txt 的「只认路径」、查窗口属于哪个程序

TITLE = "重新对看板"
SW_RESTORE, VK_MENU, KEYUP, GW_OWNER = 9, 0x12, 2, 4
u32 = ctypes.WinDLL("user32", use_last_error=True)
ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

u32.EnumWindows.argtypes = [ENUM, wt.LPARAM]
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.IsIconic.argtypes = [wt.HWND]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindow.argtypes = [wt.HWND, ctypes.c_uint]
u32.GetWindow.restype = wt.HWND
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.MessageBoxW.argtypes = [wt.HWND, wt.LPCWSTR, wt.LPCWSTR, wt.UINT]


def iconic_windows(only: str = "") -> list:
    """pobo.exe 里最小化着的窗口，没有主人的（博易云最小化时状态记在它身上）排前面。"""
    found, names = [], {}

    @ENUM
    def cb(h, _):
        if not u32.IsWindowVisible(h) or not u32.IsIconic(h):
            return True
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value not in names:
            names[pid.value] = fl.exe_name(pid.value).lower()
        if os.path.basename(names[pid.value]) == "pobo.exe" and str(only).lower() in names[pid.value]:
            found.append(h)
        return True

    u32.EnumWindows(cb, 0)
    return sorted(found, key=lambda h: bool(u32.GetWindow(h, GW_OWNER)))


def bring_forward() -> bool:
    """把博易云调到最前面。返回有没有找到博易云。
    只对最小化着的窗口用「还原」：对最大化的窗口用它会变成小窗口，窗口大小一变所有格子都不贴（11-10 试出来的）。"""
    only = fl.read_board()["参数"].get("只认路径", "")
    for h in iconic_windows(only):
        u32.ShowWindow(h, SW_RESTORE)
    time.sleep(0.5)
    pobo = fl.find_pobo(only)  # 跟 --test 用同一个办法找主窗口
    if pobo is None:
        return False
    h = pobo[0]
    u32.keybd_event(VK_MENU, 0, 0, 0)  # 按一下 Alt，Windows 才肯让别的窗口到最前面
    u32.keybd_event(VK_MENU, 0, KEYUP, 0)
    u32.BringWindowToTop(h)
    u32.SetForegroundWindow(h)
    time.sleep(0.8)  # 等博易云画完
    return True


def say(text: str, icon: int = 0x40) -> None:
    u32.MessageBoxW(None, text, TITLE, icon | 0x40000)  # 0x40000 = 弹窗在最前面


def main() -> None:
    if not bring_forward():
        say("没找到博易云：先把博易云打开，再双击一次。", 0x30)
        return
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    python = Path(sys.executable).with_name("python.exe")  # 快捷方式用 pythonw 启动（没有黑窗口）；要拿到 --test 说的话得用 python.exe
    r = subprocess.run([str(python), "-u", str(HERE / "竞价浮层.py"), "--test"], cwd=HERE, env=env, capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
    if r.returncode == 0 and "存了" in out:
        say(f"对好了。\n\n{out}\n\n刚才贴的样例标签如果都在对的格子上，就不用管了。")
    else:
        say(f"这次没对成，看下面的原因：\n\n{out or '（没有输出）'}", 0x30)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pythonw 没有黑窗口，出错不弹就什么都看不到
        say(f"出错了，把这段话给 AI 看：\n\n{type(e).__name__}: {e}", 0x10)
