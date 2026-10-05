r"""
win_fix.py  v1.3.3
WinFix — ремонт Windows после «сборок»: курсор, звуки входа, автозагрузка
(музыка при входе), проверка реестра, открытые порты, DISM/SFC.

Журнал:
v1.3.3: исправления по полному анализу: QSS + QPalette для всех окон (QFileDialog, списки, комбо — без
        светлого текста на светлом); лог перекрашивается при смене темы; цвета статусов под тему;
        EXE без uac_admin (права просит сама программа, --selftest в build_exe.bat не падает);
        удаление из автозагрузки — shutil.move + уникальное имя (работает между дисками);
        тумблер мелодии и размер курсора не «врут», если действие не выполнилось (размер — с задержкой);
        цепочки действий (исправить → проверить) без гонки — Worker(then=…);
        точка восстановления создаётся всегда (обход лимита 24 ч) и проверяется;
        восстановленные курсоры — владелец TrustedInstaller и исходные права;
        статус курсора считает «чужими» только ✗; подтверждение выхода во время работы;
        в вопросах по умолчанию «Нет»; Проводник перезапускается без прав админа;
        «Папка процесса»/«Завершить» — в фоне; regedit: любой язык, HKU/HKCR, /m;
        IFEO — пропуск замены диспетчера на Process Explorer/System Informer; hosts — чужие строки
        комментируются, а не стираются; автозагрузка: Policies\Run, службы, Active Setup;
        проверка Defender: DisableRealtimeMonitoring; --selftest создаёт окно и применяет обе темы.
v1.3.2: окна вопросов/сообщений (QMessageBox) в цветах темы — текст был не читаем;
        курсоры *_eoa.cur из AppData\Local\Microsoft\Windows\Cursors — это файлы самой Windows
        (Специальные возможности), больше не помечаются «чужое».
v1.3.1: курсор: «🧩 Восстановить файлы» — оригиналы из хранилища WinSxS копируются обратно в
        C:\Windows\Cursors (сверка по SHA256, takeown/icacls), т.к. SFC эти файлы может не вернуть;
        владелец в логе — имя учётки вместо SID, без «O:».
v1.3.0: курсор: размер указателя 1–15 (Stepper [−][+], как в Параметрах), применяется сразу;
        кнопка «Параметры указателя»; виджет Stepper.
v1.2.1: курсор: сброс на встроенные курсоры Windows (пустые значения), т.к. сборка подменяет сами
        файлы aero_* в C:\Windows\Cursors; проверка подмены файлов (владелец не TrustedInstaller);
        сброс и для экрана входа (HKU\.DEFAULT). Исправлено открытие «Свойства мыши» и других .cpl/.msc
        (через control.exe / mmc.exe, запасной вариант — Параметры), ошибки открытия пишутся в лог.
v1.2.0: подробные логи для отладки: logs/win_fix.log (DEBUG: команды, коды, вывод, реестр, traceback),
        шапка сессии, перехват падений (sys/threading/Qt), время действий, тумблер «подробно в окне»,
        меню лога: открыть файл / папку логов.
v1.1.0: боковая панель с вкладками (иконка + название), сворачивание ☰, состояние сохраняется.
v1.0.0: первая версия — 6 страниц + тема, контекстные меню, лог, авто-права админа.
"""
from __future__ import annotations

import base64
import csv
import ctypes
import importlib
import importlib.util
import io
import json
import logging
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_NAME = "WinFix"
VERSION = "1.3.3"
IS_WIN = os.name == "nt"
NOWIN = 0x08000000 if IS_WIN else 0
FROZEN = getattr(sys, "frozen", False)
APP_ROOT = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config.json"
LOG_DIR = APP_ROOT / "logs"
LOG_PATH = LOG_DIR / "win_fix.log"
WINDIR = os.environ.get("SystemRoot", r"C:\Windows")

REQUIRED = (("PySide6", "PySide6>=6.5"),)


# ───────────────────────── авто-установка библиотек ─────────────────────────
def _msgbox(text: str, title: str = APP_NAME) -> None:
    if IS_WIN:
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)
    else:
        print(f"{title}: {text}")


def _python_exe() -> str:
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe" and exe.with_name("python.exe").exists():
        return str(exe.with_name("python.exe"))
    return str(exe)


def pip_install(pips, console: bool = True) -> bool:
    py = _python_exe()
    flags = 0x10 if (console and IS_WIN) else NOWIN
    quiet = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if subprocess.call([py, "-m", "pip", "--version"], creationflags=NOWIN, **quiet) != 0:
        subprocess.call([py, "-m", "ensurepip", "--upgrade"], creationflags=flags)
    base = [py, "-m", "pip", "install", "--disable-pip-version-check"]
    ok = subprocess.call(base + list(pips), creationflags=flags) == 0
    if not ok:
        ok = subprocess.call(base + ["--user"] + list(pips), creationflags=flags) == 0
    importlib.invalidate_caches()
    return ok


def ensure_packages() -> None:
    if FROZEN or "--selftest" in sys.argv:
        return
    miss = [pip for mod, pip in REQUIRED if importlib.util.find_spec(mod) is None]
    if not miss:
        return
    pip_install(miss)
    if any(importlib.util.find_spec(m) is None for m, _ in REQUIRED):
        _msgbox("Не удалось установить библиотеки:\n" + "\n".join(miss)
                + "\n\nУстановите вручную:\npip install " + " ".join(miss))
        sys.exit(1)


ensure_packages()

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt, QTimer, Signal  # noqa: E402
from PySide6.QtGui import (QAction, QColor, QFont, QGuiApplication, QPainter,  # noqa: E402
                           QPalette, QTextCharFormat, QTextCursor)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication,  # noqa: E402
                               QButtonGroup, QFileDialog, QFrame, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu,
                               QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
                               QStackedWidget, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

try:
    import winreg as wr
except ImportError:  # не Windows (тесты)
    wr = None


# ───────────────────────── конфиг и лог ─────────────────────────
DEFAULT_CONFIG = {"theme": "dark", "geometry": "", "splitter": "", "page": 0, "ports_listen_only": True, "side_collapsed": False, "log_verbose": False}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        cfg.update(json.loads(CONFIG_PATH.read_text("utf-8")))
    except Exception:
        pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass


LOGQ: "queue.Queue" = queue.Queue()
_DONE_SENTINEL = object()


class _QueueHandler(logging.Handler):
    def emit(self, record):
        rec = logging.makeLogRecord(record.__dict__)
        rec.exc_info = rec.exc_text = None
        msg = self.format(rec)
        if record.levelno <= logging.DEBUG:
            msg = msg.replace("  ", "  · ", 1)
        LOGQ.put(msg)


_SECRET_RE = re.compile(r"(?i)(password|pass|token|key)=\S+")


class _MaskFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = _SECRET_RE.sub(r"\1=***", record.msg)
        return True


log = logging.getLogger("winfix")
log.setLevel(logging.DEBUG)
log.addFilter(_MaskFilter())
_qh = _QueueHandler()
_qh.setLevel(logging.INFO)
_qh.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
log.addHandler(_qh)
try:
    LOG_DIR.mkdir(exist_ok=True)
    _fh = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)-7s [%(threadName)s] %(funcName)s: "
                                       "%(message)s", "%Y-%m-%d %H:%M:%S"))
    log.addHandler(_fh)
except Exception:
    _fh = None


def set_verbose(on: bool) -> None:
    _qh.setLevel(logging.DEBUG if on else logging.INFO)


def _short(text: str, n: int = 1500) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n] + f" …[+{len(text) - n} симв.]"


def log_session_start() -> None:
    import platform
    log.debug("=" * 70)
    log.info(f"{APP_NAME} v{VERSION} запуск")
    log.debug(f"Python {sys.version.split()[0]} · {platform.platform()} · frozen={FROZEN} · admin={is_admin()}")
    log.debug(f"APP_ROOT={APP_ROOT} · argv={sys.argv}")


def install_crash_hooks() -> None:
    import traceback

    def hook(et, ev, tb):
        log.critical("⛔ Необработанная ошибка: " + "".join(traceback.format_exception(et, ev, tb)))
    sys.excepthook = hook
    threading.excepthook = lambda a: hook(a.exc_type, a.exc_value, a.exc_traceback)


def ui(fn) -> None:
    """Выполнить fn в UI-потоке."""
    LOGQ.put(fn)


# ───────────────────────── система: процессы, PowerShell ─────────────────────────
def _oem() -> str:
    try:
        return f"cp{ctypes.windll.kernel32.GetOEMCP()}" if IS_WIN else "utf-8"
    except Exception:
        return "cp866"


def _decode(b: bytes) -> str:
    if not b:
        return ""
    if b.count(b"\x00") > len(b) // 4:
        return b.decode("utf-16-le", "replace")
    for enc in ("utf-8", _oem(), "cp866", "cp1251"):
        try:
            return b.decode(enc)
        except (UnicodeDecodeError, LookupError):
            pass
    return b.decode("cp1251", "replace")


def run_cmd(args, timeout: int = 120, label: str = ""):
    t0 = time.time()
    log.debug(f"$ {label or ' '.join(map(str, args))}")
    r = subprocess.run(args, capture_output=True, timeout=timeout, creationflags=NOWIN)
    out, err = _decode(r.stdout), _decode(r.stderr)
    log.debug(f"  → код {r.returncode} за {time.time() - t0:.1f} с"
              + (f"\n  stdout: {_short(out)}" if out.strip() else "")
              + (f"\n  stderr: {_short(err)}" if err.strip() else ""))
    return r.returncode, out, err


def run_ps(script: str, timeout: int = 120):
    pre = "[Console]::OutputEncoding=[Text.Encoding]::UTF8;$ProgressPreference='SilentlyContinue';"
    enc = base64.b64encode((pre + script).encode("utf-16-le")).decode()
    return run_cmd(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-EncodedCommand", enc], timeout, label="PS> " + _short(script, 600))


def run_stream(args, on_line) -> int:
    """Потоковый вывод (DISM/SFC). SFC пишет в UTF-16 — определяем сами."""
    log.debug(f"$ {' '.join(args)}  (поток)")
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=NOWIN)
    head = p.stdout.peek(256)[:256]
    enc = "utf-16-le" if head.count(b"\x00") > len(head) // 4 else _oem()
    last_pct = 0.0
    for line in io.TextIOWrapper(p.stdout, encoding=enc, errors="replace", newline=None):
        line = line.replace("\x00", "").strip()
        if not line or set(line) <= set("=[]. "):
            continue
        if "%" in line:
            if time.time() - last_pct < 2:
                log.debug(f"  {line}")
                continue
            last_pct = time.time()
        on_line(line)
    return p.wait()


def ps_quote(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate() -> bool:
    if FROZEN:
        exe, params = sys.executable, "--no-admin"
    else:
        pyw = Path(sys.executable).with_name("pythonw.exe")
        exe = str(pyw if pyw.exists() else sys.executable)
        params = f'"{Path(__file__).resolve()}" --no-admin'
    return ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1) > 32


FALLBACK = {"main.cpl": "ms-settings:mousetouchpad", "mmsys.cpl": "ms-settings:sound",
            "appwiz.cpl": "ms-settings:appsfeatures"}


def _shell_exec(verb, target, args) -> int:
    r = ctypes.windll.shell32.ShellExecuteW(None, verb, target, args or None, None, 1)
    log.debug(f"ShellExecute {verb} {target} {args} → {r}")
    return r


def shell_open(target: str, args: str = "", admin: bool = False) -> None:
    if not IS_WIN:
        log.info(f"(не Windows) открыть: {target} {args}")
        return
    low = target.lower()
    verb = "runas" if admin else "open"
    if low.endswith(".cpl"):
        path = os.path.join(WINDIR, "System32", "control.exe")
        r = _shell_exec(verb, path, f"{target} {args}".strip())
    elif low.endswith(".msc"):
        r = _shell_exec(verb, os.path.join(WINDIR, "System32", "mmc.exe"), f"{target} {args}".strip())
    else:
        r = _shell_exec(verb, target, args)
    if r <= 32 and low in FALLBACK:
        log.warning(f"⚠ {target} не открылся (код {r}) — открываю Параметры")
        r = _shell_exec("open", FALLBACK[low], "")
    if r <= 32:
        log.error(f"✗ Не удалось открыть {target} (код {r})")


def exe_from_cmd(cmd: str) -> str:
    cmd = os.path.expandvars((cmd or "").strip())
    if cmd.startswith('"'):
        return cmd[1:].split('"', 1)[0]
    m = re.match(r"(.+?\.(exe|bat|cmd|vbs|js|ps1|lnk|mp3|wav|wma|ogg|flac|m4a))\b", cmd, re.I)
    return m.group(1) if m else cmd.split(" ")[0]


def show_in_explorer(path: str) -> None:
    path = exe_from_cmd(path)
    if path and os.path.exists(path):
        subprocess.Popen(["explorer", "/select,", path], creationflags=NOWIN)
    else:
        log.warning(f"⚠ Файл не найден: {path}")


# ───────────────────────── реестр ─────────────────────────
HK = {"HKCU": wr.HKEY_CURRENT_USER, "HKLM": wr.HKEY_LOCAL_MACHINE,
      "HKCR": wr.HKEY_CLASSES_ROOT, "HKU": wr.HKEY_USERS} if wr else {}
W64 = 0x0100


def _need_reg():
    if not wr:
        raise RuntimeError("реестр доступен только в Windows")


def reg_get(root, path, name):
    if not wr:
        return None
    try:
        with wr.OpenKey(HK[root], path, 0, wr.KEY_READ | W64) as k:
            return wr.QueryValueEx(k, name)[0]
    except OSError:
        return None


def reg_set(root, path, name, value, typ=None):
    _need_reg()
    if typ is None:
        typ = wr.REG_DWORD if isinstance(value, int) else wr.REG_BINARY if isinstance(value, bytes) else wr.REG_SZ
    old = reg_get(root, path, name)
    with wr.CreateKeyEx(HK[root], path, 0, wr.KEY_SET_VALUE | W64) as k:
        wr.SetValueEx(k, name, 0, typ, value)
    log.debug(f"REG SET {root}\\{path} [{name or '(по умолч.)'}]: {old!r} → {value!r}")


def reg_del(root, path, name) -> bool:
    _need_reg()
    try:
        with wr.OpenKey(HK[root], path, 0, wr.KEY_SET_VALUE | W64) as k:
            old = reg_get(root, path, name)
            wr.DeleteValue(k, name)
        log.debug(f"REG DEL {root}\\{path} [{name}] (было {old!r})")
        return True
    except FileNotFoundError:
        log.debug(f"REG DEL {root}\\{path} [{name}] — нет значения")
        return False


def reg_values(root, path):
    out = []
    if not wr:
        return out
    try:
        with wr.OpenKey(HK[root], path, 0, wr.KEY_READ | W64) as k:
            i = 0
            while True:
                try:
                    out.append(wr.EnumValue(k, i))
                except OSError:
                    break
                i += 1
    except OSError:
        pass
    return out


def reg_subkeys(root, path):
    out = []
    if not wr:
        return out
    try:
        with wr.OpenKey(HK[root], path, 0, wr.KEY_READ | W64) as k:
            i = 0
            while True:
                try:
                    out.append(wr.EnumKey(k, i))
                except OSError:
                    break
                i += 1
    except OSError:
        pass
    return out


def reg_key_exists(root, path) -> bool:
    if not wr:
        return False
    try:
        wr.OpenKey(HK[root], path, 0, wr.KEY_READ | W64).Close()
        return True
    except OSError:
        return False


def reg_delete_tree(root, path) -> None:
    _need_reg()
    log.debug(f"REG DELTREE {root}\\{path}")
    ctypes.windll.advapi32.RegDeleteTreeW(HK[root], path)
    wr.DeleteKey(HK[root], path) if reg_key_exists(root, path) else None


HK_FULL = {"HKCU": "HKEY_CURRENT_USER", "HKLM": "HKEY_LOCAL_MACHINE", "HKCR": "HKEY_CLASSES_ROOT",
           "HKU": "HKEY_USERS"}
REGEDIT_KEY = r"Software\Microsoft\Windows\CurrentVersion\Applets\Regedit"


def _regedit_root() -> str:
    """Корень в адресной строке regedit («Компьютер» / «Computer» …) — зависит от языка Windows."""
    last = reg_get("HKCU", REGEDIT_KEY, "LastKey") or ""
    if "\\HKEY_" in last:
        return last.split("\\HKEY_", 1)[0]
    try:
        ru = (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x19
    except Exception:
        ru = False
    return "Компьютер" if ru else "Computer"


def open_regedit(key: str) -> None:
    head, _, rest = key.partition("\\")
    full = HK_FULL.get(head.upper(), head) + ("\\" + rest if rest else "")
    try:
        reg_set("HKCU", REGEDIT_KEY, "LastKey", _regedit_root() + "\\" + full)
    except Exception:
        log.debug("LastKey не записан", exc_info=True)
    shell_open("regedit.exe", "/m")  # /m — новое окно, иначе открытый regedit игнорирует LastKey


# ───────────────────────── курсор ─────────────────────────
CUR_KEY = r"Control Panel\Cursors"
CURSORS = [("Arrow", "Основной", "aero_arrow.cur"), ("Help", "Справка", "aero_helpsel.cur"),
           ("AppStarting", "Фоновый режим", "aero_working.ani"), ("Wait", "Занят", "aero_busy.ani"),
           ("Crosshair", "Точный выбор", ""), ("IBeam", "Выделение текста", ""),
           ("NWPen", "Рукописный ввод", "aero_pen.cur"), ("No", "Недоступно", "aero_unavail.cur"),
           ("SizeNS", "Верт. размер", "aero_ns.cur"), ("SizeWE", "Гор. размер", "aero_ew.cur"),
           ("SizeNWSE", "Диаг. размер 1", "aero_nwse.cur"), ("SizeNESW", "Диаг. размер 2", "aero_nesw.cur"),
           ("SizeAll", "Перемещение", "aero_move.cur"), ("UpArrow", "Альтернативный", "aero_up.cur"),
           ("Hand", "Ссылка", "aero_link.cur"), ("Pin", "Местоположение", "aero_pin.cur"),
           ("Person", "Человек", "aero_person.cur")]


ACC_KEY = r"Software\Microsoft\Accessibility"


def cursor_size_get() -> int:
    v = reg_get("HKCU", ACC_KEY, "CursorSize")
    if isinstance(v, int) and 1 <= v <= 15:
        return v
    base = reg_get("HKCU", CUR_KEY, "CursorBaseSize")
    return max(1, min(15, (int(base) - 32) // 16 + 1)) if isinstance(base, int) else 1


def cursor_size_set(n: int) -> None:
    """Размер как в Параметрах: 1 = стандартный (32 px), каждый шаг +16 px."""
    _need_reg()
    n = max(1, min(15, int(n)))
    reg_set("HKCU", ACC_KEY, "CursorSize", n)
    reg_set("HKCU", CUR_KEY, "CursorBaseSize", 32 + (n - 1) * 16)
    ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 3)  # SPI_SETCURSORS
    log.info(f"✓ Размер указателя: {n} ({32 + (n - 1) * 16} px)")


def cursor_scan():
    scheme = reg_get("HKCU", CUR_KEY, "") or "(без схемы)"
    rows = []
    sysdir = os.path.join(WINDIR, "cursors").lower()
    for reg, title, std in CURSORS:
        v = reg_get("HKCU", CUR_KEY, reg) or ""
        full = os.path.expandvars(v)
        if not v:
            st = "ok"
        elif full.lower().startswith(sysdir) and os.path.basename(full).lower().startswith("aero_"):
            st = "warn"
        elif "\\microsoft\\windows\\cursors\\" in full.lower() and full.lower().endswith("_eoa.cur"):
            st = "ok"  # создаёт сама Windows (Параметры → Указатель мыши)
        else:
            st = "bad"
        rows.append((title, v or "(системный)", st, reg))
    custom = [n for n, _, _ in reg_values("HKCU", CUR_KEY + r"\Schemes")]
    return scheme, rows, custom


def cursor_files_tampered():
    """Файлы aero_* в C:\\Windows\\Cursors, владелец которых не TrustedInstaller (подменены сборкой)."""
    if not IS_WIN:
        return []
    code, out, _ = run_ps(
        "Get-ChildItem \"$env:SystemRoot\\Cursors\\aero_*\" | %{ $o=((Get-Acl $_.FullName).Owner) -replace '^O:','';"
        " if($o -match '^S-1-'){ try{ $o=(New-Object Security.Principal.SecurityIdentifier($o))"
        ".Translate([Security.Principal.NTAccount]).Value }catch{} };"
        " if($o -notmatch 'TrustedInstaller'){ $_.Name + ' (' + $o + ')' } }")
    return [x.strip() for x in out.splitlines() if x.strip()]


CURSOR_RESTORE_PS = r"""
$dst = Join-Path $env:SystemRoot 'Cursors'
$hit = Get-ChildItem (Join-Path $env:SystemRoot 'WinSxS') -Directory -ErrorAction SilentlyContinue |
  ?{ Test-Path (Join-Path $_.FullName 'aero_arrow.cur') } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $hit){ 'NOSRC'; exit 2 }
'SRC ' + $hit.FullName
foreach($f in Get-ChildItem $hit.FullName -File | ?{ $_.Extension -in '.cur','.ani' }){
  $t = Join-Path $dst $f.Name
  if((Test-Path $t) -and (Get-FileHash $t).Hash -eq (Get-FileHash $f.FullName).Hash){ 'SAME ' + $f.Name; continue }
  try{
    if(Test-Path $t){
      takeown /f "$t" /a | Out-Null
      icacls "$t" /grant '*S-1-5-32-544:F' | Out-Null
    }
    Copy-Item $f.FullName $t -Force -ErrorAction Stop
    # права как у оригинала: владелец TrustedInstaller, остальным — чтение
    icacls "$t" /inheritance:r /grant:r 'NT SERVICE\TrustedInstaller:F' '*S-1-5-32-544:RX' '*S-1-5-18:RX' `
      '*S-1-5-32-545:RX' '*S-1-15-2-1:RX' | Out-Null
    icacls "$t" /setowner 'NT SERVICE\TrustedInstaller' | Out-Null
    if($LASTEXITCODE){ 'OWNER ' + $f.Name }
    'OK ' + $f.Name
  }catch{ 'FAIL ' + $f.Name + ' : ' + $_.Exception.Message }
}
"""


def cursor_restore_files():
    """Оригинальные курсоры из WinSxS → C:\\Windows\\Cursors."""
    if not IS_WIN:
        raise RuntimeError("только Windows")
    if not is_admin():
        raise PermissionError
    log.info("⏳ Ищу оригинальные курсоры в C:\\Windows\\WinSxS (до минуты)…")
    code, out, err = run_ps(CURSOR_RESTORE_PS, timeout=600)
    lines = [x.strip() for x in out.splitlines() if x.strip()]
    if "NOSRC" in lines:
        raise RuntimeError("в WinSxS нет оригиналов — остаётся DISM /RestoreHealth + SFC")
    ok = [x[3:] for x in lines if x.startswith("OK ")]
    same = [x for x in lines if x.startswith("SAME ")]
    fail = [x[5:] for x in lines if x.startswith("FAIL ")]
    owner = [x[6:] for x in lines if x.startswith("OWNER ")]
    for x in lines:
        if x.startswith("SRC "):
            log.info(f"   источник: {x[4:]}")
    log.info(f"✓ Восстановлено файлов: {len(ok)}, уже оригинальных: {len(same)}")
    if owner:
        log.warning(f"⚠ Владелец TrustedInstaller не назначен ({len(owner)}): " + ", ".join(owner[:6]))
    for f in fail[:10]:
        log.error(f"✗ {f}")
    if err.strip() and not lines:
        raise RuntimeError(_short(err, 300))


def cursor_reset():
    """Встроенные курсоры Windows: пустые значения → берутся из системных библиотек, не из файлов,
    поэтому подмена файлов в C:\\Windows\\Cursors не влияет."""
    _need_reg()
    roots = [("HKCU", CUR_KEY)]
    if reg_key_exists("HKU", r".DEFAULT\Control Panel\Cursors"):
        roots.append(("HKU", r".DEFAULT\Control Panel\Cursors"))
    for root, key in roots:
        for reg, _t, _std in CURSORS:
            try:
                reg_set(root, key, reg, "", wr.REG_EXPAND_SZ)
            except PermissionError:
                log.warning(f"⚠ {root}\\{key}: нет прав (экран входа не сброшен)")
                break
        else:
            reg_set(root, key, "", "")
            reg_set(root, key, "Scheme Source", 0)
    reg_set("HKCU", CUR_KEY, "CursorBaseSize", 32)
    try:
        reg_set("HKCU", r"Software\Microsoft\Accessibility", "CursorSize", 1)
    except Exception:
        pass
    ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 3)  # SPI_SETCURSORS


def cursor_drop_schemes():
    for name, _, _ in reg_values("HKCU", CUR_KEY + r"\Schemes"):
        reg_del("HKCU", CUR_KEY + r"\Schemes", name)


# ───────────────────────── звуки ─────────────────────────
SND_APPS = r"AppEvents\Schemes\Apps"
SND_EVENTS = [("WindowsLogon", "Вход в Windows"), ("WindowsUnlock", "Разблокировка"),
              ("SystemStart", "Запуск Windows"), ("WindowsLogoff", "Выход из системы"),
              ("SystemExit", "Завершение работы"), (".Default", "Стандартный звук"),
              ("SystemNotification", "Уведомление"), ("DeviceConnect", "Подключение устройства"),
              ("DeviceDisconnect", "Отключение устройства"), ("SystemAsterisk", "Звёздочка"),
              ("SystemHand", "Критическая ошибка")]
BOOT_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI\BootAnimation"
BOOT_POL = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"


def sound_scan():
    rows = []
    media = os.path.join(WINDIR, "media").lower()
    for ev, title in SND_EVENTS:
        base = rf"{SND_APPS}\.Default\{ev}"
        cur = reg_get("HKCU", base + r"\.Current", "") or ""
        dflt = reg_get("HKCU", base + r"\.Default", "") or ""
        full = os.path.expandvars(cur).lower()
        if cur.lower() == dflt.lower():
            st = "ok"
        elif cur and not full.startswith(media):
            st = "bad"
        else:
            st = "warn"
        rows.append((title, cur or "(нет)", dflt or "(нет)", st, ev))
    dis = reg_get("HKLM", BOOT_KEY, "DisableStartupSound")
    if dis is None:
        dis = reg_get("HKLM", BOOT_POL, "DisableStartupSound")
    return rows, not bool(dis)


def sound_reset_all():
    _need_reg()
    reg_set("HKCU", r"AppEvents\Schemes", "", ".Default")
    n = 0
    for app in reg_subkeys("HKCU", SND_APPS):
        for ev in reg_subkeys("HKCU", rf"{SND_APPS}\{app}"):
            base = rf"{SND_APPS}\{app}\{ev}"
            if not reg_key_exists("HKCU", base + r"\.Default"):
                continue
            d = reg_get("HKCU", base + r"\.Default", "") or ""
            if (reg_get("HKCU", base + r"\.Current", "") or "") != d:
                reg_set("HKCU", base + r"\.Current", "", d, wr.REG_EXPAND_SZ)
                n += 1
    return n


def sound_set(ev: str, default: bool):
    base = rf"{SND_APPS}\.Default\{ev}"
    val = (reg_get("HKCU", base + r"\.Default", "") or "") if default else ""
    reg_set("HKCU", base + r"\.Current", "", val, wr.REG_EXPAND_SZ)


def startup_sound_set(on: bool):
    reg_set("HKLM", BOOT_KEY, "DisableStartupSound", 0 if on else 1)
    if reg_get("HKLM", BOOT_POL, "DisableStartupSound") is not None:
        reg_set("HKLM", BOOT_POL, "DisableStartupSound", 0 if on else 1)


# ───────────────────────── автозагрузка ─────────────────────────
APPROVED = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved"
RUN_KEYS = [("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run", "Run"),
            ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\RunOnce", None),
            ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "Run"),
            ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", None),
            ("HKLM", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "Run32"),
            ("HKLM", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce", None),
            ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", None),
            ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", None)]
ACTIVE_SETUP = [r"SOFTWARE\Microsoft\Active Setup\Installed Components",
                r"SOFTWARE\WOW6432Node\Microsoft\Active Setup\Installed Components"]
MUSIC_RE = re.compile(r"\.(mp3|wav|wma|ogg|flac|m4a|aac|mid|midi)\b|wmplayer|vlc|aimp|foobar|winamp|"
                      r"mpc-hc|potplayer|soundplayer|playsound|mplay32|sndrec|musicbee|groove", re.I)


def _approved_on(root, sub, name) -> bool:
    v = reg_get(root, rf"{APPROVED}\{sub}", name)
    return not (isinstance(v, bytes) and v and v[0] & 1)


def _approved_set(root, sub, name, on: bool):
    ft = int((time.time() + 11644473600) * 10_000_000).to_bytes(8, "little")
    data = (b"\x02\x00\x00\x00" + b"\x00" * 8) if on else (b"\x03\x00\x00\x00" + ft)
    reg_set(root, rf"{APPROVED}\{sub}", name, data, wr.REG_BINARY)


def startup_folders():
    return [("HKCU", Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
             "Папка автозагрузки (пользователь)"),
            ("HKLM", Path(os.environ.get("ProgramData", "")) / r"Microsoft\Windows\Start Menu\Programs\StartUp",
             "Папка автозагрузки (все)")]


def startup_scan():
    items = []
    for root, path, appr in RUN_KEYS:
        for name, val, _t in reg_values(root, path):
            if not name:
                continue
            src = f"{root}\\{'…' + path[-30:] if len(path) > 34 else path}"
            items.append(dict(kind="reg", src=src, name=name, cmd=str(val), root=root, path=path, appr=appr,
                              on=_approved_on(root, appr, name) if appr else True))
    lnks = []
    for root, folder, title in startup_folders():
        if not folder.is_dir():
            continue
        for f in folder.iterdir():
            if f.name.lower() == "desktop.ini":
                continue
            it = dict(kind="file", src=title, name=f.name, cmd=str(f), root=root, file=str(f),
                      appr="StartupFolder", on=_approved_on(root, "StartupFolder", f.name))
            items.append(it)
            if f.suffix.lower() == ".lnk":
                lnks.append(it)
    if lnks and IS_WIN:
        arr = ",".join(ps_quote(i["file"]) for i in lnks)
        code, out, _ = run_ps("$s=New-Object -ComObject WScript.Shell;@(" + arr + ")|%{$l=$s.CreateShortcut($_);"
                              "($l.TargetPath+' '+$l.Arguments).Trim()}|ConvertTo-Json -Compress")
        try:
            res = json.loads(out or "[]")
            res = [res] if isinstance(res, str) else res
            for it, t in zip(lnks, res):
                it["cmd"] = f"{t}   ← {it['name']}"
        except Exception:
            pass
    if IS_WIN:
        code, out, _ = run_ps(
            "@(Get-ScheduledTask | ?{$_.TaskPath -notlike '\\Microsoft\\*'} | %{[pscustomobject]@{"
            "p=$_.TaskPath;n=$_.TaskName;s=[string]$_.State;"
            "a=(($_.Actions|%{($_.Execute+' '+$_.Arguments).Trim()}) -join ' ; ')}}) | ConvertTo-Json -Compress",
            timeout=90)
        try:
            res = json.loads(out or "[]")
            res = [res] if isinstance(res, dict) else res
            for t in res:
                items.append(dict(kind="task", src="Планировщик " + t["p"], name=t["n"], cmd=t.get("a") or "",
                                  tpath=t["p"], on=t["s"] != "Disabled"))
        except Exception as e:
            log.warning(f"⚠ Планировщик не прочитан: {e}")
        code, out, _ = run_ps(
            "@(Get-CimInstance Win32_Service | ?{ $_.StartMode -in 'Auto','Disabled' -and $_.PathName -and "
            "$_.PathName -notlike \"*$env:SystemRoot*\" -and $_.PathName -notmatch 'Windows Defender' } | "
            "%{[pscustomobject]@{n=$_.Name;d=$_.DisplayName;p=$_.PathName;m=[string]$_.StartMode}}) "
            "| ConvertTo-Json -Compress", timeout=90)
        try:
            res = json.loads(out or "[]")
            res = [res] if isinstance(res, dict) else res
            for t in res:
                items.append(dict(kind="svc", src="Службы (не Windows)", name=f"{t['d']} ({t['n']})",
                                  svc=t["n"], cmd=t.get("p") or "", on=t["m"] != "Disabled"))
        except Exception as e:
            log.warning(f"⚠ Службы не прочитаны: {e}")
    win = WINDIR.lower()
    for path in ACTIVE_SETUP:
        for guid in reg_subkeys("HKLM", path):
            key = rf"{path}\{guid}"
            stub = reg_get("HKLM", key, "StubPath")
            if not stub or reg_get("HKLM", key, "IsInstalled") in (0, b"\x00\x00\x00\x00"):
                continue
            if win in os.path.expandvars(str(stub)).lower() or "%systemroot%" in str(stub).lower():
                continue
            items.append(dict(kind="asetup", src="Active Setup", name=reg_get("HKLM", key, "") or guid,
                              cmd=str(stub), root="HKLM", path=key, on=True))
    for it in items:
        it["music"] = bool(MUSIC_RE.search(it["cmd"] + " " + it["name"]))
    return items


def startup_set_on(it: dict, on: bool):
    if it["kind"] == "task":
        verb = "Enable" if on else "Disable"
        code, _o, err = run_ps(f"{verb}-ScheduledTask -TaskPath {ps_quote(it['tpath'])} -TaskName {ps_quote(it['name'])}")
        if code:
            raise RuntimeError(err.strip() or "нет прав (нужен администратор)")
    elif it["kind"] == "svc":
        code, _o, err = run_ps(f"Set-Service -Name {ps_quote(it['svc'])} "
                               f"-StartupType {'Automatic' if on else 'Disabled'} -ErrorAction Stop")
        if code:
            raise RuntimeError(err.strip() or "нет прав (нужен администратор)")
    elif it.get("appr"):
        _approved_set(it["root"], it["appr"], it["name"], on)
    else:
        raise RuntimeError("RunOnce / Policies / Active Setup нельзя отключить — только удалить")
    it["on"] = on


def _unique(path: Path) -> Path:
    n = 1
    out = path
    while out.exists():
        out = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return out


def startup_delete(it: dict):
    if it["kind"] == "reg":
        reg_del(it["root"], it["path"], it["name"])
        if it.get("appr"):
            reg_del(it["root"], rf"{APPROVED}\{it['appr']}", it["name"])
    elif it["kind"] == "asetup":
        reg_del("HKLM", it["path"], "StubPath")
    elif it["kind"] == "svc":
        raise RuntimeError("службу не удаляю — только «⏸ Отключить»")
    elif it["kind"] == "file":
        dst = APP_ROOT / "removed_startup"
        dst.mkdir(exist_ok=True)
        target = _unique(dst / it["name"])
        shutil.move(it["file"], target)  # между дисками os.replace не работает
        log.info(f"   файл перенесён: {target}")
    else:
        code, _o, err = run_ps(f"Unregister-ScheduledTask -TaskPath {ps_quote(it['tpath'])} "
                               f"-TaskName {ps_quote(it['name'])} -Confirm:$false")
        if code:
            raise RuntimeError(err.strip() or "нет прав")


# ───────────────────────── проверки реестра ─────────────────────────
WL = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
POL_SYS = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
POL_EXP = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
IFEO = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
HOSTS = Path(WINDIR) / r"System32\drivers\etc\hosts"
HOSTS_OK = {"localhost", "localhost.localdomain"}


def _absent_or0(root, path, name):
    v = reg_get(root, path, name)
    return (v in (None, 0, "0")), ("нет" if v is None else str(v))


def _policy_check(root, path, name):
    return lambda: _absent_or0(root, path, name), lambda: reg_del(root, path, name)


IFEO_OK = re.compile(r"procexp|systeminformer|processhacker", re.I)  # замена диспетчера задач — легально


def _ifeo_list():
    """Программы с IFEO Debugger, кроме замены taskmgr на Process Explorer / System Informer."""
    out = []
    for k in reg_subkeys("HKLM", IFEO):
        dbg = reg_get("HKLM", rf"{IFEO}\{k}", "Debugger")
        if dbg and not (k.lower() == "taskmgr.exe" and IFEO_OK.search(str(dbg))):
            out.append((k, str(dbg)))
    return out


def _hosts_bad(ln: str) -> bool:
    t = ln.split("#", 1)[0].split()
    return len(t) >= 2 and not set(x.lower() for x in t[1:]) <= HOSTS_OK


def _hosts_lines():
    try:
        txt = HOSTS.read_text("utf-8", errors="replace")
    except Exception:
        return []
    return [ln.strip() for ln in txt.splitlines() if _hosts_bad(ln)]


def _hosts_fix():
    """Чужие строки не стираются, а комментируются (# WinFix:) — их легко вернуть."""
    raw = HOSTS.read_bytes()
    bak = HOSTS.with_name("hosts.bak_winfix")
    bak.write_bytes(raw)
    txt = raw.decode("utf-8", "replace")
    lines = [("# WinFix: " + ln) if _hosts_bad(ln) else ln for ln in txt.splitlines()]
    HOSTS.write_text("\r\n".join(lines) + "\r\n", "utf-8", newline="")
    log.info(f"   чужие строки закомментированы, копия: {bak}")


def _exe_assoc():
    a = reg_get("HKCR", ".exe", "")
    c = reg_get("HKCR", r"exefile\shell\open\command", "")
    hk = reg_key_exists("HKCU", r"Software\Classes\.exe") or reg_key_exists("HKCU", r"Software\Classes\exefile")
    ok = (a or "").lower() == "exefile" and (c or "").replace(" ", "") == '"%1"%*' and not hk
    return ok, f".exe={a}; command={c}" + ("; есть перехват в HKCU" if hk else "")


def _exe_assoc_fix():
    reg_set("HKLM", r"SOFTWARE\Classes\.exe", "", "exefile")
    reg_set("HKLM", r"SOFTWARE\Classes\exefile\shell\open\command", "", '"%1" %*')
    for k in (r"Software\Classes\.exe", r"Software\Classes\exefile"):
        if reg_key_exists("HKCU", k):
            reg_delete_tree("HKCU", k)


def build_checks():
    ui_ = os.path.join(WINDIR, "system32", "userinit.exe") + ","
    C = []

    def add(title, norm, check, fix, level="bad", key=""):
        C.append(dict(title=title, norm=norm, check=check, fix=fix, level=level, key=key))

    add("Оболочка Winlogon (Shell)", "explorer.exe",
        lambda: (((reg_get("HKLM", WL, "Shell") or "").strip().lower() == "explorer.exe"), str(reg_get("HKLM", WL, "Shell"))),
        lambda: reg_set("HKLM", WL, "Shell", "explorer.exe"), key="HKLM\\" + WL)
    add("Userinit", ui_,
        lambda: (((reg_get("HKLM", WL, "Userinit") or "").strip().lower().rstrip(",") == ui_.lower().rstrip(",")),
                 str(reg_get("HKLM", WL, "Userinit"))),
        lambda: reg_set("HKLM", WL, "Userinit", ui_), key="HKLM\\" + WL)
    add("Shell в HKCU (перехват)", "нет",
        lambda: (reg_get("HKCU", r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell") is None,
                 str(reg_get("HKCU", r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell"))),
        lambda: reg_del("HKCU", r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell"),
        key=r"HKCU\Software\Microsoft\Windows NT\CurrentVersion\Winlogon")
    for root, path, name, title in [
            ("HKCU", POL_SYS, "DisableTaskMgr", "Запрет диспетчера задач"),
            ("HKLM", POL_SYS, "DisableTaskMgr", "Запрет диспетчера задач (все)"),
            ("HKCU", POL_SYS, "DisableRegistryTools", "Запрет regedit"),
            ("HKLM", POL_SYS, "DisableRegistryTools", "Запрет regedit (все)"),
            ("HKCU", r"Software\Policies\Microsoft\Windows\System", "DisableCMD", "Запрет командной строки"),
            ("HKCU", POL_EXP, "NoControlPanel", "Запрет панели управления"),
            ("HKCU", POL_EXP, "NoRun", "Запрет «Выполнить» (Win+R)"),
            ("HKCU", POL_EXP, "NoFolderOptions", "Запрет параметров папок")]:
        chk, fix = _policy_check(root, path, name)
        add(title, "нет / 0", chk, fix, key=f"{root}\\{path}")
    add("UAC (EnableLUA)", "1",
        lambda: (reg_get("HKLM", POL_SYS, "EnableLUA") in (None, 1), str(reg_get("HKLM", POL_SYS, "EnableLUA"))),
        lambda: reg_set("HKLM", POL_SYS, "EnableLUA", 1), level="warn", key="HKLM\\" + POL_SYS)
    add("AppInit_DLLs (внедрение DLL)", "пусто",
        lambda: (not (reg_get("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows", "AppInit_DLLs") or "").strip(),
                 str(reg_get("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows", "AppInit_DLLs") or "")),
        lambda: reg_set("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows", "AppInit_DLLs", ""),
        key=r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows")
    add("IFEO Debugger (подмена программ)", "нет",
        lambda: (lambda L: (not L, "; ".join(f"{k} → {d}" for k, d in L) or "нет"))(_ifeo_list()),
        lambda: [reg_del("HKLM", rf"{IFEO}\{k}", "Debugger") for k, _d in _ifeo_list()], key="HKLM\\" + IFEO)
    add("Ассоциация .exe", '"%1" %*', _exe_assoc, _exe_assoc_fix, key=r"HKCR\exefile\shell\open\command")
    add("Служба обновлений (wuauserv)", "вручную (3)",
        lambda: (reg_get("HKLM", r"SYSTEM\CurrentControlSet\Services\wuauserv", "Start") in (2, 3),
                 str(reg_get("HKLM", r"SYSTEM\CurrentControlSet\Services\wuauserv", "Start"))),
        lambda: reg_set("HKLM", r"SYSTEM\CurrentControlSet\Services\wuauserv", "Start", 3), level="warn",
        key=r"HKLM\SYSTEM\CurrentControlSet\Services\wuauserv")
    chk, fix = _policy_check("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "NoAutoUpdate")
    add("Политика: обновления выключены", "нет / 0", chk, fix, level="warn",
        key=r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU")
    chk, fix = _policy_check("HKLM", r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware")
    add("Политика: Defender выключен", "нет / 0", chk, fix, level="warn",
        key=r"HKLM\SOFTWARE\Policies\Microsoft\Windows Defender")
    chk, fix = _policy_check("HKLM", r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                             "DisableRealtimeMonitoring")
    add("Политика: защита в реальном времени выкл.", "нет / 0", chk, fix, level="warn",
        key=r"HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection")
    IS = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    add("Прокси (ProxyEnable)", "0",
        lambda: (reg_get("HKCU", IS, "ProxyEnable") in (None, 0),
                 f"{reg_get('HKCU', IS, 'ProxyEnable')} {reg_get('HKCU', IS, 'ProxyServer') or ''}".strip()),
        lambda: reg_set("HKCU", IS, "ProxyEnable", 0), level="warn", key="HKCU\\" + IS)
    add("Файл hosts", "только localhost",
        lambda: (lambda L: (not L, f"{len(L)} строк: " + "; ".join(L[:3])))(_hosts_lines()),
        _hosts_fix, level="warn", key=str(HOSTS))
    return C


# ───────────────────────── порты ─────────────────────────
RISKY = {21: "FTP", 23: "Telnet", 135: "RPC", 137: "NetBIOS", 138: "NetBIOS", 139: "NetBIOS", 445: "SMB",
         1900: "SSDP/UPnP", 3389: "RDP", 5900: "VNC", 5985: "WinRM", 5986: "WinRM"}


def pid_names() -> dict:
    code, out, _ = run_cmd(["tasklist", "/fo", "csv", "/nh"])
    names = {}
    for row in csv.reader(out.splitlines()):
        if len(row) >= 2 and row[1].isdigit():
            names[row[1]] = row[0]
    return names


def ports_scan():
    _c, out, _ = run_cmd(["netstat", "-ano"])
    names = pid_names()
    rows = []
    for line in out.splitlines():
        p = line.split()
        if not p or p[0] not in ("TCP", "UDP"):
            continue
        if p[0] == "TCP" and len(p) >= 5:
            local, remote, state, pid = p[1], p[2], p[3], p[4]
        elif p[0] == "UDP" and len(p) >= 4:
            local, remote, state, pid = p[1], p[2], "", p[-1]
        else:
            continue
        addr, _, port = local.rpartition(":")
        if not port.isdigit():
            continue
        listen = p[0] == "UDP" or remote in ("0.0.0.0:0", "[::]:0", "*:*")
        rows.append(dict(proto=p[0], addr=addr, port=int(port), remote=remote,
                         state="слушает" if (listen and p[0] == "TCP") else state, listen=listen,
                         pid=pid, name=names.get(pid, "?")))
    rows.sort(key=lambda r: (r["proto"], r["port"]))
    return rows


def port_rule(proto, port) -> str:
    return f"WinFix блок {proto} {port}"


RESTORE_POINT_PS = r"""
$k = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore'
$old = (Get-ItemProperty $k -Name SystemRestorePointCreationFrequency -ErrorAction SilentlyContinue).SystemRestorePointCreationFrequency
$rc = 0
try{
  Set-ItemProperty $k -Name SystemRestorePointCreationFrequency -Value 0 -Type DWord   # обход лимита «1 точка в 24 ч»
  Enable-ComputerRestore -Drive "$env:SystemDrive\" -ErrorAction Stop
  Checkpoint-Computer -Description 'WinFix' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop -WarningVariable w
  if($w){ 'RP_WARN ' + ($w -join ' '); $rc = 3 } else { 'RP_OK' }
}catch{ 'RP_WARN ' + $_.Exception.Message; $rc = 1 }
finally{
  if($null -eq $old){ Remove-ItemProperty $k -Name SystemRestorePointCreationFrequency -ErrorAction SilentlyContinue }
  else{ Set-ItemProperty $k -Name SystemRestorePointCreationFrequency -Value $old -Type DWord }
}
exit $rc
"""


def _explorer_running() -> bool:
    _c, out, _ = run_cmd(["tasklist", "/fi", "IMAGENAME eq explorer.exe", "/fo", "csv", "/nh"])
    return "explorer.exe" in out.lower()


# ───────────────────────── Worker ─────────────────────────
class Worker:
    def __init__(self):
        self.busy = False

    def run(self, title: str, fn, *args, then=None):
        """then — вызвать в UI-потоке ПОСЛЕ освобождения (можно запускать следующее действие)."""
        if self.busy:
            log.warning("⚠ Подождите — выполняется другое действие")
            return False
        self.busy = True
        ui(lambda: _APP and _APP._set_busy(title))

        def body():
            t0 = time.time()
            log.debug(f"▶ начало: {title}")
            try:
                fn(*args)
            except PermissionError:
                log.error(f"✗ {title}: нет прав — запустите от администратора", exc_info=True)
            except subprocess.TimeoutExpired:
                log.error(f"✗ {title}: превышено время ожидания", exc_info=True)
            except Exception as e:
                log.error(f"✗ {title}: {e}", exc_info=True)
            finally:
                log.debug(f"■ конец: {title} ({time.time() - t0:.1f} с)")
                self.busy = False
                LOGQ.put(_DONE_SENTINEL)
                if then:
                    LOGQ.put(then)
        threading.Thread(target=body, daemon=True).start()
        return True


_APP = None

# ───────────────────────── тема ─────────────────────────
_QT_THEMES = {
    "dark": {"bg": "#1b1d23", "side": "#16181d", "panel": "#23262e", "panel2": "#2a2e38", "line": "#343946",
             "text": "#e6e8ee", "muted": "#8a91a3", "log_bg": "#111318", "log_fg": "#d5d8e0", "accent": "#4f8cff",
             "ok": "#3ecf8e", "err": "#ff5d6c", "warn": "#f5b545"},
    "light": {"bg": "#f3f4f7", "side": "#e9ebf0", "panel": "#ffffff", "panel2": "#f1f3f7", "line": "#dde1e8",
              "text": "#1c2230", "muted": "#6b7385", "log_bg": "#fbfbfd", "log_fg": "#1c2230", "accent": "#2f6fe4",
              "ok": "#15935a", "err": "#d42f40", "warn": "#a96a00"}}
_OK, _ERR, _WARN = "#3ecf8e", "#ff5d6c", "#f5b545"  # меняются в _apply_theme под тему
ST_COLOR = {"ok": _OK, "warn": _WARN, "bad": _ERR}


def _set_status_colors(p: dict) -> None:
    global _OK, _ERR, _WARN
    _OK, _ERR, _WARN = p["ok"], p["err"], p["warn"]
    ST_COLOR.update(ok=_OK, warn=_WARN, bad=_ERR)


def _palette(p: dict) -> QPalette:
    """Палитра для всего, что QSS не покрыл (системные части диалогов, списки, поля)."""
    pal = QPalette()
    for role, key in ((QPalette.Window, "panel"), (QPalette.WindowText, "text"), (QPalette.Base, "panel2"),
                      (QPalette.AlternateBase, "panel"), (QPalette.Text, "text"), (QPalette.Button, "panel2"),
                      (QPalette.ButtonText, "text"), (QPalette.ToolTipBase, "panel2"), (QPalette.ToolTipText, "text"),
                      (QPalette.Highlight, "accent"), (QPalette.PlaceholderText, "muted"), (QPalette.Link, "accent")):
        pal.setColor(role, QColor(p[key]))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, QColor(p["muted"]))
    return pal
ST_TEXT = {"ok": "✓ норма", "warn": "⚠ изменено", "bad": "✗ чужое"}


def _qss(p: dict) -> str:
    return f"""
    * {{ font-family: "Segoe UI"; font-size: 10pt; color: {p['text']}; }}
    QMainWindow, QWidget#root {{ background: {p['bg']}; }}
    QDialog, QMessageBox, QFileDialog, QInputDialog {{ background: {p['panel']}; color: {p['text']}; }}
    QDialog QLabel, QMessageBox QLabel {{ color: {p['text']}; background: transparent; }}
    QDialog QPushButton {{ min-width: 80px; }}
    QAbstractItemView, QTreeView, QListView, QTextEdit, QPlainTextEdit {{ background: {p['panel2']}; color: {p['text']};
        border: 1px solid {p['line']}; border-radius: 7px; selection-background-color: {p['accent']};
        selection-color: #ffffff; }}
    QComboBox, QSpinBox, QDoubleSpinBox {{ background: {p['panel2']}; color: {p['text']}; border: 1px solid {p['line']};
        border-radius: 7px; padding: 4px 8px; }}
    QComboBox:focus, QSpinBox:focus {{ border-color: {p['accent']}; }}
    QComboBox QAbstractItemView {{ background: {p['panel']}; border: 1px solid {p['line']}; }}
    QCheckBox, QRadioButton {{ background: transparent; }}
    QWidget#page {{ background: {p['bg']}; }}
    #side {{ background: {p['side']}; border-right: 1px solid {p['line']}; }}
    #side QPushButton#nav {{ border: none; border-radius: 9px; background: transparent; text-align: left;
                             padding: 9px 12px; font-size: 10pt; color: {p['muted']}; }}
    #side QPushButton#nav:hover {{ background: {p['panel2']}; color: {p['text']}; }}
    #side QPushButton#nav:checked {{ background: {p['panel2']}; color: {p['text']}; font-weight: 600;
                                     border-left: 3px solid {p['accent']}; }}
    #side QPushButton#burger {{ border: none; background: transparent; font-size: 14pt; text-align: left;
                                padding: 6px 14px; color: {p['muted']}; }}
    #side QPushButton#burger:hover {{ color: {p['accent']}; }}
    #side QLabel#appName {{ font-size: 11pt; font-weight: 700; color: {p['text']}; padding-left: 4px; }}
    QFrame#card {{ background: {p['panel']}; border: 1px solid {p['line']}; border-radius: 10px; }}
    QLabel#cardTitle {{ color: {p['muted']}; font-size: 8pt; font-weight: 600; letter-spacing: 1px; }}
    QLabel#hint {{ color: {p['muted']}; font-size: 9pt; }}
    QLabel#big {{ font-size: 13pt; font-weight: 600; }}
    QPushButton {{ background: {p['panel2']}; border: 1px solid {p['line']}; border-radius: 7px; padding: 6px 14px; }}
    QPushButton:hover {{ border-color: {p['accent']}; }}
    QPushButton:disabled {{ color: {p['muted']}; }}
    QPushButton#primary {{ background: {p['accent']}; border-color: {p['accent']}; color: #ffffff; font-weight: 600; }}
    QPushButton#primary:hover {{ background: {QColor(p['accent']).lighter(115).name()}; }}
    QPushButton#danger {{ background: transparent; border: 1px solid {_ERR}; color: {_ERR}; }}
    QPushButton#danger:hover {{ background: {_ERR}; color: #ffffff; }}
    QPushButton#chip {{ padding: 3px 10px; border-radius: 12px; font-size: 9pt; }}
    QPushButton#seg {{ border-radius: 0; padding: 5px 16px; }}
    QPushButton#seg:checked {{ background: {p['accent']}; color: #ffffff; border-color: {p['accent']}; }}
    QLineEdit {{ background: {p['panel2']}; border: 1px solid {p['line']}; border-radius: 7px; padding: 5px 8px; }}
    QLineEdit:focus {{ border-color: {p['accent']}; }}
    QTableWidget {{ background: {p['panel']}; alternate-background-color: {p['panel2']}; border: 1px solid {p['line']};
                    border-radius: 7px; selection-background-color: {p['accent']}; selection-color: #ffffff; }}
    QHeaderView::section {{ background: {p['panel2']}; color: {p['muted']}; border: none;
                            border-bottom: 1px solid {p['line']}; padding: 5px; font-weight: 600; }}
    QTableCornerButton::section {{ background: {p['panel2']}; border: none; }}
    QPlainTextEdit#log {{ background: {p['log_bg']}; color: {p['log_fg']}; border: 1px solid {p['line']};
                          border-radius: 7px; font-family: Consolas; font-size: 9pt; }}
    QMenu {{ background: {p['panel']}; border: 1px solid {p['line']}; border-radius: 8px; padding: 4px; }}
    QMenu::item {{ padding: 6px 22px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {p['accent']}; color: #ffffff; }}
    QMenu::separator {{ height: 1px; background: {p['line']}; margin: 4px 8px; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; }}
    QScrollBar:horizontal {{ height: 10px; background: transparent; }}
    QScrollBar::handle {{ background: {p['line']}; border-radius: 5px; min-height: 24px; min-width: 24px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QToolTip {{ background: {p['panel2']}; color: {p['text']}; border: 1px solid {p['accent']}; padding: 4px; }}
    QSplitter::handle {{ background: {p['bg']}; }}
    #statusbar {{ background: {p['side']}; border-top: 1px solid {p['line']}; }}
    #statusbar QLabel {{ color: {p['muted']}; font-size: 9pt; }}
    QLabel#pill {{ background: {p['panel2']}; border-radius: 9px; padding: 1px 10px; }}
    """


# ───────────────────────── виджеты ─────────────────────────
class Toggle(QAbstractButton):
    _accent, _off, _text = "#4f8cff", "#454b59", "#e6e8ee"

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)
        self.setCursor(Qt.PointingHandCursor)

    @classmethod
    def set_theme(cls, accent, off, text):
        cls._accent, cls._off, cls._text = accent, off, text

    def sizeHint(self):
        w = 44 + (self.fontMetrics().horizontalAdvance(self.text()) + 12 if self.text() else 0)
        return QSize(w, 26)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self._accent if self.isChecked() else self._off))
        p.drawRoundedRect(QRectF(2, 4, 38, 18), 9, 9)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QRectF(22 if self.isChecked() else 4, 6, 14, 14))
        if self.text():
            p.setPen(QColor(self._text))
            p.drawText(QRectF(50, 0, self.width() - 50, self.height()), Qt.AlignVCenter | Qt.AlignLeft, self.text())


class Stepper(QWidget):
    changed = Signal(int)

    def __init__(self, value=1, lo=1, hi=15, suffix="", parent=None):
        super().__init__(parent)
        self.lo, self.hi, self.suffix = lo, hi, suffix
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.minus = _btn("−", "chip", "Меньше", lambda: self.set_value(self.val - 1, True))
        self.plus = _btn("+", "chip", "Больше", lambda: self.set_value(self.val + 1, True))
        self.lbl = QLabel()
        self.lbl.setMinimumWidth(70)
        self.lbl.setAlignment(Qt.AlignCenter)
        for w in (self.minus, self.lbl, self.plus):
            lay.addWidget(w)
        self.val = lo
        self.set_value(value)

    def set_value(self, v, emit=False):
        v = max(self.lo, min(self.hi, int(v)))
        changed = v != self.val
        self.val = v
        self.lbl.setText(f"{v}{self.suffix}")
        self.minus.setEnabled(v > self.lo)
        self.plus.setEnabled(v < self.hi)
        if emit and changed:
            self.changed.emit(v)


class Segmented(QWidget):
    changed = Signal(str)

    def __init__(self, options, current, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.group = QButtonGroup(self)
        for key, title in options:
            b = QPushButton(title)
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setChecked(key == current)
            b.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
            self.group.addButton(b)
            lay.addWidget(b)
        lay.addStretch(1)


def _lab(text, name=""):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(name == "hint")
    return lb


def _btn(text, name="", tip="", slot=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    if tip:
        b.setToolTip(tip)
    if slot:
        b.clicked.connect(lambda _=False, t=text: log.debug(f"клик: {t}"))
        b.clicked.connect(slot)
    b.setCursor(Qt.PointingHandCursor)
    return b


def _card(title):
    fr = QFrame()
    fr.setObjectName("card")
    lay = QVBoxLayout(fr)
    lay.setContentsMargins(14, 10, 14, 12)
    lay.setSpacing(8)
    lay.addWidget(_lab(title.upper(), "cardTitle"))
    return fr, lay


def _row(*widgets, stretch=True):
    h = QHBoxLayout()
    h.setSpacing(8)
    for w in widgets:
        h.addWidget(w)
    if stretch:
        h.addStretch(1)
    return h


def _table(headers, stretch_col=-1):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(26)
    h = t.horizontalHeader()
    h.setSectionResizeMode(QHeaderView.ResizeToContents)
    h.setSectionResizeMode(stretch_col if stretch_col >= 0 else len(headers) - 1, QHeaderView.Stretch)
    t.setContextMenuPolicy(Qt.CustomContextMenu)
    t.setWordWrap(False)
    return t


def _cell(text, color=None, tip=""):
    it = QTableWidgetItem(str(text))
    if color:
        it.setForeground(QColor(color))
    it.setToolTip(tip or str(text))
    return it


def _table_text(t: QTableWidget, rows=None) -> str:
    out = []
    if rows is None:
        rows = range(t.rowCount())
        out.append("\t".join(t.horizontalHeaderItem(c).text() for c in range(t.columnCount())))
    for r in rows:
        out.append("\t".join((t.item(r, c).text() if t.item(r, c) else "") for c in range(t.columnCount())))
    return "\n".join(out)


def _menu(parent, items):
    m = QMenu(parent)
    for it in items:
        if it is None:
            m.addSeparator()
        else:
            a = QAction(it[0], m)
            a.triggered.connect(lambda _=False, t=it[0]: log.debug(f"меню: {t}"))
            a.triggered.connect(it[1])
            m.addAction(a)
    return m


def _copy(text):
    QGuiApplication.clipboard().setText(text)
    log.info("✓ Скопировано")


# ───────────────────────── окно ─────────────────────────
class App(QMainWindow):
    PAGES = [("🖱", "Курсор", "Курсор"), ("🔊", "Звуки", "Звуки входа"),
             ("🚀", "Автозагрузка", "Автозагрузка (музыка при входе)"), ("🩺", "Реестр", "Проверка реестра"),
             ("🌐", "Порты", "Порты"), ("🛠", "Система", "Система и инструменты"), ("🎨", "Цвета", "Цвета")]
    SIDE_W, SIDE_MIN = 196, 62

    def __init__(self):
        super().__init__()
        global _APP
        _APP = self
        self.cfg = load_config()
        self.worker = Worker()
        self.startup_items: list = []
        self.port_rows: list = []
        self.checks = build_checks()
        self.check_res: list = []
        self.busy_btns: list = []
        self._log_lines: deque = deque(maxlen=5000)
        self._size_timer = QTimer(self)
        self._size_timer.setSingleShot(True)
        self._size_timer.timeout.connect(self._cur_size_apply)
        self.setWindowTitle(f"{APP_NAME} — v{VERSION} · Qt6")
        self.resize(1180, 780)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        body = QHBoxLayout()
        body.setSpacing(0)
        outer.addLayout(body, 1)

        side = QFrame()
        side.setObjectName("side")
        self.side = side
        sl = QVBoxLayout(side)
        sl.setContentsMargins(8, 8, 8, 10)
        sl.setSpacing(4)
        head = QHBoxLayout()
        self.burger = QPushButton("☰")
        self.burger.setObjectName("burger")
        self.burger.setToolTip("Свернуть / развернуть панель")
        self.burger.setCursor(Qt.PointingHandCursor)
        self.burger.clicked.connect(self._toggle_side)
        head.addWidget(self.burger)
        self.app_name = _lab(APP_NAME, "appName")
        head.addWidget(self.app_name, 1)
        sl.addLayout(head)
        sl.addSpacing(6)
        self.nav = QButtonGroup(self)
        self.nav_btns = []
        self.stack = QStackedWidget()
        builders = [self._page_cursor, self._page_sound, self._page_startup, self._page_registry,
                    self._page_ports, self._page_system, self._page_theme]
        for i, ((emo, short, tip), build) in enumerate(zip(self.PAGES, builders)):
            b = QPushButton()
            b.setObjectName("nav")
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setFixedHeight(40)
            b.setCursor(Qt.PointingHandCursor)
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda pos, bb=b: self._side_menu(bb.mapToGlobal(pos)))
            self.nav_btns.append((b, emo, short))
            self.nav.addButton(b, i)
            if i == len(self.PAGES) - 1:
                sl.addStretch(1)
            sl.addWidget(b)
            page = QWidget()
            page.setObjectName("page")
            pl = QVBoxLayout(page)
            pl.setContentsMargins(16, 16, 16, 12)
            pl.setSpacing(12)
            pl.addWidget(_lab(f"{emo}  {tip}", "big"))
            build(pl)
            self.stack.addWidget(page)
        self.nav.idClicked.connect(self._go)
        side.setContextMenuPolicy(Qt.CustomContextMenu)
        side.customContextMenuRequested.connect(lambda pos: self._side_menu(side.mapToGlobal(pos)))
        self._set_side(bool(self.cfg.get("side_collapsed", False)))
        body.addWidget(side)

        self.split = QSplitter(Qt.Vertical)
        self.split.addWidget(self.stack)
        lc, ll = _card("Лог")
        self.logw = QPlainTextEdit()
        self.logw.setObjectName("log")
        self.logw.setReadOnly(True)
        self.logw.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.logw.setMaximumBlockCount(5000)
        self.logw.setContextMenuPolicy(Qt.CustomContextMenu)
        self.logw.customContextMenuRequested.connect(self._log_menu)
        ll.addWidget(self.logw)
        self.split.addWidget(lc)
        self.split.setStretchFactor(0, 3)
        self.split.setStretchFactor(1, 1)
        wrap = QVBoxLayout()
        wrap.setContentsMargins(0, 0, 12, 8)
        wrap.addWidget(self.split)
        body.addLayout(wrap, 1)

        sb = QFrame()
        sb.setObjectName("statusbar")
        sb.setFixedHeight(30)
        sbl = QHBoxLayout(sb)
        sbl.setContentsMargins(10, 0, 12, 0)
        self.pill = QLabel("● готов")
        self.pill.setObjectName("pill")
        sbl.addWidget(self.pill)
        adm = is_admin()
        sbl.addWidget(QLabel("🛡 администратор" if adm else "⚠ без прав администратора — часть исправлений не сработает"))
        sbl.addStretch(1)
        self.status_lbl = QLabel("")
        sbl.addWidget(self.status_lbl)
        outer.addWidget(sb)

        self._apply_theme(self.cfg.get("theme", "dark"))
        try:
            if self.cfg.get("geometry"):
                self.restoreGeometry(QByteArray.fromBase64(self.cfg["geometry"].encode()))
            if self.cfg.get("splitter"):
                self.split.restoreState(QByteArray.fromBase64(self.cfg["splitter"].encode()))
        except Exception:
            pass
        self._go(int(self.cfg.get("page", 0)) % len(self.PAGES))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._drain_log)
        self.timer.start(150)
        set_verbose(bool(self.cfg.get("log_verbose")))
        if not adm:
            log.warning("⚠ Без прав администратора — изменения HKLM, задачи и SFC не сработают")
        log.info(f"Лог-файл: {LOG_PATH}")
        QTimer.singleShot(300, self._refresh_light)

    # ── общие ──
    def _go(self, i):
        log.debug(f"вкладка → {self.PAGES[i][1]}")
        self.nav.button(i).setChecked(True)
        self.stack.setCurrentIndex(i)
        self.cfg["page"] = i

    def _set_side(self, collapsed: bool):
        self.cfg["side_collapsed"] = collapsed
        self.side.setFixedWidth(self.SIDE_MIN if collapsed else self.SIDE_W)
        self.app_name.setVisible(not collapsed)
        for b, emo, short in self.nav_btns:
            b.setText(emo if collapsed else f"{emo}   {short}")
            b.setStyleSheet("font-size:16pt; padding:4px 0; text-align:center;" if collapsed else "")

    def _toggle_side(self):
        self._set_side(not self.cfg.get("side_collapsed", False))

    def _side_menu(self, gpos):
        acts = [(f"{e}  {s}", lambda _=False, i=i: self._go(i)) for i, (e, s, _t) in enumerate(self.PAGES)]
        acts += [None, ("☰ Развернуть панель" if self.cfg.get("side_collapsed") else "☰ Свернуть панель",
                        self._toggle_side)]
        _menu(self, acts).exec(gpos)

    def _status(self, text):
        self.status_lbl.setText(text)

    def _set_busy(self, title):
        self.pill.setText(f"● {title}…")
        self.pill.setStyleSheet(f"color:{_WARN};")
        for b in self.busy_btns:
            b.setEnabled(False)

    def _done(self):
        self.pill.setText("● готов")
        self.pill.setStyleSheet(f"color:{_OK};")
        for b in self.busy_btns:
            b.setEnabled(True)

    def _drain_log(self):
        for _ in range(500):
            try:
                item = LOGQ.get_nowait()
            except queue.Empty:
                break
            if item is _DONE_SENTINEL:
                self._done()
            elif callable(item):
                try:
                    item()
                except Exception as e:
                    log.error(f"✗ UI: {e}", exc_info=True)
            else:
                self._append(str(item))

    def _append(self, line):
        self._log_lines.append(line)
        sb = self.logw.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 4
        self._render_line(line)
        if at_bottom:
            sb.setValue(sb.maximum())

    def _render_line(self, line):
        """Цвет — из текущей темы; при смене темы лог перерисовывается (_rerender_log)."""
        fmt = QTextCharFormat()
        p = _QT_THEMES[self.cfg.get("theme", "dark")]
        fmt.setForeground(QColor(_ERR if ("✗" in line or "⛔" in line) else _WARN if "⚠" in line
                                 else _OK if ("✓" in line or "✅" in line)
                                 else p["muted"] if line[8:12] == "  · " else p["log_fg"]))
        cur = QTextCursor(self.logw.document())
        cur.movePosition(QTextCursor.End)
        if not self.logw.document().isEmpty():
            cur.insertBlock()
        cur.insertText(line, fmt)

    def _rerender_log(self):
        sb = self.logw.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 4
        pos = sb.value()
        self.logw.setUpdatesEnabled(False)
        self.logw.clear()
        for line in self._log_lines:
            self._render_line(line)
        self.logw.setUpdatesEnabled(True)
        sb.setValue(sb.maximum() if at_bottom else pos)

    def _log_clear(self):
        self._log_lines.clear()
        self.logw.clear()

    def _log_menu(self, pos):
        def save():
            fn, _ = QFileDialog.getSaveFileName(self, "Сохранить лог", str(APP_ROOT / "winfix_log.txt"), "*.txt")
            if fn:
                Path(fn).write_text(self.logw.toPlainText(), "utf-8")
        _menu(self, [("📋 Копировать", self.logw.copy),
                     ("📋 Копировать всё", lambda: _copy(self.logw.toPlainText())),
                     ("Выделить всё", self.logw.selectAll), None,
                     ("🔬 Подробно в окне: " + ("вкл" if self.cfg.get("log_verbose") else "выкл"),
                      lambda: self._set_verbose(not self.cfg.get("log_verbose"))),
                     ("📄 Открыть файл лога", lambda: shell_open(str(LOG_PATH))),
                     ("📁 Папка логов", lambda: shell_open(str(LOG_DIR))), None,
                     ("💾 Сохранить в файл…", save), ("🗑 Очистить окно", self._log_clear)]
              ).exec(self.logw.mapToGlobal(pos))

    def _set_verbose(self, on: bool):
        self.cfg["log_verbose"] = on
        set_verbose(on)
        if hasattr(self, "verbose_tg"):
            self.verbose_tg.setChecked(on)
        log.info(f"✓ Подробный лог в окне: {'вкл' if on else 'выкл'}")

    def _ask(self, text) -> bool:
        return QMessageBox.question(self, APP_NAME, text, QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No) == QMessageBox.Yes  # Enter = «Нет»

    def _sel_rows(self, t: QTableWidget):
        return sorted({i.row() for i in t.selectedIndexes()})

    def _refresh_light(self):
        self.cursor_refresh()
        self.sound_refresh()

    # ── 🖱 курсор ──
    def _page_cursor(self, pl):
        c, cl = _card("Текущая схема указателей")
        self.cur_scheme = _lab("—", "big")
        cl.addWidget(self.cur_scheme)
        self.cur_tbl = _table(["Роль", "Файл", "Статус"], 1)
        self.cur_tbl.customContextMenuRequested.connect(self._cur_menu)
        cl.addWidget(self.cur_tbl, 1)
        cl.addLayout(_row(_btn("♻ Вернуть стандартный курсор", "primary",
                               "Схема «Windows по умолчанию», размер 32, применяется сразу", self.cursor_reset),
                          _btn("🔄 Обновить", "", "Перечитать реестр", self.cursor_refresh),
                          _btn("🗑 Удалить авторские схемы", "danger",
                               "Удалить пользовательские схемы из списка «Схема»", self.cursor_drop),
                          _btn("🧩 Восстановить файлы", "", "Вернуть оригинальные aero_* из WinSxS в C:\\Windows\\Cursors",
                               self.cursor_files),
                          _btn("🖱 Свойства мыши", "", "main.cpl", lambda: shell_open("main.cpl"))))
        self.cur_size = Stepper(cursor_size_get(), 1, 15)
        self.cur_size.setToolTip("1 — стандартный размер (32 px), каждый шаг +16 px")
        self.cur_size.changed.connect(self._cur_size)
        cl.addLayout(_row(_lab("Размер указателя:"), self.cur_size,
                          _btn("1 — стандарт", "chip", "Вернуть обычный размер", lambda: self._cur_size(1, True)),
                          _btn("⚙ Параметры указателя", "chip", "ms-settings:easeofaccess-mousepointer",
                               lambda: shell_open("ms-settings:easeofaccess-mousepointer"))))
        cl.addWidget(_lab("✓ (системный) — встроенный курсор Windows, подменить его сборка не может. "
                          "⚠ — файл из C:\\Windows\\Cursors (сборка могла заменить сам файл). "
                          "✗ — чужой файл. Вернуть оригинальные файлы — 🛠 DISM + SFC.", "hint"))
        pl.addWidget(c, 1)

    def cursor_refresh(self):
        scheme, rows, custom = cursor_scan()
        self.cur_size.set_value(cursor_size_get())
        self.cur_scheme.setText(f"Схема: {scheme}" + (f"   ·   авторских схем: {len(custom)}" if custom else ""))
        t = self.cur_tbl
        t.setRowCount(len(rows))
        for r, (title, f, st, reg) in enumerate(rows):
            t.setItem(r, 0, _cell(title, tip=reg))
            t.setItem(r, 1, _cell(f))
            t.setItem(r, 2, _cell(ST_TEXT[st], ST_COLOR[st]))
        bad = sum(1 for x in rows if x[2] == "bad")
        warn = sum(1 for x in rows if x[2] == "warn")
        self._status("Курсор: " + (f"✗ чужих файлов {bad}" if bad else
                                   f"⚠ файлы C:\\Windows\\Cursors: {warn}" if warn else "✓ стандартный"))

    def _cur_size(self, n, set_widget=False):
        """Клики [−][+] копятся 400 мс, применяется последнее значение."""
        if set_widget:
            self.cur_size.set_value(n)
        self._size_timer.start(400)

    def _cur_size_apply(self):
        if self.worker.busy:
            return self._size_timer.start(300)
        n = self.cur_size.val

        def job():
            try:
                cursor_size_set(n)
            finally:
                ui(self._cur_size_sync)
        self.worker.run("размер курсора", job)

    def _cur_size_sync(self):
        if not self._size_timer.isActive():  # пока пользователь щёлкает — не мешаем
            self.cur_size.set_value(cursor_size_get())

    def cursor_files(self):
        if not self._ask("Вернуть оригинальные файлы курсоров из хранилища Windows (WinSxS)\n"
                         "в C:\\Windows\\Cursors? Подменённые сборкой файлы будут перезаписаны."):
            return

        def job():
            cursor_restore_files()
            ui(self.cursor_refresh)
        self.worker.run("восстановление файлов курсоров", job)

    def cursor_reset(self):
        def job():
            bad = cursor_files_tampered()
            if bad:
                log.warning(f"⚠ Сборка подменила файлы курсоров в C:\\Windows\\Cursors ({len(bad)}): "
                            + ", ".join(bad[:6]) + (" …" if len(bad) > 6 else ""))
                log.warning("⚠ Ставлю встроенные курсоры (не из файлов). Вернуть сами файлы — «🧩 Восстановить файлы»")
            cursor_reset()
            log.info("✓ Встроенный стандартный курсор Windows применён")
            ui(self.cursor_refresh)
        self.worker.run("сброс курсора", job)

    def cursor_drop(self):
        if self._ask("Удалить все пользовательские схемы курсоров?\n(Системные схемы Windows не трогаются.)"):
            def job():
                cursor_drop_schemes()
                log.info("✓ Авторские схемы удалены")
                ui(self.cursor_refresh)
            self.worker.run("удаление схем", job)

    def _cur_menu(self, pos):
        rows = self._sel_rows(self.cur_tbl)
        f = self.cur_tbl.item(rows[0], 1).text() if rows else ""
        _menu(self, [("♻ Вернуть стандартный курсор", self.cursor_reset),
                     ("📂 Показать файл", lambda: show_in_explorer(f)), None,
                     ("📋 Копировать строку", lambda: _copy(_table_text(self.cur_tbl, rows))),
                     ("📋 Копировать всё", lambda: _copy(_table_text(self.cur_tbl))),
                     ("🔎 Открыть в regedit", lambda: open_regedit(r"HKCU\Control Panel\Cursors")),
                     ("🔄 Обновить", self.cursor_refresh)]).exec(self.cur_tbl.viewport().mapToGlobal(pos))

    # ── 🔊 звук ──
    def _page_sound(self, pl):
        c, cl = _card("Звуки системных событий")
        self.snd_tbl = _table(["Событие", "Сейчас", "По умолчанию", "Статус"], 1)
        self.snd_tbl.customContextMenuRequested.connect(self._snd_menu)
        cl.addWidget(self.snd_tbl, 1)
        self.snd_toggle = Toggle("Мелодия запуска Windows")
        self.snd_toggle.setToolTip("DisableStartupSound в HKLM (нужны права администратора)")
        self.snd_toggle.clicked.connect(self._snd_toggle)
        cl.addLayout(_row(_btn("♻ Вернуть стандартные звуки", "primary",
                               "Все события: .Current = .Default, схема «По умолчанию»", self.sound_reset),
                          _btn("🔇 Без звука входа", "", "Вход, разблокировка, запуск — без звука", self.sound_mute),
                          _btn("🔄 Обновить", "", "", self.sound_refresh),
                          _btn("🔊 Панель «Звук»", "", "mmsys.cpl", lambda: shell_open("mmsys.cpl")),
                          self.snd_toggle))
        cl.addWidget(_lab("Если музыка играет не через «звуки Windows», а программой (плеер, .mp3, скрипт) — "
                          "она на странице 🚀 с пометкой 🎵.", "hint"))
        pl.addWidget(c, 1)

    def sound_refresh(self):
        rows, start_on = sound_scan()
        t = self.snd_tbl
        t.setRowCount(len(rows))
        for r, (title, cur, dflt, st, ev) in enumerate(rows):
            t.setItem(r, 0, _cell(title, tip=ev))
            t.setItem(r, 1, _cell(cur))
            t.setItem(r, 2, _cell(dflt))
            t.setItem(r, 3, _cell(ST_TEXT[st], ST_COLOR[st]))
            t.item(r, 0).setData(Qt.UserRole, ev)
        self.snd_toggle.setChecked(start_on)

    def sound_reset(self):
        def job():
            n = sound_reset_all()
            log.info(f"✓ Звуки сброшены на стандартные (изменено событий: {n})")
            ui(self.sound_refresh)
        self.worker.run("сброс звуков", job)

    def sound_mute(self):
        def job():
            for ev in ("WindowsLogon", "WindowsUnlock", "SystemStart"):
                sound_set(ev, False)
            log.info("✓ Звук входа отключён")
            ui(self.sound_refresh)
        self.worker.run("отключение звука входа", job)

    def _snd_toggle(self):
        on = self.snd_toggle.isChecked()

        def job():
            try:
                startup_sound_set(on)
                log.info(f"✓ Мелодия запуска Windows {'включена' if on else 'выключена'}")
            finally:
                ui(self.sound_refresh)  # тумблер = реальное значение из реестра
        if not self.worker.run("мелодия запуска", job):
            self.snd_toggle.setChecked(not on)

    def _snd_menu(self, pos):
        rows = self._sel_rows(self.snd_tbl)
        evs = [self.snd_tbl.item(r, 0).data(Qt.UserRole) for r in rows]
        f = self.snd_tbl.item(rows[0], 1).text() if rows else ""

        def setv(default):
            def job():
                for ev in evs:
                    sound_set(ev, default)
                log.info("✓ Готово")
                ui(self.sound_refresh)
            self.worker.run("звук события", job)

        def play():
            try:
                import winsound
                winsound.PlaySound(os.path.expandvars(f), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                log.warning(f"⚠ Не воспроизвести: {e}")
        _menu(self, [("▶ Прослушать", play), ("♻ Вернуть по умолчанию", lambda: setv(True)),
                     ("🔇 Без звука", lambda: setv(False)), None,
                     ("📂 Показать файл", lambda: show_in_explorer(f)),
                     ("📋 Копировать строку", lambda: _copy(_table_text(self.snd_tbl, rows))),
                     ("📋 Копировать всё", lambda: _copy(_table_text(self.snd_tbl))),
                     ("🔄 Обновить", self.sound_refresh)]).exec(self.snd_tbl.viewport().mapToGlobal(pos))

    # ── 🚀 автозагрузка ──
    def _page_startup(self, pl):
        c, cl = _card("Что запускается при входе")
        self.st_filter = QLineEdit()
        self.st_filter.setPlaceholderText("🔎 Фильтр: имя, команда, источник…")
        self.st_filter.textChanged.connect(self._st_fill)
        self.st_music = Toggle("Только 🎵 звук/плееры")
        self.st_music.clicked.connect(self._st_fill)
        top = QHBoxLayout()
        top.addWidget(self.st_filter, 1)
        top.addWidget(self.st_music)
        cl.addLayout(top)
        self.st_tbl = _table(["🎵", "Вкл", "Источник", "Имя", "Команда"], 4)
        self.st_tbl.customContextMenuRequested.connect(self._st_menu)
        cl.addWidget(self.st_tbl, 1)
        b_scan = _btn("🔎 Сканировать", "primary", "Реестр Run/RunOnce, папки автозагрузки, Планировщик", self.startup_refresh)
        self.busy_btns.append(b_scan)
        cl.addLayout(_row(b_scan, _btn("⏸ Отключить", "", "Как в диспетчере задач — обратимо", lambda: self._st_set(False)),
                          _btn("▶ Включить", "", "", lambda: self._st_set(True)),
                          _btn("🗑 Удалить", "danger", "Значение реестра / файл в removed_startup / задача", self._st_del),
                          _btn("📂 Расположение", "", "Показать файл в проводнике", self._st_show)))
        cl.addWidget(_lab("🎵 — похоже на музыку при входе (.mp3/.wav, плееры). Сначала «Отключить», "
                          "перезайти в Windows, и только если тихо — «Удалить».", "hint"))
        pl.addWidget(c, 1)

    def startup_refresh(self):
        def job():
            items = startup_scan()
            m = sum(1 for i in items if i["music"])
            log.info(f"✓ Автозагрузка: {len(items)} записей" + (f", ⚠ 🎵 подозрительных: {m}" if m else ""))
            ui(lambda: (setattr(self, "startup_items", items), self._st_fill()))
        self.worker.run("сканирование автозагрузки", job)

    def _st_visible(self):
        q = self.st_filter.text().lower().strip()
        return [i for i in self.startup_items
                if (not self.st_music.isChecked() or i["music"])
                and (not q or q in (i["name"] + i["cmd"] + i["src"]).lower())]

    def _st_fill(self):
        vis = self._st_visible()
        t = self.st_tbl
        t.setRowCount(len(vis))
        for r, it in enumerate(vis):
            col = _WARN if it["music"] else None
            t.setItem(r, 0, _cell("🎵" if it["music"] else ""))
            t.setItem(r, 1, _cell("✓" if it["on"] else "⏸", _OK if it["on"] else _ERR))
            t.setItem(r, 2, _cell(it["src"], tip=it.get("path", it["src"])))
            t.setItem(r, 3, _cell(it["name"], col))
            t.setItem(r, 4, _cell(it["cmd"], col))
            t.item(r, 0).setData(Qt.UserRole, it)
        self._status(f"Автозагрузка: {len(vis)} из {len(self.startup_items)}")

    def _st_sel(self):
        return [self.st_tbl.item(r, 0).data(Qt.UserRole) for r in self._sel_rows(self.st_tbl)]

    def _st_set(self, on):
        items = self._st_sel()
        if not items:
            return log.warning("⚠ Выберите строки")

        def job():
            for it in items:
                try:
                    startup_set_on(it, on)
                    log.info(f"✓ {'Включено' if on else 'Отключено'}: {it['name']}")
                except Exception as e:
                    log.error(f"✗ {it['name']}: {e}", exc_info=True)
            ui(self._st_fill)
        self.worker.run("автозагрузка", job)

    def _st_del(self):
        items = self._st_sel()
        if not items or not self._ask("Удалить из автозагрузки:\n\n" + "\n".join(i["name"] for i in items)
                                      + "\n\nФайлы будут перенесены в папку removed_startup."):
            return

        def job():
            for it in items:
                try:
                    startup_delete(it)
                    self.startup_items.remove(it)
                    log.info(f"✓ Удалено: {it['name']}")
                except Exception as e:
                    log.error(f"✗ {it['name']}: {e}", exc_info=True)
            ui(self._st_fill)
        self.worker.run("удаление", job)

    def _st_show(self):
        for it in self._st_sel()[:3]:
            show_in_explorer(it.get("file") or it["cmd"].split("   ←")[0])

    def _st_menu(self, pos):
        rows = self._sel_rows(self.st_tbl)
        items = self._st_sel()
        reg = items[0] if items and items[0]["kind"] in ("reg", "asetup") else None
        acts = [("⏸ Отключить", lambda: self._st_set(False)), ("▶ Включить", lambda: self._st_set(True)),
                ("🗑 Удалить…", self._st_del), None, ("📂 Показать файл", self._st_show)]
        if reg:
            acts.append(("🔎 Открыть в regedit", lambda: open_regedit(f"{reg['root']}\\{reg['path']}")))
        if items and items[0]["kind"] == "task":
            acts.append(("🗓 Планировщик заданий", lambda: shell_open("taskschd.msc")))
        if items and items[0]["kind"] == "svc":
            acts.append(("⚙ Службы", lambda: shell_open("services.msc")))
        acts += [None, ("📋 Копировать строку", lambda: _copy(_table_text(self.st_tbl, rows))),
                 ("📋 Копировать всё", lambda: _copy(_table_text(self.st_tbl))),
                 ("🔎 Сканировать заново", self.startup_refresh)]
        _menu(self, acts).exec(self.st_tbl.viewport().mapToGlobal(pos))

    # ── 🩺 реестр ──
    def _page_registry(self, pl):
        c, cl = _card("Типичные поломки и «твики» сборок")
        self.rg_tbl = _table(["Статус", "Проверка", "Сейчас", "Норма"], 2)
        self.rg_tbl.customContextMenuRequested.connect(self._rg_menu)
        cl.addWidget(self.rg_tbl, 1)
        b = _btn("🔎 Проверить", "primary", "", self.reg_check)
        self.busy_btns.append(b)
        cl.addLayout(_row(b, _btn("🛠 Исправить выбранное", "", "", lambda: self.reg_fix(selected=True)),
                          _btn("🛠 Исправить все ✗", "danger", "Только красные (критичные)", lambda: self.reg_fix(False))))
        cl.addWidget(_lab("✗ — явная поломка/блокировка. ⚠ — сборка «оптимизировала» (обновления, Defender, "
                          "hosts, прокси): исправляй, если хочешь вернуть как в чистой Windows. "
                          "Изменения HKLM требуют прав администратора; часть — перезагрузки.", "hint"))
        pl.addWidget(c, 1)

    def reg_check(self):
        def job():
            res = []
            for ch in self.checks:
                try:
                    ok, cur = ch["check"]()
                except Exception as e:
                    log.debug(f"проверка «{ch['title']}» упала", exc_info=True)
                    ok, cur = False, f"ошибка: {e}"
                log.debug(f"check «{ch['title']}»: ok={ok} сейчас={cur!r}")
                res.append(("ok" if ok else ch["level"], cur))
            bad = sum(1 for s, _ in res if s == "bad")
            warn = sum(1 for s, _ in res if s == "warn")
            log.info(f"{'⚠' if bad else '✓'} Реестр: проверок {len(res)}, ✗ {bad}, ⚠ {warn}")
            ui(lambda: self._rg_fill(res))
        self.worker.run("проверка реестра", job)

    def _rg_fill(self, res):
        self.check_res = res
        t = self.rg_tbl
        t.setRowCount(len(res))
        txt = {"ok": "✓ норма", "warn": "⚠ изменено", "bad": "✗ проблема"}
        for r, (ch, (st, cur)) in enumerate(zip(self.checks, res)):
            t.setItem(r, 0, _cell(txt[st], ST_COLOR[st]))
            t.setItem(r, 1, _cell(ch["title"], tip=ch["key"]))
            t.setItem(r, 2, _cell(cur))
            t.setItem(r, 3, _cell(ch["norm"]))

    def reg_fix(self, selected=True):
        if not self.check_res:
            return log.warning("⚠ Сначала «Проверить»")
        if selected:
            idx = [r for r in self._sel_rows(self.rg_tbl) if self.check_res[r][0] != "ok"]
        else:
            idx = [r for r, (s, _) in enumerate(self.check_res) if s == "bad"]
        if not idx:
            return log.info("✓ Исправлять нечего")
        if not self._ask("Исправить:\n\n" + "\n".join(self.checks[i]["title"] for i in idx)):
            return

        def job():
            for i in idx:
                ch = self.checks[i]
                try:
                    ch["fix"]()
                    log.info(f"✓ Исправлено: {ch['title']}")
                except Exception as e:
                    log.error(f"✗ {ch['title']}: {e}", exc_info=True)
            log.info("⚠ Часть изменений вступит в силу после перезагрузки")
        self.worker.run("исправление реестра", job, then=self.reg_check)

    def _rg_menu(self, pos):
        rows = self._sel_rows(self.rg_tbl)
        key = self.checks[rows[0]]["key"] if rows else ""
        acts = [("🛠 Исправить", lambda: self.reg_fix(True)),
                ("🔎 Открыть в regedit", lambda: open_regedit(key) if key.startswith("HK") else show_in_explorer(key)),
                None, ("📋 Копировать строку", lambda: _copy(_table_text(self.rg_tbl, rows))),
                ("📋 Копировать всё", lambda: _copy(_table_text(self.rg_tbl))), ("🔎 Проверить заново", self.reg_check)]
        _menu(self, acts).exec(self.rg_tbl.viewport().mapToGlobal(pos))

    # ── 🌐 порты ──
    def _page_ports(self, pl):
        c, cl = _card("Открытые порты (netstat)")
        self.pt_filter = QLineEdit()
        self.pt_filter.setPlaceholderText("🔎 Фильтр: порт, процесс, адрес…")
        self.pt_filter.textChanged.connect(self._pt_fill)
        self.pt_listen = Toggle("Только прослушиваемые")
        self.pt_listen.setChecked(bool(self.cfg.get("ports_listen_only", True)))
        self.pt_listen.clicked.connect(self._pt_fill)
        top = QHBoxLayout()
        top.addWidget(self.pt_filter, 1)
        top.addWidget(self.pt_listen)
        cl.addLayout(top)
        self.pt_tbl = _table(["Протокол", "Адрес", "Порт", "Удалённый", "Состояние", "PID", "Процесс", "Заметка"], 7)
        self.pt_tbl.customContextMenuRequested.connect(self._pt_menu)
        cl.addWidget(self.pt_tbl, 1)
        b = _btn("🔎 Сканировать", "primary", "", self.ports_refresh)
        self.busy_btns.append(b)
        cl.addLayout(_row(b, _btn("🧱 Заблокировать порт", "", "Входящее правило брандмауэра", lambda: self._pt_rule(True)),
                          _btn("🔓 Снять блок", "", "Удалить правило WinFix", lambda: self._pt_rule(False)),
                          _btn("🛡 Брандмауэр", "", "wf.msc", lambda: shell_open("wf.msc"))))
        cl.addWidget(_lab("Жёлтым — порты, которые часто атакуют снаружи (SMB 445, RDP 3389, NetBIOS, VNC…). "
                          "0.0.0.0 / [::] — слушает на всех сетях, 127.0.0.1 — только локально (безопасно).", "hint"))
        pl.addWidget(c, 1)

    def ports_refresh(self):
        def job():
            rows = ports_scan()
            lis = [r for r in rows if r["listen"]]
            risky = sorted({r["port"] for r in lis if r["port"] in RISKY and not r["addr"].startswith(("127.", "[::1]"))})
            log.info(f"✓ Порты: всего {len(rows)}, слушают {len(lis)}"
                     + (f"  ⚠ рискованные: {', '.join(f'{p} {RISKY[p]}' for p in risky)}" if risky else ""))
            ui(lambda: (setattr(self, "port_rows", rows), self._pt_fill()))
        self.worker.run("сканирование портов", job)

    def _pt_fill(self):
        self.cfg["ports_listen_only"] = self.pt_listen.isChecked()
        q = self.pt_filter.text().lower().strip()
        vis = [r for r in self.port_rows if (r["listen"] or not self.pt_listen.isChecked())
               and (not q or q in f"{r['port']} {r['name']} {r['addr']} {r['remote']} {r['pid']}".lower())]
        t = self.pt_tbl
        t.setSortingEnabled(False)
        t.setRowCount(len(vis))
        for i, r in enumerate(vis):
            local = r["addr"].startswith(("127.", "[::1]"))
            note = RISKY.get(r["port"], "")
            col = _WARN if note and r["listen"] and not local else None
            vals = [r["proto"], r["addr"], r["port"], r["remote"], r["state"], r["pid"], r["name"],
                    (note + (" · только локально" if local else " · открыт в сеть")) if note else ""]
            for c, v in enumerate(vals):
                it = _cell(v, col)
                if c in (2, 5):
                    it.setData(Qt.DisplayRole, int(v) if str(v).isdigit() else v)
                t.setItem(i, c, it)
            t.item(i, 0).setData(Qt.UserRole, r)
        t.setSortingEnabled(True)
        self._status(f"Порты: показано {len(vis)}")

    def _pt_sel(self):
        return [self.pt_tbl.item(r, 0).data(Qt.UserRole) for r in self._sel_rows(self.pt_tbl)]

    def _pt_rule(self, block):
        rows = self._pt_sel()
        if not rows:
            return log.warning("⚠ Выберите порт")
        ports = sorted({(r["proto"], r["port"]) for r in rows})
        if block and not self._ask("Заблокировать входящие подключения:\n" + ", ".join(f"{p} {n}" for p, n in ports)
                                   + "\n\nЕсли порт нужен программе (игра, сетевой диск) — она перестанет работать."):
            return

        def job():
            for proto, port in ports:
                name = port_rule(proto, port)
                args = (["netsh", "advfirewall", "firewall", "add", "rule", f"name={name}", "dir=in", "action=block",
                         f"protocol={proto}", f"localport={port}"] if block else
                        ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"])
                code, out, err = run_cmd(args)
                (log.info if code == 0 else log.error)(
                    f"{'✓' if code == 0 else '✗'} {'Блок' if block else 'Снят блок'} {proto} {port}"
                    + ("" if code == 0 else f": {(out or err).strip()}"))
        self.worker.run("брандмауэр", job)

    def _pt_menu(self, pos):
        rows = self._sel_rows(self.pt_tbl)
        sel = self._pt_sel()

        def open_proc():
            if sel:
                def job():
                    _c, out, _ = run_ps(f"(Get-Process -Id {int(sel[0]['pid'])}).Path")
                    show_in_explorer(out.strip())
                self.worker.run("папка процесса", job)

        def kill():
            if sel and self._ask(f"Завершить процесс {sel[0]['name']} (PID {sel[0]['pid']})?"):
                def job():
                    code, out, err = run_cmd(["taskkill", "/PID", str(sel[0]["pid"]), "/F"])
                    (log.info if code == 0 else log.error)(("✓ " if code == 0 else "✗ ") + (out or err).strip())
                self.worker.run("завершение процесса", job, then=self.ports_refresh)
        _menu(self, [("🧱 Заблокировать порт", lambda: self._pt_rule(True)),
                     ("🔓 Снять блок WinFix", lambda: self._pt_rule(False)), None,
                     ("📂 Папка процесса", open_proc), ("⛔ Завершить процесс…", kill), None,
                     ("📋 Копировать строку", lambda: _copy(_table_text(self.pt_tbl, rows))),
                     ("📋 Копировать всё", lambda: _copy(_table_text(self.pt_tbl))),
                     ("🔎 Сканировать заново", self.ports_refresh)]).exec(self.pt_tbl.viewport().mapToGlobal(pos))

    # ── 🛠 система ──
    def _page_system(self, pl):
        c, cl = _card("Проверка системных файлов")
        b1 = _btn("⚡ DISM + SFC", "primary", "Сначала восстановить хранилище, затем проверить файлы (20–40 мин)",
                  lambda: self.sys_scan(True, True))
        b2 = _btn("DISM", "", "DISM /Online /Cleanup-Image /RestoreHealth", lambda: self.sys_scan(True, False))
        b3 = _btn("SFC", "", "sfc /scannow", lambda: self.sys_scan(False, True))
        self.busy_btns += [b1, b2, b3]
        cl.addLayout(_row(b1, b2, b3))
        cl.addWidget(_lab("Возвращает оригинальные системные файлы (в т.ч. подменённые курсоры, звуки, темы). "
                          "Нужен интернет и права администратора.", "hint"))
        pl.addWidget(c)

        c, cl = _card("Восстановление")
        b4 = _btn("💾 Точка восстановления", "", "Создать перед правками", self.sys_restore_point)
        self.busy_btns.append(b4)
        cl.addLayout(_row(b4, _btn("🔄 Перезапустить Проводник", "", "", self.sys_explorer),
                          _btn("⏻ Перезагрузка", "danger", "", self.sys_reboot)))
        pl.addWidget(c)

        c, cl = _card("Панели Windows")
        chips = [("🖱 Мышь", "main.cpl"), ("🔊 Звук", "mmsys.cpl"), ("⚙ Службы", "services.msc"),
                 ("🗓 Планировщик", "taskschd.msc"), ("🛡 Брандмауэр", "wf.msc"), ("🧬 Regedit", "regedit.exe"),
                 ("📦 Программы", "appwiz.cpl"), ("♻ Восстановление", "rstrui.exe")]
        cl.addLayout(_row(*[_btn(t, "chip", cmd, lambda _=False, x=cmd: shell_open(x)) for t, cmd in chips]))
        pl.addWidget(c)

        c, cl = _card("Проверенные утилиты (GitHub / Microsoft)")
        tools = [("WinUtil (Chris Titus) — твики, откат, ремонт", "https://github.com/ChrisTitusTech/winutil", True),
                 ("Sophia Script — тонкая настройка/откат Windows 10/11", "https://github.com/farag2/Sophia-Script-for-Windows", False),
                 ("Autoruns — всё, что стартует с системой", "https://learn.microsoft.com/sysinternals/downloads/autoruns", False),
                 ("TCPView — порты и соединения вживую", "https://learn.microsoft.com/sysinternals/downloads/tcpview", False)]
        for title, url, run in tools:
            ws = [_lab(title), _btn("🌐 Открыть", "chip", url, lambda _=False, u=url: webbrowser.open(u))]
            if run:
                ws.append(_btn("⚡ Запустить", "chip", "irm christitus.com/win | iex  (PowerShell от админа)",
                               self.sys_winutil))
            cl.addLayout(_row(*ws))
        pl.addWidget(c)
        pl.addStretch(1)

    def sys_scan(self, dism, sfc):
        def job():
            if dism:
                log.info("⏳ DISM /RestoreHealth …")
                code = run_stream(["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"], log.info)
                (log.info if code == 0 else log.error)(f"{'✓' if code == 0 else '✗'} DISM завершён, код {code}")
            if sfc:
                log.info("⏳ sfc /scannow …")
                code = run_stream(["sfc", "/scannow"], log.info)
                (log.info if code == 0 else log.warning)(f"{'✓' if code == 0 else '⚠'} SFC завершён, код {code}"
                                                         " (подробно: C:\\Windows\\Logs\\CBS\\CBS.log)")
        self.worker.run("проверка системы", job)

    def sys_restore_point(self):
        def job():
            if not is_admin():
                raise PermissionError
            code, out, err = run_ps(RESTORE_POINT_PS, 300)
            if "RP_OK" in out:
                log.info("✓ Точка восстановления создана")
            else:
                msg = (out.replace("RP_WARN", "").strip() or err.strip() or f"код {code}")[:300]
                log.error(f"✗ Точка не создана: {msg}")
        self.worker.run("точка восстановления", job)

    def sys_explorer(self):
        def job():
            run_cmd(["taskkill", "/F", "/IM", "explorer.exe"])
            for _ in range(8):  # Winlogon обычно сам перезапускает оболочку (AutoRestartShell)
                time.sleep(0.5)
                if _explorer_running():
                    return log.info("✓ Проводник перезапущен")
            if is_admin():  # из процесса администратора — запуск с обычными правами
                subprocess.Popen(["runas", "/trustlevel:0x20000", "explorer.exe"], creationflags=NOWIN)
                time.sleep(2)
            if not _explorer_running():
                subprocess.Popen(["explorer.exe"], creationflags=NOWIN)
            log.info("✓ Проводник перезапущен")
        self.worker.run("перезапуск проводника", job)

    def sys_reboot(self):
        if self._ask("Перезагрузить компьютер через 10 секунд?"):
            run_cmd(["shutdown", "/r", "/t", "10"])
            log.info("⚠ Перезагрузка через 10 с (отмена: shutdown /a)")

    def sys_winutil(self):
        if self._ask("Запустить WinUtil из интернета (PowerShell от администратора)?"):
            shell_open("powershell.exe", '-NoExit -NoProfile -ExecutionPolicy Bypass -Command "irm christitus.com/win | iex"',
                       admin=True)

    # ── 🎨 тема ──
    def _page_theme(self, pl):
        c, cl = _card("Тема")
        seg = Segmented([("dark", "🌙 Тёмная"), ("light", "☀ Светлая")], self.cfg.get("theme", "dark"))
        seg.changed.connect(self._apply_theme)
        cl.addWidget(seg)
        cl.addLayout(_row(_btn("💾 Сохранить", "primary", "", lambda: (save_config(self._cfg_snapshot()),
                                                                       log.info("✓ Настройки сохранены")))))
        cl.addWidget(_lab(f"{APP_NAME} v{VERSION} · настройки: {CONFIG_PATH}", "hint"))
        pl.addWidget(c)
        c, cl = _card("Логи")
        self.verbose_tg = Toggle("Подробно в окне (команды, реестр, коды)")
        self.verbose_tg.setChecked(bool(self.cfg.get("log_verbose")))
        self.verbose_tg.clicked.connect(lambda: self._set_verbose(self.verbose_tg.isChecked()))
        cl.addWidget(self.verbose_tg)
        cl.addLayout(_row(_btn("📄 Открыть лог", "", str(LOG_PATH), lambda: shell_open(str(LOG_PATH))),
                          _btn("📁 Папка логов", "", str(LOG_DIR), lambda: shell_open(str(LOG_DIR)))))
        cl.addWidget(_lab("В файл пишется всё всегда (DEBUG + traceback ошибок), 5 файлов по 2 МБ. "
                          "Если что-то не так — пришли logs/win_fix.log.", "hint"))
        pl.addWidget(c)
        pl.addStretch(1)

    def _apply_theme(self, name):
        name = name if name in _QT_THEMES else "dark"
        self.cfg["theme"] = name
        p = _QT_THEMES[name]
        _set_status_colors(p)
        app = QApplication.instance()
        app.setPalette(_palette(p))
        app.setStyleSheet(_qss(p))
        Toggle.set_theme(p["accent"], "#454b59" if name == "dark" else "#c3c8d2", p["text"])
        for w in self.findChildren(Toggle):
            w.update()
        if getattr(self, "_themed", False):  # перекрасить уже выведенное под новую тему
            self._rerender_log()
            self.cursor_refresh()
            self.sound_refresh()
            self._st_fill()
            self._pt_fill()
            if self.check_res:
                self._rg_fill(self.check_res)
        self._themed = True

    def _cfg_snapshot(self):
        self.cfg["geometry"] = bytes(self.saveGeometry().toBase64()).decode()
        self.cfg["splitter"] = bytes(self.split.saveState().toBase64()).decode()
        return self.cfg

    def closeEvent(self, e):
        if self.worker.busy and not self._ask("Ещё выполняется действие (" + self.pill.text().strip("● …")
                                              + ").\nПрервать и закрыть программу?"):
            return e.ignore()
        save_config(self._cfg_snapshot())
        log.debug("выход")
        super().closeEvent(e)


# ───────────────────────── запуск ─────────────────────────
def selftest() -> int:
    lines, ok = [], True
    try:
        import PySide6
        lines.append(f"PySide6 {PySide6.__version__}: ok")
        for fn in (cursor_scan, sound_scan, build_checks, _qss):
            assert callable(fn)
        assert len(build_checks()) > 10
        lines.append("логика: ok")
        app = QApplication.instance() or QApplication(sys.argv[:1])
        w = App()
        for theme in ("light", "dark"):
            w._apply_theme(theme)
            log.info(f"✓ selftest {theme}")
            w._drain_log()
        assert w.logw.document().blockCount() >= 2
        w.timer.stop()
        w.deleteLater()  # без closeEvent — config.json не трогаем
        app.processEvents()
        lines.append("окно и темы: ok")
    except Exception as e:
        ok = False
        lines.append(f"ОШИБКА: {e}")
    lines.append(f"{APP_NAME} v{VERSION} selftest: {'OK' if ok else 'FAIL'}")
    txt = "\n".join(lines)
    print(txt)
    try:
        (APP_ROOT / "selftest.txt").write_text(txt, "utf-8")
    except Exception:
        pass
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if IS_WIN and not is_admin() and "--no-admin" not in sys.argv:
        try:
            if elevate():
                sys.exit(0)
        except Exception:
            pass
    if IS_WIN:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WinFix.App")
        except Exception:
            pass
    install_crash_hooks()
    log_session_start()
    try:
        from PySide6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(lambda mode, ctx, msg: log.debug(f"Qt: {msg}"))
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
