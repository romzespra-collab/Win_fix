r"""
win_fix.py  v1.6.2
WinFix — ремонт Windows после «сборок»: курсор, звуки входа, автозагрузка
(музыка при входе), проверка реестра, открытые порты, DISM/SFC.

Журнал:
v1.6.2: чистка реестра: переключатель «⚠ Неподключённые диски — тоже мусор» (как CCleaner, запоминается);
        удаление ключа снимает запрет Deny (UserChoice у расширений) и пробует снова;
        «пустой класс» — ещё и классы только с описанием (без shell/CLSID/иконки), если на них не ссылается
        ни одно расширение (напр. Intel.GraphicsControlPanel.igp.1).
v1.6.1: ИСПРАВЛЕНО: удаление ключей реестра целиком не работало в Windows (RegDeleteTreeW через ctypes падал
        на 64-битном Python) — теперь рекурсивно через winreg; затрагивало чистку реестра (расширения, пустые
        ключи), меню Проводника, политики браузеров, остатки программ, ассоциацию .exe.
        Чистка: служебные ключи FileExts (DDECache, OpenWithList) больше не считаются расширениями;
        расширение не «неиспользуемое», если его открывает живая программа («Открыть с помощью»).
        Галочка в чекбоксах таблиц.
v1.6.0: 🧽 Чистка реестра (как в CCleaner): неиспользуемые расширения, неверный/пустой класс файлов, ошибки путей
        приложений (Compatibility Assistant, Layers, App Paths), ошибки установки (Installer\Folders), пустые
        программные ключи, правила брандмауэра на удалённые программы, устаревшие ссылки MUI, автозагрузка без
        файла, устаревшие записи установки, общие DLL; галочки, категории (запоминаются), всё — в ↩ Откат.
        Пути на неподключённых дисках (флешка, сеть) не считаются мусором: ⚠ и без галочки.
v1.5.0: 🗑 Программы — список установленных (HKLM/HKCU, 32/64), запуск деинсталлятора (MSI: /X) с ожиданием,
        поиск остатков: папка установки, Program Files/ProgramData/AppData (+ папка издателя), ярлыки,
        ключи реестра (+ ключ издателя), запись «Программы и компоненты», автозагрузка, службы и задачи из
        папки программы; ✗ точно / ⚠ похоже; системные папки и ключи (Microsoft, Common Files…) защищены;
        файлы — в backup\uninstall (↩ Откат вернёт), «Очистить backup\uninstall» освобождает место.
        Ряды кнопок переносятся на узком окне — без горизонтальной прокрутки (FlowLayout).
v1.4.0: ↩ Откат — каждое действие пишет старые значения (реестр, ключи целиком, файлы, ярлыки, задачи, DNS,
        исключения Defender) в backup/undo_*.json, откат одной кнопкой; 🪄 «Исправить всё» (точка → курсор →
        звуки → реестр ✗ → важные службы ✗); 📄 отчёт по всем проверкам (reports/*.txt); новые страницы:
        ⚙ Службы (отключённые сборкой), 🧭 Браузеры (ярлыки с сайтом, политики стартовой/поиска/расширений),
        📋 Меню Проводника (скрыть/показать/удалить пункты), 🏴 Активаторы (задачи, службы, файлы, IFEO,
        KMS-сервер, исключения Defender), 🌐 Сеть (DNS-серверы, сброс DNS/Winsock/TCP-IP/WinHTTP);
        оформление Windows: стандартная тема/обои, удаление OEM-сведений; проверки реестра: запреты обоев/темы/
        экрана блокировки; 🔄 проверка обновлений на GitHub; страницы прокручиваются; вкладка запоминается по имени.
v1.3.5: заблокированные кнопки выглядят заблокированными (и primary/danger), подсказка «недоступно: выполняется …»
        и строка «⏳ Выполняется» на странице 🛠; кнопка «⏹ Остановить» для DISM/SFC; ⏻ (нет в шрифтах) → 🔁.
v1.3.4: курсор: подмена файлов определяется сверкой SHA256 с оригиналом из WinSxS, а не только по владельцу —
        оригиналы, восстановленные прошлой версией (владелец «Администраторы»), больше не считаются подменой;
        файлы C:\Windows\Cursors (в т.ч. не aero_*) — ✓, если совпадают с оригиналом; сверка при запуске в фоне;
        «🧩 Восстановить файлы» возвращает владельца TrustedInstaller и уже оригинальным файлам.
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
VERSION = "1.6.2"
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

from PySide6.QtCore import QByteArray, QItemSelectionModel, QPoint, QRect, QRectF, QSize, Qt, QTimer, Signal  # noqa: E402
from PySide6.QtGui import (QAction, QColor, QFont, QGuiApplication, QPainter,  # noqa: E402
                           QPalette, QTextCharFormat, QTextCursor)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication,  # noqa: E402
                               QButtonGroup, QFileDialog, QFrame, QHBoxLayout,
                               QHeaderView, QLabel, QLayout, QLineEdit, QMainWindow, QMenu,
                               QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
                               QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem,
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


_STREAM = {"proc": None, "stopped": False}  # текущий DISM/SFC — для кнопки «⏹ Остановить»


def stop_stream() -> bool:
    p = _STREAM["proc"]
    if p and p.poll() is None:
        _STREAM["stopped"] = True
        log.warning(f"⚠ Останавливаю {p.args[0]} (PID {p.pid})…")
        run_cmd(["taskkill", "/PID", str(p.pid), "/T", "/F"]) if IS_WIN else p.kill()
        return True
    return False


def run_stream(args, on_line) -> int:
    """Потоковый вывод (DISM/SFC). SFC пишет в UTF-16 — определяем сами."""
    log.debug(f"$ {' '.join(args)}  (поток)")
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=NOWIN)
    _STREAM["proc"] = p
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


# ── журнал отката: всё, что меняет действие Worker, пишется в backup/undo_*.json ──
BACKUP_DIR = APP_ROOT / "backup"
_JOURNAL = threading.local()  # .ops — список операций текущего действия (None — не пишем)


def journal(op: dict) -> None:
    ops = getattr(_JOURNAL, "ops", None)
    if ops is not None:
        ops.append(op)


def _enc(v):
    return {"b64": base64.b64encode(v).decode()} if isinstance(v, (bytes, bytearray)) else v


def _dec(v):
    return base64.b64decode(v["b64"]) if isinstance(v, dict) and "b64" in v else v


def reg_get_raw(root, path, name):
    """(значение, тип) или None."""
    if not wr:
        return None
    try:
        with wr.OpenKey(HK[root], path, 0, wr.KEY_READ | W64) as k:
            return wr.QueryValueEx(k, name)
    except OSError:
        return None


def _journal_reg(root, path, name):
    if getattr(_JOURNAL, "ops", None) is None:
        return
    raw = reg_get_raw(root, path, name)
    journal({"t": "reg", "root": root, "path": path, "name": name,
             "old": None if raw is None else {"v": _enc(raw[0]), "type": raw[1]}})


def journal_file(path) -> None:
    """Запомнить содержимое файла до изменения."""
    try:
        journal({"t": "file", "path": str(path), "b64": base64.b64encode(Path(path).read_bytes()).decode()})
    except OSError:
        pass


def reg_set(root, path, name, value, typ=None):
    _need_reg()
    if typ is None:
        typ = wr.REG_DWORD if isinstance(value, int) else wr.REG_BINARY if isinstance(value, bytes) else wr.REG_SZ
    old = reg_get(root, path, name)
    _journal_reg(root, path, name)
    with wr.CreateKeyEx(HK[root], path, 0, wr.KEY_SET_VALUE | W64) as k:
        wr.SetValueEx(k, name, 0, typ, value)
    log.debug(f"REG SET {root}\\{path} [{name or '(по умолч.)'}]: {old!r} → {value!r}")


def reg_del(root, path, name) -> bool:
    _need_reg()
    try:
        with wr.OpenKey(HK[root], path, 0, wr.KEY_SET_VALUE | W64) as k:
            old = reg_get(root, path, name)
            if old is not None:
                _journal_reg(root, path, name)
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


def reg_dump(root, path) -> dict:
    """Ключ целиком (значения + подключи) — для отката удаления."""
    return {"values": [[n, _enc(v), t] for n, v, t in reg_values(root, path)],
            "keys": {k: reg_dump(root, rf"{path}\{k}") for k in reg_subkeys(root, path)}}


def reg_restore_tree(root, path, dump) -> None:
    with wr.CreateKeyEx(HK[root], path, 0, wr.KEY_SET_VALUE | W64) as k:
        for n, v, t in dump["values"]:
            wr.SetValueEx(k, n, 0, t, _dec(v))
    for sub, d in dump["keys"].items():
        reg_restore_tree(root, rf"{path}\{sub}", d)


def reg_delete_tree(root, path) -> None:
    _need_reg()
    log.debug(f"REG DELTREE {root}\\{path}")
    if getattr(_JOURNAL, "ops", None) is not None and reg_key_exists(root, path):
        journal({"t": "tree", "root": root, "path": path, "dump": reg_dump(root, path)})
    # только winreg: RegDeleteTreeW через ctypes на 64-битном Python падал (корень HKEY не влезал в int)

    def rm(p):
        for sub in reg_subkeys(root, p):
            rm(rf"{p}\{sub}")
        try:
            wr.DeleteKeyEx(HK[root], p, W64, 0)
        except FileNotFoundError:
            pass
        except PermissionError:
            if not IS_WIN:
                raise
            # UserChoice и т.п.: Windows ставит запрет (Deny) — снимаем его и пробуем ещё раз
            rp = ps_quote(f"Registry::{HK_FULL[root]}\\{p}")
            run_ps(f"$a=Get-Acl -LiteralPath {rp};$a.Access|?{{$_.AccessControlType -eq 'Deny'}}|"
                   f"%{{[void]$a.RemoveAccessRule($_)}};Set-Acl -LiteralPath {rp} -AclObject $a")
            log.debug(f"снят запрет Deny: {root}\\{p}")
            wr.DeleteKeyEx(HK[root], p, W64, 0)
    rm(path)
    if reg_key_exists(root, path):
        raise RuntimeError("ключ не удалён (нет прав?)")


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


def cursor_scan(bad_files=None):
    """bad_files — имена подменённых файлов в C:\\Windows\\Cursors (None — ещё не проверено)."""
    scheme = reg_get("HKCU", CUR_KEY, "") or "(без схемы)"
    rows = []
    sysdir = os.path.join(WINDIR, "cursors").lower() + "\\"
    for reg, title, std in CURSORS:
        v = reg_get("HKCU", CUR_KEY, reg) or ""
        full = os.path.expandvars(v)
        if not v:
            st = "ok"
        elif full.lower().startswith(sysdir):  # файл самой Windows: норма, если не подменён
            st = "warn" if bad_files is None or os.path.basename(full).lower() in bad_files else "ok"
        elif "\\microsoft\\windows\\cursors\\" in full.lower() and full.lower().endswith("_eoa.cur"):
            st = "ok"  # создаёт сама Windows (Параметры → Указатель мыши)
        else:
            st = "bad"
        rows.append((title, v or "(системный)", st, reg))
    custom = [n for n, _, _ in reg_values("HKCU", CUR_KEY + r"\Schemes")]
    return scheme, rows, custom


# общие куски PowerShell: поиск оригиналов в WinSxS, владелец, права как у оригинала
_CUR_PS_LIB = r"""
$dst = Join-Path $env:SystemRoot 'Cursors'
function Find-Src { Get-ChildItem (Join-Path $env:SystemRoot 'WinSxS') -Directory -ErrorAction SilentlyContinue |
  ?{ Test-Path (Join-Path $_.FullName 'aero_arrow.cur') } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
function Get-Owner($p){ $o = ((Get-Acl $p).Owner) -replace '^O:',''
  if($o -match '^S-1-'){ try{ $o = (New-Object Security.Principal.SecurityIdentifier($o)).Translate([Security.Principal.NTAccount]).Value }catch{} }
  $o }
function Is-TI($o){ $o -match 'TrustedInstaller' -or $o -eq 'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464' }
function Set-OrigAcl($t){
  icacls "$t" /inheritance:r /grant:r 'NT SERVICE\TrustedInstaller:F' '*S-1-5-32-544:RX' '*S-1-5-18:RX' `
    '*S-1-5-32-545:RX' '*S-1-15-2-1:RX' | Out-Null
  icacls "$t" /setowner 'NT SERVICE\TrustedInstaller' | Out-Null
  $LASTEXITCODE -eq 0 }
"""

CURSOR_CHECK_PS = _CUR_PS_LIB + r"""
$suspect = @(Get-ChildItem $dst -File | ?{ $_.Extension -in '.cur','.ani' -and -not (Is-TI (Get-Owner $_.FullName)) })
if(-not $suspect){ exit 0 }
$hit = Find-Src
foreach($f in $suspect){
  $src = if($hit){ Join-Path $hit.FullName $f.Name }
  if($src -and (Test-Path $src) -and (Get-FileHash $src).Hash -eq (Get-FileHash $f.FullName).Hash){ 'OWNER ' + $f.Name }
  elseif(-not $src -or -not (Test-Path $src)){ 'NOREF ' + $f.Name + ' (' + (Get-Owner $f.FullName) + ')' }
  else{ 'BAD ' + $f.Name + ' (' + (Get-Owner $f.FullName) + ')' }
}
"""


def cursor_files_check():
    """Сверка файлов C:\\Windows\\Cursors с оригиналами WinSxS (только тех, у кого владелец не TrustedInstaller).
    → (подменены, только_владелец). Оригинальный файл с другим владельцем — НЕ подмена."""
    if not IS_WIN:
        return [], []
    code, out, _ = run_ps(CURSOR_CHECK_PS, timeout=600)
    lines = [x.strip() for x in out.splitlines() if x.strip()]
    bad = [x[4:] for x in lines if x.startswith("BAD ")]
    owner = [x[6:] for x in lines if x.startswith("OWNER ")]
    noref = [x[6:] for x in lines if x.startswith("NOREF ")]
    for x in noref:
        log.debug(f"нет оригинала в WinSxS для сверки: {x}")
    return bad, owner


def bad_names(bad) -> set:
    return {x.split(" (")[0].lower() for x in bad}


CURSOR_RESTORE_PS = _CUR_PS_LIB + r"""
$hit = Find-Src
if(-not $hit){ 'NOSRC'; exit 2 }
'SRC ' + $hit.FullName
foreach($f in Get-ChildItem $hit.FullName -File | ?{ $_.Extension -in '.cur','.ani' }){
  $t = Join-Path $dst $f.Name
  if((Test-Path $t) -and (Get-FileHash $t).Hash -eq (Get-FileHash $f.FullName).Hash){
    if(Is-TI (Get-Owner $t)){ 'SAME ' + $f.Name }
    elseif(Set-OrigAcl $t){ 'ACL ' + $f.Name } else { 'OWNER ' + $f.Name }   # оригинал, но владелец не тот
    continue
  }
  try{
    if(Test-Path $t){
      takeown /f "$t" /a | Out-Null
      icacls "$t" /grant '*S-1-5-32-544:F' | Out-Null
    }
    Copy-Item $f.FullName $t -Force -ErrorAction Stop
    if(-not (Set-OrigAcl $t)){ 'OWNER ' + $f.Name }
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
    acl = [x for x in lines if x.startswith("ACL ")]
    for x in lines:
        if x.startswith("SRC "):
            log.info(f"   источник: {x[4:]}")
    log.info(f"✓ Восстановлено файлов: {len(ok)}, уже оригинальных: {len(same) + len(acl)}"
             + (f" (у {len(acl)} возвращён владелец TrustedInstaller)" if acl else ""))
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
        tp, tn = ps_quote(it['tpath']), ps_quote(it['name'])
        code, _o, err = run_ps(f"{verb}-ScheduledTask -TaskPath {tp} -TaskName {tn}")
        if code:
            raise RuntimeError(err.strip() or "нет прав (нужен администратор)")
        journal({"t": "ps", "what": f"задача {it['name']}",
                 "undo": f"{'Disable' if on else 'Enable'}-ScheduledTask -TaskPath {tp} -TaskName {tn}"})
    elif it["kind"] == "svc":
        svc_start_set(it["svc"], 2 if on else 4)
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
        move_journaled(it["file"], target)
        log.info(f"   файл перенесён: {target}")
    else:
        task_delete(it["tpath"], it["name"])


def move_journaled(src, dst) -> None:
    shutil.move(str(src), str(dst))  # между дисками os.replace не работает
    journal({"t": "move", "src": str(src), "dst": str(dst)})


def task_delete(tpath, name) -> None:
    """Удалить задачу Планировщика; XML сохраняется в журнал — откат пересоздаст её."""
    tp, tn = ps_quote(tpath), ps_quote(name)
    _c, xml, _e = run_ps(f"Export-ScheduledTask -TaskPath {tp} -TaskName {tn}")
    code, _o, err = run_ps(f"Unregister-ScheduledTask -TaskPath {tp} -TaskName {tn} -Confirm:$false")
    if code:
        raise RuntimeError(err.strip() or "нет прав")
    if xml.strip():
        journal({"t": "ps", "what": f"задача {name}",
                 "undo": f"Register-ScheduledTask -TaskPath {tp} -TaskName {tn} -Xml {ps_quote(xml)} -Force"})


SVC_KEY = r"SYSTEM\CurrentControlSet\Services"


def svc_start_set(name: str, start: int, delayed: int | None = None) -> None:
    """Тип запуска службы через реестр (пишется в журнал отката). 2 авто, 3 вручную, 4 отключена."""
    reg_set("HKLM", rf"{SVC_KEY}\{name}", "Start", int(start))
    if delayed is not None:
        reg_set("HKLM", rf"{SVC_KEY}\{name}", "DelayedAutostart", int(delayed))


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
    journal_file(HOSTS)
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
    for root, path, name, title in [
            ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop", "NoChangingWallPaper",
             "Запрет смены обоев"),
            ("HKCU", POL_EXP, "NoThemesTab", "Запрет смены темы"),
            ("HKCU", POL_SYS, "Wallpaper", "Принудительные обои (политика)"),
            ("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "LockScreenImage",
             "Принудительный экран блокировки"),
            ("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoChangingLockScreen",
             "Запрет смены экрана блокировки")]:
        chk, fix = _policy_check(root, path, name)
        add(title, "нет / 0", chk, fix, level="warn", key=f"{root}\\{path}")
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


# ───────────────────────── журнал отката ─────────────────────────
def save_journal(title: str, ops) -> None:
    if not ops:
        return
    try:
        BACKUP_DIR.mkdir(exist_ok=True)
        f = _unique(BACKUP_DIR / f"undo_{int(time.time() * 1000)}.json")  # мс — порядок даже в одну секунду
        f.write_text(json.dumps({"title": title, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "ops": ops},
                                ensure_ascii=False, indent=1), "utf-8")
        log.debug(f"журнал отката: {f.name} ({len(ops)} изм.)")
    except Exception:
        log.warning("⚠ Журнал отката не сохранён", exc_info=True)


def journal_list() -> list:
    out = []
    for f in sorted(BACKUP_DIR.glob("undo_*.json"), reverse=True) if BACKUP_DIR.is_dir() else []:
        try:
            d = json.loads(f.read_text("utf-8"))
            out.append(dict(file=str(f), title=d.get("title", "?"), time=d.get("time", ""), n=len(d.get("ops", [])),
                            done=bool(d.get("undone"))))
        except Exception:
            log.debug(f"битый журнал {f}", exc_info=True)
    return out


def journal_undo(path: str) -> None:
    """Откатить одно действие: операции в обратном порядке. Сам откат в журнал не пишется."""
    f = Path(path)
    d = json.loads(f.read_text("utf-8"))
    if d.get("undone"):
        raise RuntimeError("уже откачено")
    errors = 0
    for op in reversed(d["ops"]):
        try:
            t = op["t"]
            if t == "reg":
                if op["old"] is None:
                    reg_del(op["root"], op["path"], op["name"])
                else:
                    reg_set(op["root"], op["path"], op["name"], _dec(op["old"]["v"]), op["old"]["type"])
            elif t == "tree":
                reg_restore_tree(op["root"], op["path"], op["dump"])
            elif t == "file":
                Path(op["path"]).write_bytes(base64.b64decode(op["b64"]))
            elif t == "move":
                shutil.move(op["dst"], op["src"])
            elif t == "ps":
                code, _o, err = run_ps(op["undo"])
                if code:
                    raise RuntimeError(err.strip()[:200] or f"код {code}")
            log.debug(f"откат: {op.get('t')} {op.get('path') or op.get('what') or ''}")
        except Exception as e:
            errors += 1
            log.error(f"✗ откат {op.get('t')} {op.get('path') or op.get('what') or ''}: {e}")
    d["undone"] = time.strftime("%Y-%m-%d %H:%M:%S")
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
    (log.warning if errors else log.info)(f"{'⚠' if errors else '✓'} Откачено: {d['title']} "
                                          f"({len(d['ops']) - errors} из {len(d['ops'])})")


# ───────────────────────── службы ─────────────────────────
# имя: (название, запуск по умолчанию, отложенный, важная)
SERVICES = {
    "Audiosrv": ("Аудио Windows", 2, 0, True), "AudioEndpointBuilder": ("Построитель аудио", 2, 0, True),
    "Themes": ("Темы", 2, 0, True), "WSearch": ("Поиск Windows", 2, 1, True), "Dnscache": ("DNS-клиент", 2, 0, True),
    "Dhcp": ("DHCP-клиент", 2, 0, True), "NlaSvc": ("Сетевое расположение", 2, 0, True),
    "netprofm": ("Список сетей", 3, 0, True), "Wcmsvc": ("Диспетчер подключений", 2, 0, True),
    "WlanSvc": ("Wi-Fi", 2, 0, True), "LanmanWorkstation": ("Рабочая станция", 2, 0, True),
    "mpssvc": ("Брандмауэр", 2, 0, True), "WinDefend": ("Антивирус Defender", 2, 0, True),
    "wscsvc": ("Центр безопасности", 2, 1, True), "SecurityHealthService": ("Безопасность Windows", 3, 0, True),
    "EventLog": ("Журнал событий", 2, 0, True), "Schedule": ("Планировщик заданий", 2, 0, True),
    "CryptSvc": ("Криптография", 2, 0, True), "Winmgmt": ("WMI", 2, 0, True), "ProfSvc": ("Профили", 2, 0, True),
    "EventSystem": ("События COM+", 2, 0, True), "PlugPlay": ("Plug and Play", 3, 0, True),
    "Power": ("Питание", 2, 0, True), "Appinfo": ("Сведения о приложениях (UAC)", 3, 0, True),
    "wuauserv": ("Центр обновления", 3, 0, True), "BITS": ("Фоновая передача (BITS)", 3, 0, True),
    "UsoSvc": ("Оркестратор обновлений", 2, 1, False), "msiserver": ("Установщик Windows", 3, 0, True),
    "TrustedInstaller": ("Установщик модулей", 3, 0, True), "VSS": ("Теневое копирование", 3, 0, True),
    "Spooler": ("Печать", 2, 0, False), "bthserv": ("Bluetooth", 3, 0, False), "SysMain": ("SysMain", 2, 0, False),
    "FontCache": ("Кэш шрифтов", 2, 0, False), "LanmanServer": ("Сервер (общие папки)", 2, 0, False),
    "iphlpsvc": ("IP Helper", 2, 0, False), "WpnService": ("Уведомления", 2, 0, False),
    "ShellHWDetection": ("Автозапуск носителей", 2, 0, False), "stisvc": ("Сканеры и камеры", 3, 0, False),
    "WbioSrvc": ("Биометрия (Windows Hello)", 3, 0, False), "TabletInputService": ("Сенсорная клавиатура", 3, 0, False),
    "W32Time": ("Служба времени", 3, 0, False), "WerSvc": ("Отчёты об ошибках", 3, 0, False),
    "DiagTrack": ("Телеметрия", 2, 0, False), "DPS": ("Диагностика", 2, 0, False),
    "seclogon": ("Вторичный вход", 3, 0, False), "RasMan": ("Удалённый доступ", 3, 0, False),
    "AppXSvc": ("Магазин: развёртывание", 3, 0, False), "ClipSVC": ("Магазин: лицензии", 3, 0, False),
    "InstallService": ("Магазин: установка", 3, 0, False), "wlidsvc": ("Учётная запись Microsoft", 3, 0, False),
    "XblAuthManager": ("Xbox: вход", 3, 0, False), "SDRSVC": ("Архивация", 3, 0, False)}
START_TXT = {0: "загрузка", 1: "система", 2: "авто", 3: "вручную", 4: "отключена"}


def services_scan():
    rows = []
    for name, (title, dflt, delayed, important) in SERVICES.items():
        if not reg_key_exists("HKLM", rf"{SVC_KEY}\{name}"):
            continue
        cur = reg_get("HKLM", rf"{SVC_KEY}\{name}", "Start")
        if cur == 4 and dflt != 4:
            st = "bad" if important else "warn"
        else:
            st = "ok"
        rows.append(dict(name=name, title=title, cur=cur, dflt=dflt, delayed=delayed, important=important, st=st))
    return rows


def service_fix(r: dict) -> None:
    svc_start_set(r["name"], r["dflt"], r["delayed"] if r["dflt"] == 2 else None)


# ───────────────────────── браузеры и ярлыки ─────────────────────────
BROWSER_EXE = re.compile(r"\\(chrome|msedge|firefox|opera|launcher|browser|iexplore|vivaldi|brave|yandex)\.exe$", re.I)
URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|ru|net|org|info|xyz|top|club|online|site|pro|biz)"
                    r"(?:/\S*)?\b")
LNK_SCAN_PS = r"""
$sh = New-Object -ComObject WScript.Shell
$dirs = @([Environment]::GetFolderPath('Desktop'), "$env:PUBLIC\Desktop",
  "$env:APPDATA\Microsoft\Windows\Start Menu", "$env:ProgramData\Microsoft\Windows\Start Menu",
  "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch") | ?{ $_ -and (Test-Path $_) }
@($dirs | %{ Get-ChildItem $_ -Recurse -Filter *.lnk -ErrorAction SilentlyContinue } | %{
  $l = $sh.CreateShortcut($_.FullName); [pscustomobject]@{f=$_.FullName; t=$l.TargetPath; a=$l.Arguments} }) |
  ConvertTo-Json -Compress
"""
POLICY_BROWSERS = [(r"SOFTWARE\Policies\Google\Chrome", "Chrome"), (r"SOFTWARE\Policies\Microsoft\Edge", "Edge"),
                   (r"SOFTWARE\Policies\BraveSoftware\Brave", "Brave"), (r"SOFTWARE\Policies\YandexBrowser", "Яндекс"),
                   (r"SOFTWARE\Policies\Mozilla\Firefox", "Firefox"), (r"SOFTWARE\Policies\Opera Software\Opera", "Opera")]
POLICY_RED = re.compile(r"ExtensionInstallForcelist|ExtensionSettings|Extensions|DefaultSearch|SearchEngines|"
                        r"Homepage|RestoreOnStartup|NewTabPage|Proxy", re.I)


def lnk_clean_args(args: str) -> str:
    return re.sub(r"\s{2,}", " ", URL_RE.sub("", args or "")).strip()


def browsers_scan():
    items = []
    if IS_WIN:
        _c, out, _ = run_ps(LNK_SCAN_PS, timeout=120)
        try:
            res = json.loads(out or "[]")
            res = [res] if isinstance(res, dict) else res
        except Exception:
            res = []
        for r in res:
            if BROWSER_EXE.search(r.get("t") or "") and URL_RE.search(r.get("a") or ""):
                items.append(dict(kind="lnk", src="Ярлык", name=Path(r["f"]).name, file=r["f"],
                                  val=f"{r['t']} {r['a']}", st="bad"))
    for root in ("HKCU", "HKLM"):
        for base, br in POLICY_BROWSERS:
            if not reg_key_exists(root, base):
                continue
            for n, v, _t in reg_values(root, base):
                items.append(dict(kind="pol", src=f"{br} · политика {root}", name=n, root=root, path=base,
                                  val=str(v), st="bad" if POLICY_RED.search(n) else "warn"))
            for sub in reg_subkeys(root, base):
                vals = "; ".join(str(v) for _n, v, _t in reg_values(root, rf"{base}\{sub}"))[:300]
                items.append(dict(kind="polkey", src=f"{br} · политика {root}", name=sub + "\\", root=root,
                                  path=rf"{base}\{sub}", val=vals or "(ключ)",
                                  st="bad" if POLICY_RED.search(sub) else "warn"))
    return items


def browser_fix(it: dict) -> None:
    if it["kind"] == "lnk":
        journal_file(it["file"])
        new = lnk_clean_args(it["val"].split(" ", 1)[1] if " " in it["val"] else "")
        code, _o, err = run_ps(f"$s=New-Object -ComObject WScript.Shell;$l=$s.CreateShortcut({ps_quote(it['file'])});"
                               f"$l.Arguments={ps_quote(new)};$l.Save()")
        if code:
            raise RuntimeError(err.strip() or "ярлык не сохранён")
    elif it["kind"] == "pol":
        reg_del(it["root"], it["path"], it["name"])
    else:
        reg_delete_tree(it["root"], it["path"])


# ───────────────────────── контекстное меню Проводника ─────────────────────────
CTX_SHELL = [r"*\shell", r"AllFilesystemObjects\shell", r"Directory\shell", r"Directory\Background\shell",
             r"Folder\shell", r"Drive\shell", r"DesktopBackground\Shell"]
CTX_EX = [r"*\shellex\ContextMenuHandlers", r"AllFilesystemObjects\shellex\ContextMenuHandlers",
          r"Directory\shellex\ContextMenuHandlers", r"Directory\Background\shellex\ContextMenuHandlers",
          r"Folder\shellex\ContextMenuHandlers", r"Drive\shellex\ContextMenuHandlers"]
CTX_BUILTIN = {
    "open", "opennew", "explore", "find", "runas", "cmd", "powershell", "print", "printto", "edit", "pintohome",
    "pintostartscreen", "updateencryptionsettings", "updateencryptionsettingswork", "encrypt", "decrypt",
    "opennewprocess", "opennewtab", "opennewwindow", "openinsandbox", "display", "personalize", "properties",
    "sharing", "epp", "modernsharing", "open with", "open with encryptionmenu", "sendto", "workfolders",
    "copyaspathmenu", "library location", "offline files", "new", "folderredirect", "{596ab062-b4d2-4215-9f74-e9109b0a8153}",
    "{a2a9545d-a0c2-42b4-9708-a0b2badd77c8}", "{90aa3a4e-1cba-4233-b8bb-535773d48449}", "{e2bf9676-5f8f-435c-97eb-11607a5bedf7}",
    "{09a47860-11b0-4da5-afa5-26d86198a780}", "{7ad84985-87b4-4a16-be58-8b72a5b390f7}", "{b8cdcb65-b1bf-4b42-9428-1dfdb7ee92af}",
    "{f81e9010-6ea4-11ce-a7ff-00aa003ca9f6}", "{d969a300-e7ff-11d0-a93b-00a0c91e2ca2}", "{474c98ee-cf3d-41f5-80e3-4aab0ab04301}",
    "{5250e46f-bb09-d602-5891-f476dc89b700}", "{e82a2d71-5b2f-43a0-97b8-81be15854de8}", "{fbeb8a05-beee-4442-804e-409d6c4515e9}"}
BLOCKED = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Blocked"
GUID_RE = re.compile(r"^\{[0-9a-f-]{36}\}$", re.I)


def _clsid_dll(clsid: str) -> str:
    return str(reg_get("HKCR", rf"CLSID\{clsid}\InprocServer32", "") or reg_get("HKCR", rf"CLSID\{clsid}", "") or "")


def ctx_scan(show_builtin=False):
    items = []
    for base in CTX_SHELL:
        for verb in reg_subkeys("HKCR", base):
            if not show_builtin and verb.lower() in CTX_BUILTIN:
                continue
            key = rf"{base}\{verb}"
            title = reg_get("HKCR", key, "MUIVerb") or reg_get("HKCR", key, "") or verb
            cmd = reg_get("HKCR", key + r"\command", "") or ("(подменю)" if reg_get("HKCR", key, "SubCommands") is not None
                                                              or reg_key_exists("HKCR", key + r"\shell") else "")
            items.append(dict(kind="verb", where=base.split("\\")[0], name=verb, title=str(title), cmd=str(cmd),
                              path=key, on=reg_get("HKCR", key, "LegacyDisable") is None,
                              builtin=verb.lower() in CTX_BUILTIN))
    for base in CTX_EX:
        for h in reg_subkeys("HKCR", base):
            key = rf"{base}\{h}"
            clsid = h if GUID_RE.match(h) else str(reg_get("HKCR", key, "") or "")
            builtin = h.lower() in CTX_BUILTIN or clsid.lower() in CTX_BUILTIN
            if (not show_builtin and builtin) or not clsid:
                continue
            blocked = reg_get("HKLM", BLOCKED, clsid) is not None or reg_get("HKCU", BLOCKED, clsid) is not None
            items.append(dict(kind="ex", where=base.split("\\")[0], name=h, title=h, cmd=_clsid_dll(clsid),
                              clsid=clsid, path=key, on=not blocked, builtin=builtin))
    return items


def ctx_set_on(it: dict, on: bool) -> None:
    if it["kind"] == "verb":
        if on:
            reg_del("HKCR", it["path"], "LegacyDisable")
        else:
            reg_set("HKCR", it["path"], "LegacyDisable", "")
    else:
        if on:
            reg_del("HKLM", BLOCKED, it["clsid"])
            reg_del("HKCU", BLOCKED, it["clsid"])
        else:
            try:
                reg_set("HKLM", BLOCKED, it["clsid"], it["name"])
            except PermissionError:
                reg_set("HKCU", BLOCKED, it["clsid"], it["name"])
    it["on"] = on


# ───────────────────────── следы активаторов (KMS) ─────────────────────────
KMS_RE = r"kms|aact|autopico|kmspico|kms_?vl|kmseldi|secoh|ratiborus|w10digital|hwidgen|massgrave|activat"
KMS_PS = r"""
$re = '__RE__'
$o = @()
Get-ScheduledTask -ErrorAction SilentlyContinue | ?{ $_.TaskPath -notlike '\Microsoft\*' -and
  (($_.TaskName + ' ' + (($_.Actions | %{ $_.Execute + ' ' + $_.Arguments }) -join ' ')) -match $re) } |
  %{ $o += [pscustomobject]@{k='task'; n=$_.TaskName; p=$_.TaskPath;
     v=(($_.Actions | %{ $_.Execute + ' ' + $_.Arguments }) -join ' ; ')} }
Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | ?{ ($_.Name + ' ' + $_.DisplayName + ' ' + $_.PathName) -match $re -and
  $_.PathName -notmatch 'sppsvc|svchost' } | %{ $o += [pscustomobject]@{k='svc'; n=$_.Name; p=''; v=$_.PathName} }
@("$env:SystemRoot\SECOH-QAD.exe", "$env:SystemRoot\SECOH-QAD.dll", "$env:SystemRoot\System32\SppExtComObjHook.dll",
  "$env:SystemRoot\System32\SppExtComObjPatcher.exe", "$env:SystemRoot\AAct_Tools", "$env:SystemRoot\KMSAutoS",
  "$env:ProgramData\KMSAutoS", "$env:ProgramData\KMSAuto", "$env:ProgramData\KMSAuto Net",
  "$env:ProgramFiles\KMSpico", "${env:ProgramFiles(x86)}\KMSpico", "$env:ProgramData\Microsoft\AAct") |
  ?{ $_ -and (Test-Path $_) } | %{ $o += [pscustomobject]@{k='file'; n=(Split-Path $_ -Leaf); p=$_; v=$_} }
try { (Get-MpPreference -ErrorAction Stop).ExclusionPath | ?{ $_ } |
  %{ $o += [pscustomobject]@{k='mpex'; n=$_; p=''; v=$_} } } catch {}
@($o) | ConvertTo-Json -Compress
"""
SPP = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform"
OSPP = r"SOFTWARE\Microsoft\OfficeSoftwareProtectionPlatform"


def kms_scan():
    items = []
    if IS_WIN:
        _c, out, _ = run_ps(KMS_PS.replace("__RE__", KMS_RE), timeout=180)
        try:
            res = json.loads(out or "[]")
            res = [res] if isinstance(res, dict) else res
        except Exception:
            res = []
        kre = re.compile(KMS_RE, re.I)
        for r in res:
            k = r["k"]
            if k == "mpex":
                bad = bool(kre.search(r["n"])) or bool(re.match(r"(?i)^[a-z]:\\?$|^%?systemroot%?|.*\\windows\\?$", r["n"]))
                items.append(dict(kind="mpex", src="Исключение Defender", name=r["n"], val=r["v"],
                                  st="bad" if bad else "warn"))
            else:
                items.append(dict(kind=k, src={"task": "Задача", "svc": "Служба", "file": "Файл/папка"}[k],
                                  name=r["n"], path=r.get("p") or "", val=r.get("v") or "", st="bad"))
    for exe in ("SppExtComObj.exe", "sppsvc.exe", "osppsvc.exe"):
        for val in ("Debugger", "VerifierDlls"):
            v = reg_get("HKLM", rf"{IFEO}\{exe}", val)
            if v:
                items.append(dict(kind="reg", src="IFEO (перехват активации)", name=f"{exe} → {val}", root="HKLM",
                                  path=rf"{IFEO}\{exe}", rname=val, val=str(v), st="bad"))
    for key, title in ((SPP, "KMS-сервер Windows"), (OSPP, "KMS-сервер Office")):
        v = reg_get("HKLM", key, "KeyManagementServiceName")
        if v:
            local = bool(re.match(r"^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|localhost)", str(v)))
            items.append(dict(kind="reg", src=title, name="KeyManagementServiceName", root="HKLM", path=key,
                              rname="KeyManagementServiceName", val=str(v), st="bad" if local else "warn"))
    return items


def kms_delete(it: dict) -> None:
    k = it["kind"]
    if k == "task":
        task_delete(it["path"], it["name"])
    elif k == "svc":
        run_ps(f"Stop-Service -Name {ps_quote(it['name'])} -Force -ErrorAction SilentlyContinue")
        svc_start_set(it["name"], 4)  # сначала отключаем (откатывается), затем удаляем
        code, out, err = run_cmd(["sc", "delete", it["name"]])
        if code:
            raise RuntimeError((out or err).strip() or "служба не удалена")
        log.warning(f"⚠ Служба {it['name']} удалена — откат вернёт только тип запуска")
    elif k == "file":
        dst = BACKUP_DIR / "kms"
        dst.mkdir(parents=True, exist_ok=True)
        move_journaled(it["path"], _unique(dst / Path(it["path"]).name))
    elif k == "mpex":
        code, _o, err = run_ps(f"Remove-MpPreference -ExclusionPath {ps_quote(it['name'])} -ErrorAction Stop")
        if code:
            raise RuntimeError(err.strip() or "нет прав")
        journal({"t": "ps", "what": f"исключение {it['name']}",
                 "undo": f"Add-MpPreference -ExclusionPath {ps_quote(it['name'])}"})
    elif k == "reg":
        reg_del(it["root"], it["path"], it["rname"])


# ───────────────────────── сеть ─────────────────────────
DNS_KNOWN = {"1.1.1.1": "Cloudflare", "1.0.0.1": "Cloudflare", "8.8.8.8": "Google", "8.8.4.4": "Google",
             "9.9.9.9": "Quad9", "149.112.112.112": "Quad9", "77.88.8.8": "Яндекс", "77.88.8.1": "Яндекс",
             "77.88.8.88": "Яндекс", "77.88.8.2": "Яндекс", "208.67.222.222": "OpenDNS", "208.67.220.220": "OpenDNS",
             "94.140.14.14": "AdGuard", "94.140.15.15": "AdGuard", "76.76.2.0": "ControlD", "76.76.10.0": "ControlD"}
PRIVATE_RE = re.compile(r"^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|127\.|169\.254\.|fe80:|fec0:|::1|fd)", re.I)


def dns_scan():
    if not IS_WIN:
        return []
    _c, out, _ = run_ps("@(Get-DnsClientServerAddress -AddressFamily IPv4 | ?{ $_.ServerAddresses } | "
                        "%{[pscustomobject]@{i=$_.InterfaceIndex; a=$_.InterfaceAlias; s=@($_.ServerAddresses)}}) "
                        "| ConvertTo-Json -Compress -Depth 3")
    try:
        res = json.loads(out or "[]")
        res = [res] if isinstance(res, dict) else res
    except Exception:
        return []
    rows = []
    for r in res:
        srv = r["s"] if isinstance(r["s"], list) else [r["s"]]
        notes = [DNS_KNOWN.get(x) or ("локальный/роутер" if PRIVATE_RE.match(x) else "⚠ неизвестный") for x in srv]
        rows.append(dict(idx=r["i"], alias=r["a"], servers=srv, note=", ".join(notes),
                         st="warn" if any(n.startswith("⚠") for n in notes) else "ok"))
    return rows


def dns_reset(row: dict) -> None:
    code, _o, err = run_ps(f"Set-DnsClientServerAddress -InterfaceIndex {int(row['idx'])} -ResetServerAddresses")
    if code:
        raise RuntimeError(err.strip() or "нет прав")
    journal({"t": "ps", "what": f"DNS {row['alias']}",
             "undo": f"Set-DnsClientServerAddress -InterfaceIndex {int(row['idx'])} -ServerAddresses "
                     f"@({','.join(ps_quote(x) for x in row['servers'])})"})


NET_CMDS = {"flushdns": (["ipconfig", "/flushdns"], "Кэш DNS очищен"),
            "winsock": (["netsh", "winsock", "reset"], "Winsock сброшен (нужна перезагрузка)"),
            "tcpip": (["netsh", "int", "ip", "reset"], "TCP/IP сброшен (нужна перезагрузка)"),
            "winhttp": (["netsh", "winhttp", "reset", "proxy"], "Прокси WinHTTP сброшен")}


def net_cmd(key: str) -> None:
    args, ok = NET_CMDS[key]
    code, out, err = run_cmd(args)
    if code:
        raise RuntimeError((out or err).strip()[:300] or f"код {code}")
    log.info(f"✓ {ok}")


# ───────────────────────── оформление Windows ─────────────────────────
OEM_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\OEMInformation"
OEM_VALUES = ("Manufacturer", "Model", "Logo", "SupportURL", "SupportPhone", "SupportHours", "HelpCustomized")
WALLPAPER = Path(WINDIR) / r"Web\Wallpaper\Windows\img0.jpg"
THEME_FILE = Path(WINDIR) / r"Resources\Themes\aero.theme"


def oem_info() -> dict:
    return {n: reg_get("HKLM", OEM_KEY, n) for n in OEM_VALUES if reg_get("HKLM", OEM_KEY, n) not in (None, "")}


def oem_clear() -> None:
    for n in OEM_VALUES:
        reg_del("HKLM", OEM_KEY, n)


def wallpaper_default() -> None:
    _need_reg()
    reg_set("HKCU", r"Control Panel\Desktop", "Wallpaper", str(WALLPAPER))
    ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, str(WALLPAPER), 3)  # SPI_SETDESKWALLPAPER


# ───────────────────────── проверка обновлений ─────────────────────────
UPDATE_REPO = "romzespra-collab/Win_fix"


def _ver(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def update_check():
    """→ (последняя версия, url) или None, если релизов нет/нет доступа."""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest",
                                 headers={"User-Agent": f"{APP_NAME}/{VERSION}", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise RuntimeError(f"GitHub ответил {e.code}")
    return d.get("tag_name", ""), d.get("html_url") or f"https://github.com/{UPDATE_REPO}/releases"


# ───────────────────────── отчёт ─────────────────────────
REPORT_DIR = APP_ROOT / "reports"
_MARK = {"ok": "✓", "warn": "⚠", "bad": "✗"}


def build_report(checks) -> Path:
    import platform
    L = [f"{APP_NAME} v{VERSION} — отчёт", time.strftime("%Y-%m-%d %H:%M:%S"),
         f"{platform.platform()} · администратор: {'да' if is_admin() else 'нет'}", "=" * 70]

    def sec(title):
        L.extend(["", title, "-" * len(title)])

    def safe(title, fn):
        try:
            fn()
        except Exception as e:
            L.append(f"  ✗ раздел «{title}» не собран: {e}")

    def cur():
        sec("КУРСОР")
        bad, owner = cursor_files_check()
        scheme, rows, custom = cursor_scan(bad_names(bad))
        L.append(f"  схема: {scheme}; авторских схем: {len(custom)}; подменённых файлов: {len(bad)}")
        L.extend(f"  {_MARK[st]} {t}: {f}" for t, f, st, _r in rows)
        L.extend(f"  ✗ подменён файл: {x}" for x in bad)

    def snd():
        sec("ЗВУКИ")
        rows, start_on = sound_scan()
        L.append(f"  мелодия запуска: {'вкл' if start_on else 'выкл'}")
        L.extend(f"  {_MARK[st]} {t}: {c}" for t, c, _d, st, _e in rows)

    def regc():
        sec("РЕЕСТР")
        for ch in checks:
            try:
                ok, cur_ = ch["check"]()
            except Exception as e:
                ok, cur_ = False, f"ошибка: {e}"
            L.append(f"  {_MARK['ok' if ok else ch['level']]} {ch['title']}: {cur_}")

    def svc():
        sec("СЛУЖБЫ (отключённые)")
        rows = [r for r in services_scan() if r["st"] != "ok"]
        L.extend(f"  {_MARK[r['st']]} {r['title']} ({r['name']}): {START_TXT.get(r['cur'], r['cur'])}, "
                 f"норма — {START_TXT[r['dflt']]}" for r in rows)
        if not rows:
            L.append("  ✓ всё в норме")

    def st():
        sec("АВТОЗАГРУЗКА")
        items = startup_scan()
        L.append(f"  записей: {len(items)}")
        L.extend(f"  🎵 {i['src']} · {i['name']}: {i['cmd']}" for i in items if i["music"])
        L.extend(f"  · {i['src']} · {i['name']} [{'вкл' if i['on'] else 'выкл'}]: {i['cmd'][:150]}" for i in items
                 if not i["music"])

    def br():
        sec("БРАУЗЕРЫ И ЯРЛЫКИ")
        items = browsers_scan()
        L.extend(f"  {_MARK[i['st']]} {i['src']} · {i['name']}: {i['val'][:200]}" for i in items)
        if not items:
            L.append("  ✓ подмен не найдено")

    def ctx():
        sec("МЕНЮ ПРОВОДНИКА (сторонние пункты)")
        items = ctx_scan()
        L.extend(f"  {'·' if i['on'] else '⏸'} {i['where']} · {i['title']}: {i['cmd'][:150]}" for i in items)
        if not items:
            L.append("  ✓ сторонних пунктов нет")

    def kms():
        sec("СЛЕДЫ АКТИВАТОРОВ")
        items = kms_scan()
        L.extend(f"  {_MARK[i['st']]} {i['src']} · {i['name']}: {i['val'][:200]}" for i in items)
        if not items:
            L.append("  ✓ не найдено")

    def net():
        sec("СЕТЬ")
        L.extend(f"  {_MARK[r['st']]} {r['alias']}: {', '.join(r['servers'])} ({r['note']})" for r in dns_scan())
        rows = ports_scan()
        risky = sorted({(r["port"], r["name"]) for r in rows if r["listen"] and r["port"] in RISKY
                        and not r["addr"].startswith(("127.", "[::1]"))})
        L.extend(f"  ⚠ открыт порт {p} {RISKY[p]} ({n})" for p, n in risky)

    def oem():
        sec("OEM-СВЕДЕНИЯ")
        info = oem_info()
        L.extend(f"  ⚠ {k}: {v}" for k, v in info.items())
        if not info:
            L.append("  ✓ пусто")

    for title, fn in (("курсор", cur), ("звуки", snd), ("реестр", regc), ("службы", svc), ("автозагрузка", st),
                      ("браузеры", br), ("меню", ctx), ("активаторы", kms), ("сеть", net), ("OEM", oem)):
        log.info(f"   отчёт: {title}…")
        safe(title, fn)
    REPORT_DIR.mkdir(exist_ok=True)
    f = REPORT_DIR / f"winfix_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    f.write_text("\r\n".join(L) + "\r\n", "utf-8-sig")
    return f


# ───────────────────────── мастер «исправить всё» ─────────────────────────
def fix_all(checks) -> None:
    """Точка восстановления → курсор → звуки → реестр (✗) → важные службы (✗). Один журнал — один откат.
    Ошибка одного шага не останавливает остальные."""
    def restore_point():
        if not is_admin():
            return log.warning("⚠ Без прав администратора — точка пропущена, HKLM не исправится")
        _c, out, err = run_ps(RESTORE_POINT_PS, 300)
        if "RP_OK" in out:
            log.info("✓ Точка восстановления создана")
        else:
            log.warning(f"⚠ Точка не создана: {(out.replace('RP_WARN', '').strip() or err.strip())[:200]}")

    def cursor():
        cursor_reset()
        log.info("✓ Курсор стандартный")

    def sounds():
        log.info(f"✓ Звуки: изменено событий {sound_reset_all()}")

    def registry():
        n = 0
        for ch in checks:
            try:
                ok, _cur = ch["check"]()
                if not ok and ch["level"] == "bad":
                    ch["fix"]()
                    n += 1
                    log.info(f"✓ Исправлено: {ch['title']}")
            except Exception as e:
                log.error(f"✗ {ch['title']}: {e}")
        log.info(f"✓ Реестр: исправлено {n}")

    def services():
        n = 0
        for r in services_scan():
            if r["st"] == "bad":
                try:
                    service_fix(r)
                    n += 1
                    log.info(f"✓ Служба {r['title']}: {START_TXT[r['dflt']]}")
                except Exception as e:
                    log.error(f"✗ Служба {r['title']}: {e}")
        log.info(f"✓ Службы: исправлено {n}")

    steps = (("Точка восстановления", restore_point), ("Курсор", cursor), ("Звуки", sounds),
             ("Реестр (только ✗)", registry), ("Важные службы", services))
    for i, (title, fn) in enumerate(steps, 1):
        log.info(f"⏳ {i}/{len(steps)} {title}…")
        try:
            fn()
        except PermissionError:
            log.error(f"✗ {title}: нет прав — запустите от администратора")
        except Exception as e:
            log.error(f"✗ {title}: {e}", exc_info=True)
    log.info("✅ Готово. Откатить всё разом — страница ↩ Откат. Часть изменений — после перезагрузки.")


# ───────────────────────── удаление программ ─────────────────────────
UNINST_KEYS = [("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
               ("HKLM", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
               ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Uninstall")]
# папки/ключи, которые никогда не предлагаются к удалению целиком
PROTECT = {"microsoft", "windows", "commonfiles", "windowsapps", "packages", "temp", "programs", "microsoftnet",
           "windowsdefender", "windowspowershell", "internetexplorer", "windowsnt", "classes", "policies",
           "wow6432node", "clients", "registeredapplications", "intel", "nvidia", "nvidiacorporation", "amd", "google",
           "mozilla", "oracle", "java", "python", "packagecache", "installer", "systemprofile", "start menu",
           "startmenu", "desktop", "documents", "default", "public", "users", "appdata", "local", "roaming",
           "locallow", "crashdumps", "d3dscache", "connecteddevicesplatform", "comms", "history", "inetcache"}
NAME_STOP = {"the", "for", "and", "x64", "x86", "bit", "64bit", "32bit", "version", "edition", "setup", "update",
             "версия", "free", "pro", "app", "application", "programs", "program", "software", "tools", "tool"}


def _norm(s: str) -> str:
    return re.sub(r"[^0-9a-zа-яё+#]", "", (s or "").lower())


def _app_key(name: str) -> str:
    """«Notepad++ (64-bit x64) 8.6.2» → «notepad++»."""
    s = re.sub(r"\(.*?\)|\bv?\d+(\.\d+)+\b|\b(x64|x86|64-bit|32-bit|64 bit|32 bit)\b", " ", name or "", flags=re.I)
    return _norm(s)


def _words(name: str) -> list:
    return [w for w in re.findall(r"[0-9a-zа-яё+#]{4,}", (name or "").lower()) if w not in NAME_STOP]


def uninstall_list() -> list:
    out, seen = [], set()
    for root, base in UNINST_KEYS:
        for sub in reg_subkeys(root, base):
            k = rf"{base}\{sub}"
            g = lambda n: reg_get(root, k, n)  # noqa: E731
            name = g("DisplayName")
            if not name or g("SystemComponent") == 1 or g("ParentKeyName") or \
                    str(g("ReleaseType") or "").lower() in ("update", "hotfix", "security update"):
                continue
            ident = (str(name).lower(), str(g("DisplayVersion") or ""))
            if ident in seen:
                continue
            seen.add(ident)
            date = str(g("InstallDate") or "")
            out.append(dict(name=str(name), ver=str(g("DisplayVersion") or ""), pub=str(g("Publisher") or ""),
                            loc=str(g("InstallLocation") or "").strip().strip('"').rstrip("\\"),
                            cmd=str(g("UninstallString") or ""), quiet=str(g("QuietUninstallString") or ""),
                            icon=str(g("DisplayIcon") or ""), size=int(g("EstimatedSize") or 0) // 1024,
                            date=f"{date[:4]}-{date[4:6]}-{date[6:8]}" if re.fullmatch(r"\d{8}", date) else "",
                            root=root, key=k, src="пользователь" if root == "HKCU" else
                            ("32-бит" if "WOW6432" in base else "все")))
    out.sort(key=lambda a: a["name"].lower())
    return out


def _install_dir(app: dict) -> str:
    """Папка программы: InstallLocation, иначе папка деинсталлятора/иконки (если это не корень Program Files)."""
    cands = [app["loc"], os.path.dirname(exe_from_cmd(app["cmd"])), os.path.dirname(exe_from_cmd(app["icon"].split(",")[0]))]
    for c in cands:
        c = (c or "").rstrip("\\")
        if c and os.path.isdir(c) and _norm(os.path.basename(c)) not in PROTECT and len(Path(c).parts) >= 3 \
                and "\\windows\\" not in c.lower() + "\\" and "msiexec" not in c.lower():
            return c
    return ""


def uninstall_run(app: dict, quiet: bool = False) -> None:
    """Запустить деинсталлятор программы и дождаться, пока её запись исчезнет из реестра."""
    cmd = (app["quiet"] if quiet and app["quiet"] else app["cmd"]).strip()
    if not cmd:
        raise RuntimeError("у программы нет деинсталлятора — используйте «🔎 Найти остатки»")
    if re.search(r"msiexec", cmd, re.I):
        cmd = re.sub(r"(?i)/I\s*(\{)", r"/X\1", cmd)
    log.info(f"⏳ Деинсталлятор: {cmd}")
    p = subprocess.Popen(cmd if IS_WIN else cmd.split())
    p.wait()
    log.debug(f"деинсталлятор завершён, код {p.returncode}")
    for _ in range(90):  # Inno/NSIS перезапускают себя из TEMP — ждём исчезновения записи до 3 мин
        if not reg_key_exists(app["root"], app["key"]):
            return log.info(f"✓ {app['name']}: удалена деинсталлятором")
        time.sleep(2)
    log.warning(f"⚠ {app['name']}: запись в реестре осталась (деинсталлятор отменён или не до конца)")


def _dir_size(path: str, limit: float = 3.0) -> int:
    total, t0 = 0, time.time()
    for r, _d, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
        if time.time() - t0 > limit:
            break
    return total


def _human(n: int) -> str:
    for u in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024:
            return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} ТБ"


def leftovers_scan(app: dict) -> list:
    """Остатки программы. st: bad — точно её (совпадение имени/папки), warn — похоже, проверьте."""
    key, words, pub = _app_key(app["name"]), _words(app["name"]), _norm(app["pub"])
    inst = _install_dir(app)
    items, seen = [], set()

    def add(kind, path, st, why, **kw):
        if path.lower() in seen:
            return
        seen.add(path.lower())
        items.append(dict(kind=kind, path=path, st=st, why=why, **kw))

    def match(name: str) -> str:
        n = _norm(name)
        if not n or n in PROTECT or n == pub:
            return ""
        if n == key or (len(key) >= 5 and (n.startswith(key) or (len(n) >= 5 and key.startswith(n)))):
            return "bad"
        if words and len(words[0]) >= 5 and n == _norm(words[0]):
            return "warn"
        return ""

    if inst:
        add("dir", inst, "bad", "папка установки")
    env = os.environ.get
    bases = [env("ProgramFiles", r"C:\Program Files"), env("ProgramFiles(x86)", r"C:\Program Files (x86)"),
             env("ProgramData", r"C:\ProgramData"), env("APPDATA", ""), env("LOCALAPPDATA", ""),
             os.path.join(env("LOCALAPPDATA", ""), "Programs"), os.path.join(env("USERPROFILE", ""), "AppData", "LocalLow"),
             os.path.join(env("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
             os.path.join(env("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs")]
    for b in bases:
        if not b or not os.path.isdir(b):
            continue
        try:
            children = list(os.scandir(b))
        except OSError:
            continue
        for e in children:
            st = match(e.name)
            if st:
                add("dir" if e.is_dir() else "file", e.path, st, "имя совпадает")
            elif e.is_dir() and pub and _norm(e.name) == pub:  # Издатель\Программа
                try:
                    subs = list(os.scandir(e.path))
                except OSError:
                    continue
                hits = [s for s in subs if match(s.name)]
                for s in hits:
                    add("dir" if s.is_dir() else "file", s.path, match(s.name), "папка издателя → программа")
                if (hits and len(hits) == len(subs)) or not subs:
                    add("dir", e.path, "warn", "папка издателя (пустая без программы)")
    # ярлыки на рабочих столах
    for d in (os.path.join(env("USERPROFILE", ""), "Desktop"), os.path.join(env("PUBLIC", ""), "Desktop")):
        if os.path.isdir(d):
            for e in os.scandir(d):
                if e.name.lower().endswith(".lnk") and match(e.name[:-4]):
                    add("file", e.path, "warn", "ярлык")
    # реестр
    for root, base in (("HKCU", "Software"), ("HKLM", "SOFTWARE"), ("HKLM", r"SOFTWARE\WOW6432Node")):
        for sub in reg_subkeys(root, base):
            st = match(sub)
            if st:
                add("reg", rf"{root}\{base}\{sub}", st, "ключ программы", root=root, rpath=rf"{base}\{sub}")
            elif pub and _norm(sub) == pub:
                subs = reg_subkeys(root, rf"{base}\{sub}")
                hits = [s for s in subs if match(s)]
                for s in hits:
                    add("reg", rf"{root}\{base}\{sub}\{s}", match(s), "ключ издателя → программа", root=root,
                        rpath=rf"{base}\{sub}\{s}")
                if (hits and len(hits) == len(subs)) or not (subs or reg_values(root, rf"{base}\{sub}")):
                    add("reg", rf"{root}\{base}\{sub}", "warn", "ключ издателя (пустой без программы)", root=root,
                        rpath=rf"{base}\{sub}")
    if reg_key_exists(app["root"], app["key"]):
        add("reg", rf"{app['root']}\{app['key']}", "warn", "запись «Программы и компоненты»", root=app["root"],
            rpath=app["key"])
    # автозагрузка, службы, задачи — по папке установки
    if inst and IS_WIN:
        il = inst.lower()
        for root, path, _appr in RUN_KEYS:
            for n, v, _t in reg_values(root, path):
                if n and il in os.path.expandvars(str(v)).lower():
                    add("regval", rf"{root}\{path}\{n}", "bad", "автозагрузка", root=root, rpath=path, rname=n)
        _c, out, _ = run_ps(
            f"$p={ps_quote(il)};@(Get-CimInstance Win32_Service | ?{{ $_.PathName -and $_.PathName.ToLower().Contains($p) }} |"
            " %{[pscustomobject]@{k='svc';n=$_.Name;v=$_.PathName}}) + @(Get-ScheduledTask | ?{ (($_.Actions | "
            "%{ $_.Execute + ' ' + $_.Arguments }) -join ' ').ToLower().Contains($p) } | "
            "%{[pscustomobject]@{k='task';n=$_.TaskName;p=$_.TaskPath;v=(($_.Actions|%{$_.Execute}) -join ' ; ')}}) "
            "| ConvertTo-Json -Compress", timeout=120)
        try:
            res = json.loads(out or "[]")
            for r in [res] if isinstance(res, dict) else res:
                if r["k"] == "svc":
                    add("svc", f"служба {r['n']}", "bad", r["v"], name=r["n"])
                else:
                    add("task", f"задача {r.get('p', '')}{r['n']}", "bad", r["v"], name=r["n"], tpath=r.get("p", "\\"))
        except Exception:
            log.debug("службы/задачи программы не прочитаны", exc_info=True)
    for it in items:
        it["size"] = _human(_dir_size(it["path"])) if it["kind"] == "dir" else \
            (_human(os.path.getsize(it["path"])) if it["kind"] == "file" and os.path.exists(it["path"]) else "")
    items.sort(key=lambda i: (i["st"] != "bad", i["kind"], i["path"].lower()))
    return items


def leftover_delete(it: dict, app_name: str) -> None:
    """Файлы и папки переносятся в backup\\uninstall (откат вернёт), ключи реестра — с копией в журнале."""
    k = it["kind"]
    if k in ("dir", "file"):
        dst = BACKUP_DIR / "uninstall" / (_norm(app_name)[:40] or "app")
        dst.mkdir(parents=True, exist_ok=True)
        move_journaled(it["path"], _unique(dst / Path(it["path"]).name))
    elif k == "reg":
        reg_delete_tree(it["root"], it["rpath"])
    elif k == "regval":
        reg_del(it["root"], it["rpath"], it["rname"])
    elif k == "svc":
        run_ps(f"Stop-Service -Name {ps_quote(it['name'])} -Force -ErrorAction SilentlyContinue")
        svc_start_set(it["name"], 4)
        code, out, err = run_cmd(["sc", "delete", it["name"]])
        if code:
            raise RuntimeError((out or err).strip() or "служба не удалена")
    elif k == "task":
        task_delete(it["tpath"], it["name"])


def backup_size() -> int:
    return _dir_size(str(BACKUP_DIR / "uninstall"), 5) if (BACKUP_DIR / "uninstall").is_dir() else 0


# ───────────────────────── чистка реестра (как CCleaner) ─────────────────────────
RC_CATS = [("fileexts", "Неиспользуемые расширения файлов"), ("badclass", "Неверный или пустой класс файлов"),
           ("apppaths", "Ошибки путей приложений"), ("installer", "Ошибки установки приложений"),
           ("software", "Пустой программный ключ"), ("firewall", "Неверное правило брандмауэра"),
           ("mui", "Устаревшие ссылки MUI"), ("run", "Автозагрузка: файла нет"),
           ("uninst", "Устаревшая запись установки"), ("shareddll", "Отсутствующие общие DLL")]
RC_TITLE = dict(RC_CATS)
FILEEXTS = r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts"
MUICACHE = r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"
COMPAT_STORE = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store"
COMPAT_LAYERS = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
APP_PATHS = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
INSTALLER_FOLDERS = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\Folders"
FW_RULES = r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules"
SHARED_DLLS = r"SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDLLs"


def _path_state(p: str) -> str:
    """ok — есть; missing — нет; nodrive — диск не подключён (флешка/сеть): не трогаем; skip — не путь."""
    p = os.path.expandvars(str(p or "").strip().strip('"')).rstrip("\\") or ""
    if not p or p.startswith(("@", "\\\\?\\", "\\Device", "%")) or "://" in p:
        return "skip"
    drive, _rest = os.path.splitdrive(p)
    if drive.startswith("\\\\"):  # сетевой путь — сеть может быть недоступна
        return "nodrive" if not os.path.exists(drive + "\\") else ("ok" if os.path.exists(p) else "missing")
    if IS_WIN and not drive:
        return "skip"
    if drive and not os.path.exists(drive + "\\"):
        return "nodrive"
    return "ok" if os.path.exists(p) else "missing"


def _rc_item(cat, data, root, path, op, name=None, state="missing"):
    nodrive = state == "nodrive"
    return dict(cat=cat, title=RC_TITLE[cat], data=str(data), key=rf"{root}\{path}" + (f"\\{name}" if name else ""),
                root=root, path=path, name=name, op=op, st="warn" if nodrive else "bad",
                note="диск не подключён (флешка/сеть) — не отмечено" if nodrive else "")


def _ext_used(ext: str) -> bool:
    """Расширение кому-то нужно: есть класс в HKCR, выбор по умолчанию или «Открыть с помощью» живой программой."""
    if reg_key_exists("HKCR", ext):
        return True
    base = rf"{FILEEXTS}\{ext}"
    uc = reg_get("HKCU", base + r"\UserChoice", "ProgId")
    if uc and reg_key_exists("HKCR", uc):
        return True
    for n, _v, _t in reg_values("HKCU", base + r"\OpenWithProgids"):
        if n and reg_key_exists("HKCR", n):
            return True
    for n, v, _t in reg_values("HKCU", base + r"\OpenWithList"):
        if n.lower() != "mrulist" and isinstance(v, str) and v and reg_key_exists("HKCR", rf"Applications\{v}"):
            return True
    return False


def regclean_scan(cats=None) -> list:
    cats = set(cats or dict(RC_CATS))
    out = []

    def add(*a, **kw):
        out.append(_rc_item(*a, **kw))

    if "fileexts" in cats:
        for ext in reg_subkeys("HKCU", FILEEXTS):
            if ext == "." or (ext.startswith(".") and not _ext_used(ext)):  # DDECache, OpenWithList — служебные
                add("fileexts", ext, "HKCU", rf"{FILEEXTS}\{ext}", "tree")
    if "badclass" in cats:
        keys = reg_subkeys("HKCR", "")
        used = set()  # на какие классы ссылаются расширения
        for k in keys:
            if k.startswith("."):
                prog = reg_get("HKCR", k, "")
                if isinstance(prog, str) and prog.strip():
                    used.add(prog.lower())
                    if not reg_key_exists("HKCR", prog):
                        add("badclass", f"{k} → {prog}", "HKCR", k, "defval")
                used.update(n.lower() for n, _v, _t in reg_values("HKCR", rf"{k}\OpenWithProgids"))
        for k in keys:
            if "." in k and not k.startswith((".", "*", "{")) and k.lower() not in used \
                    and not reg_subkeys("HKCR", k) \
                    and {n.lower() for n, _v, _t in reg_values("HKCR", k)} <= {"", "friendlytypename", "editflags", "infotip"}:
                add("badclass", k, "HKCR", k, "tree")
    if "apppaths" in cats:
        for root in ("HKCU", "HKLM"):
            store = COMPAT_STORE if root == "HKCU" else None
            for base in filter(None, (store, COMPAT_LAYERS)):
                for n, _v, _t in reg_values(root, base):
                    s = _path_state(n)
                    if s in ("missing", "nodrive"):
                        add("apppaths", n, root, base, "val", name=n, state=s)
            ap = APP_PATHS if root == "HKLM" else r"Software\Microsoft\Windows\CurrentVersion\App Paths"
            for exe in reg_subkeys(root, ap):
                v = reg_get(root, rf"{ap}\{exe}", "")
                s = _path_state(v)
                if s in ("missing", "nodrive"):
                    add("apppaths", v, root, rf"{ap}\{exe}", "tree", state=s)
    if "installer" in cats:
        for n, _v, _t in reg_values("HKLM", INSTALLER_FOLDERS):
            s = _path_state(n)
            if s in ("missing", "nodrive"):
                add("installer", n, "HKLM", INSTALLER_FOLDERS, "val", name=n, state=s)
    if "software" in cats:
        for k in reg_subkeys("HKCU", "Software"):
            if _norm(k) not in PROTECT and not reg_values("HKCU", rf"Software\{k}") and \
                    not reg_subkeys("HKCU", rf"Software\{k}"):
                add("software", k, "HKCU", rf"Software\{k}", "tree")
    if "firewall" in cats:
        for n, v, _t in reg_values("HKLM", FW_RULES):
            m = re.search(r"\|App=([^|]+)", str(v))
            if m:
                s = _path_state(m.group(1))
                if s in ("missing", "nodrive"):
                    rn = re.search(r"\|Name=([^|]+)", str(v))
                    add("firewall", f"{n} — {m.group(1)}" + (f" ({rn.group(1)})" if rn else ""), "HKLM", FW_RULES,
                        "val", name=n, state=s)
    if "mui" in cats:
        for n, _v, _t in reg_values("HKCU", MUICACHE):
            if n.startswith("@") or "." not in n:
                continue
            path = n.rsplit(".", 1)[0]  # «C:\x\app.exe.FriendlyAppName» → «C:\x\app.exe»
            s = _path_state(path)
            if s in ("missing", "nodrive"):
                add("mui", n, "HKCU", MUICACHE, "val", name=n, state=s)
    if "run" in cats:
        for root, path, _appr in RUN_KEYS:
            for n, v, _t in reg_values(root, path):
                exe = exe_from_cmd(str(v))
                if n and os.path.isabs(os.path.expandvars(exe)):
                    s = _path_state(exe)
                    if s in ("missing", "nodrive"):
                        add("run", f"{n}: {v}", root, path, "val", name=n, state=s)
    if "uninst" in cats:
        for root, base in UNINST_KEYS:
            for sub in reg_subkeys(root, base):
                k = rf"{base}\{sub}"
                cmd = str(reg_get(root, k, "UninstallString") or "")
                if not cmd or re.search(r"msiexec", cmd, re.I) or reg_get(root, k, "SystemComponent") == 1:
                    continue
                exe = exe_from_cmd(cmd)
                loc = str(reg_get(root, k, "InstallLocation") or "").strip().strip('"')
                s = _path_state(exe)
                if s in ("missing", "nodrive") and (not loc or _path_state(loc) != "ok"):
                    add("uninst", f"{reg_get(root, k, 'DisplayName') or sub}: {cmd}", root, k, "tree", state=s)
    if "shareddll" in cats:
        for n, _v, _t in reg_values("HKLM", SHARED_DLLS):
            s = _path_state(n)
            if s in ("missing", "nodrive"):
                add("shareddll", n, "HKLM", SHARED_DLLS, "val", name=n, state=s)
    return out


def regclean_fix(it: dict) -> None:
    if it["op"] == "val":
        reg_del(it["root"], it["path"], it["name"])
    elif it["op"] == "defval":
        reg_del(it["root"], it["path"], "")
    else:
        reg_delete_tree(it["root"], it["path"])


# ───────────────────────── Worker ─────────────────────────
class Worker:
    def __init__(self):
        self.busy = False

    def run(self, title: str, fn, *args, then=None, journal=True):
        """then — вызвать в UI-потоке ПОСЛЕ освобождения (можно запускать следующее действие).
        journal — писать изменения в backup/undo_*.json (для «↩ Откат»)."""
        if self.busy:
            log.warning("⚠ Подождите — выполняется другое действие")
            return False
        self.busy = True
        ui(lambda: _APP and _APP._set_busy(title))

        def body():
            t0 = time.time()
            log.debug(f"▶ начало: {title}")
            _JOURNAL.ops = [] if journal else None
            try:
                fn(*args)
            except PermissionError:
                log.error(f"✗ {title}: нет прав — запустите от администратора", exc_info=True)
            except subprocess.TimeoutExpired:
                log.error(f"✗ {title}: превышено время ожидания", exc_info=True)
            except Exception as e:
                log.error(f"✗ {title}: {e}", exc_info=True)
            finally:
                save_journal(title, _JOURNAL.ops)
                _JOURNAL.ops = None
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


def _check_svg() -> str:
    """Файл-картинка галочки для QSS (QSS берёт картинки только из файлов)."""
    import tempfile
    f = Path(tempfile.gettempdir()) / "winfix_check.svg"
    try:
        if not f.exists():
            f.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" '
                         'fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" '
                         'stroke-linejoin="round"/></svg>', "utf-8")
        return f.as_posix()
    except OSError:
        return ""


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
    QWidget#page, QScrollArea#pagescroll {{ background: {p['bg']}; border: none; }}
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
    QPushButton:disabled, QPushButton#primary:disabled, QPushButton#danger:disabled {{
        background: {p['panel2']}; border-color: {p['line']}; color: {p['muted']}; }}
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
    QTableView::indicator {{ width: 15px; height: 15px; border: 1px solid {p['muted']}; border-radius: 4px;
                             background: {p['panel2']}; }}
    QTableView::indicator:checked {{ background: {p['accent']}; border-color: {p['accent']};
        image: url({_check_svg()}); }}
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
        b.setProperty("tip", tip)
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


class FlowLayout(QLayout):
    """Ряд виджетов с переносом на следующую строку, если не помещаются по ширине."""

    def __init__(self, parent=None, spacing=8):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return self._do_layout(QRect(0, 0, w, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for it in self._items:
            size = size.expandedTo(it.minimumSize())
        return size

    def _do_layout(self, rect, test):
        x, y, line_h, sp = rect.x(), rect.y(), 0, self.spacing()
        for it in self._items:
            if it.widget() and not it.widget().isVisibleTo(it.widget().parentWidget() or it.widget()):
                continue
            hint = it.sizeHint()
            if x + hint.width() > rect.right() + 1 and line_h > 0:
                x, y, line_h = rect.x(), y + line_h + sp, 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y + (line_h - hint.height()) // 2 if line_h > hint.height() else y),
                                     hint))
            x += hint.width() + sp
            line_h = max(line_h, hint.height())
        return y + line_h - rect.y()


def _row(*widgets, stretch=True):
    """Ряд кнопок: переносится на новую строку на узком окне (без горизонтальной прокрутки)."""
    h = FlowLayout()
    for w in widgets:
        h.addWidget(w)
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
             ("🚀", "Автозагрузка", "Автозагрузка (музыка при входе)"),
             ("🗑", "Программы", "Удаление программ и их остатков"), ("🩺", "Реестр", "Проверка реестра"),
             ("🧽", "Чистка", "Чистка реестра"),
             ("⚙", "Службы", "Службы Windows"), ("🧭", "Браузеры", "Браузеры и ярлыки"),
             ("📋", "Меню", "Контекстное меню Проводника"), ("🏴", "Активаторы", "Следы активаторов"),
             ("🌐", "Сеть", "Сеть и DNS"), ("🔌", "Порты", "Порты"), ("🛠", "Система", "Система и инструменты"),
             ("↩", "Откат", "Откат изменений"), ("🎨", "Цвета", "Цвета и программа")]
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
        self._cur_bad = None  # подменённые файлы курсоров (None — проверка ещё идёт)
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
        builders = [self._page_cursor, self._page_sound, self._page_startup, self._page_uninstall, self._page_registry, self._page_regclean,
                    self._page_services, self._page_browsers, self._page_ctx, self._page_kms, self._page_net,
                    self._page_ports, self._page_system, self._page_undo, self._page_theme]
        for i, ((emo, short, tip), build) in enumerate(zip(self.PAGES, builders)):
            b = QPushButton()
            b.setObjectName("nav")
            b.setToolTip(tip)
            b.setCheckable(True)
            b.setFixedHeight(36)
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
            sc = QScrollArea()  # маленький экран — страница прокручивается, а не сжимается
            sc.setObjectName("pagescroll")
            sc.setWidgetResizable(True)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sc.setFrameShape(QFrame.NoFrame)
            sc.setWidget(page)
            page.setMinimumHeight(420)
            self.stack.addWidget(sc)
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
        names = [x[1] for x in self.PAGES]  # вкладка по имени: номера меняются между версиями
        self._go(names.index(self.cfg["page_name"]) if self.cfg.get("page_name") in names else 0)
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
        self.cfg["page_name"] = self.PAGES[i][1]
        if self.PAGES[i][1] == "Откат":
            self.undo_refresh()

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
            b.setToolTip(f"Недоступно: выполняется «{title}»")
        self.sys_busy.setStyleSheet(f"color:{_WARN};")
        self.sys_busy.setText(f"⏳ Выполняется: {title}… Остальные действия станут доступны после окончания.")
        self.sys_busy.show()

    def _done(self):
        self.pill.setText("● готов")
        self.pill.setStyleSheet(f"color:{_OK};")
        for b in self.busy_btns:
            b.setEnabled(True)
            b.setToolTip(b.property("tip") or "")
        self.sys_busy.hide()
        self.b_stop.setEnabled(False)

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
        self._cur_check_bg()

    def _cur_check_bg(self):
        """Сверка файлов курсоров с WinSxS — в отдельном потоке, кнопки не блокирует."""
        def body():
            try:
                bad, owner = cursor_files_check()
            except Exception:
                log.debug("проверка файлов курсоров упала", exc_info=True)
                return
            self._cur_bad = bad_names(bad)
            if bad:
                log.warning(f"⚠ Подменены файлы курсоров ({len(bad)}): " + ", ".join(bad[:6])
                            + (" …" if len(bad) > 6 else "") + " — «🧩 Восстановить файлы»")
            if owner:
                log.info(f"   файлы курсоров оригинальные, но владелец не TrustedInstaller ({len(owner)}) — "
                         "«🧩 Восстановить файлы» вернёт права")
            ui(self.cursor_refresh)
        threading.Thread(target=body, daemon=True).start()

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
                          _btn("🧩 Восстановить файлы", "", "Вернуть оригинальные файлы из WinSxS в C:\\Windows\\Cursors (и владельца TrustedInstaller)",
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
                          "✓ файл из C:\\Windows\\Cursors — сверен с оригиналом в WinSxS. ⚠ — файл подменён "
                          "(или ещё сверяется). ✗ — чужой файл. Вернуть оригиналы — «🧩 Восстановить файлы».", "hint"))
        pl.addWidget(c, 1)

    def cursor_refresh(self):
        scheme, rows, custom = cursor_scan(self._cur_bad)
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
                                   ("⏳ сверяю файлы с WinSxS…" if self._cur_bad is None else f"⚠ подменено файлов {warn}")
                                   if warn else "✓ стандартный"))

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
        self.worker.run("размер курсора", job, journal=False)

    def _cur_size_sync(self):
        if not self._size_timer.isActive():  # пока пользователь щёлкает — не мешаем
            self.cur_size.set_value(cursor_size_get())

    def cursor_files(self):
        if not self._ask("Вернуть оригинальные файлы курсоров из хранилища Windows (WinSxS)\n"
                         "в C:\\Windows\\Cursors? Подменённые сборкой файлы будут перезаписаны."):
            return

        def job():
            cursor_restore_files()
            bad, _owner = cursor_files_check()
            self._cur_bad = bad_names(bad)
            log.info("✓ Все файлы курсоров оригинальные" if not bad else f"⚠ Остались подменённые: {', '.join(bad[:6])}")
            ui(self.cursor_refresh)
        self.worker.run("восстановление файлов курсоров", job)

    def cursor_reset(self):
        def job():
            bad, _owner = cursor_files_check()
            self._cur_bad = bad_names(bad)
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
        c, cl = _card("Быстро")
        b0 = _btn("🪄 Исправить всё", "primary", "Точка восстановления → курсор → звуки → реестр ✗ → службы ✗",
                  self.fix_all)
        b9 = _btn("📄 Отчёт", "", "Все проверки в один файл reports\\*.txt — удобно прислать", self.make_report)
        self.busy_btns += [b0, b9]
        cl.addLayout(_row(b0, b9, _btn("↩ Откат", "", "Журнал изменений", lambda: self._go([x[1] for x in self.PAGES].index("Откат")))))
        cl.addWidget(_lab("«Исправить всё» — безопасный набор: только явные поломки (✗), одна запись для отката.",
                          "hint"))
        pl.addWidget(c)

        c, cl = _card("Проверка системных файлов")
        b1 = _btn("⚡ DISM + SFC", "primary", "Сначала восстановить хранилище, затем проверить файлы (20–40 мин)",
                  lambda: self.sys_scan(True, True))
        b2 = _btn("DISM", "", "DISM /Online /Cleanup-Image /RestoreHealth", lambda: self.sys_scan(True, False))
        b3 = _btn("SFC", "", "sfc /scannow", lambda: self.sys_scan(False, True))
        self.b_stop = _btn("⏹ Остановить", "danger", "Прервать DISM / SFC", self.sys_stop)
        self.b_stop.setEnabled(False)
        self.busy_btns += [b1, b2, b3]
        cl.addLayout(_row(b1, b2, b3, self.b_stop))
        self.sys_busy = _lab("", "hint")
        self.sys_busy.setStyleSheet(f"color:{_WARN};")
        self.sys_busy.hide()
        cl.addWidget(self.sys_busy)
        cl.addWidget(_lab("Возвращает оригинальные системные файлы (в т.ч. подменённые курсоры, звуки, темы). "
                          "Нужен интернет и права администратора.", "hint"))
        pl.addWidget(c)

        c, cl = _card("Восстановление")
        b4 = _btn("💾 Точка восстановления", "", "Создать перед правками", self.sys_restore_point)
        self.busy_btns.append(b4)
        cl.addLayout(_row(b4, _btn("🔄 Перезапустить Проводник", "", "", self.sys_explorer),
                          _btn("🔁 Перезагрузка", "danger", "Перезагрузить компьютер через 10 с", self.sys_reboot)))
        pl.addWidget(c)

        c, cl = _card("Оформление Windows")
        cl.addLayout(_row(_btn("🎨 Стандартная тема", "", str(THEME_FILE), self._theme_default),
                          _btn("🏞 Стандартные обои", "", str(WALLPAPER), self._wallpaper),
                          _btn("🏷 Убрать OEM-сведения", "danger", "Логотип/телефон/сайт сборки в «О системе»",
                               self._oem_clear),
                          _btn("⚙ Персонализация", "chip", "ms-settings:personalization",
                               lambda: shell_open("ms-settings:personalization"))))
        self.oem_lbl = _lab("", "hint")
        cl.addWidget(self.oem_lbl)
        self._oem_show()
        cl.addWidget(_lab("Запреты смены обоев/темы/экрана блокировки — 🩺 Реестр.", "hint"))
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
            _STREAM["stopped"] = False
            if dism:
                log.info("⏳ DISM /RestoreHealth …")
                code = run_stream(["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"], log.info)
                (log.info if code == 0 else log.error)(f"{'✓' if code == 0 else '✗'} DISM завершён, код {code}")
            if sfc and _STREAM["stopped"]:
                return log.warning("⚠ Остановлено — SFC не запускался")
            if sfc:
                log.info("⏳ sfc /scannow …")
                code = run_stream(["sfc", "/scannow"], log.info)
                (log.info if code == 0 else log.warning)(f"{'✓' if code == 0 else '⚠'} SFC завершён, код {code}"
                                                         " (подробно: C:\\Windows\\Logs\\CBS\\CBS.log)")
        if self.worker.run("проверка системы", job):
            self.b_stop.setEnabled(True)

    def sys_stop(self):
        if self._ask("Прервать проверку системы?\n(Повреждения не возникнет, но проверку придётся запустить заново.)"):
            if not stop_stream():
                log.info("Нечего останавливать")

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

    # ── общий шаблон «таблица + сканирование» ──
    def _scan_into(self, title, scan_fn, attr, fill, *args):
        """Сканирование в фоне → self.<attr> → fill() в UI-потоке."""
        def job():
            items = scan_fn(*args)
            bad = sum(1 for i in items if i.get("st") == "bad")
            log.info(f"{'⚠' if bad else '✓'} {title}: найдено {len(items)}" + (f", проблем {bad}" if bad else ""))
            ui(lambda: (setattr(self, attr, items), fill()))
        self.worker.run(title, job, journal=False)

    def _apply_items(self, title, items, fn, done=None, ask=None):
        """fn(item) для выбранных; ошибки по одной строке; потом done() в UI."""
        if not items:
            return log.warning("⚠ Выберите строки")
        if ask and not self._ask(ask + "\n\n" + "\n".join(str(i.get("title") or i.get("name")) for i in items[:15])
                                 + ("\n…" if len(items) > 15 else "")):
            return

        def job():
            for it in items:
                try:
                    fn(it)
                    log.info(f"✓ {title}: {it.get('title') or it.get('name')}")
                except Exception as e:
                    log.error(f"✗ {it.get('title') or it.get('name')}: {e}", exc_info=True)
        self.worker.run(title, job, then=done)

    def _sel_data(self, t: QTableWidget):
        return [t.item(r, 0).data(Qt.UserRole) for r in self._sel_rows(t) if t.item(r, 0)]

    def _scan_btn(self, text, tip, slot):
        b = _btn(text, "primary", tip, slot)
        self.busy_btns.append(b)
        return b

    def _std_menu(self, t: QTableWidget, pos, acts):
        rows = self._sel_rows(t)
        acts = acts + [None, ("📋 Копировать строку", lambda: _copy(_table_text(t, rows))),
                       ("📋 Копировать всё", lambda: _copy(_table_text(t)))]
        _menu(self, acts).exec(t.viewport().mapToGlobal(pos))

    # ── ⚙ службы ──
    def _page_services(self, pl):
        c, cl = _card("Службы Windows, которые сборки отключают")
        self.sv_all = Toggle("Показать все (не только отключённые)")
        self.sv_all.clicked.connect(self._sv_fill)
        cl.addWidget(self.sv_all)
        self.sv_tbl = _table(["Статус", "Служба", "Имя", "Сейчас", "По умолчанию", "Важная"], 1)
        self.sv_tbl.customContextMenuRequested.connect(self._sv_menu)
        cl.addWidget(self.sv_tbl, 1)
        cl.addLayout(_row(self._scan_btn("🔎 Проверить", "Тип запуска служб из реестра", self.services_refresh),
                          _btn("🛠 Вернуть выбранные", "", "Тип запуска по умолчанию", self._sv_fix_sel),
                          _btn("🛠 Вернуть все ✗", "danger", "Только важные отключённые", self._sv_fix_bad),
                          _btn("⚙ services.msc", "", "", lambda: shell_open("services.msc"))))
        cl.addWidget(_lab("✗ — важная служба отключена (звук, поиск, сеть, защита, обновления). ⚠ — второстепенная "
                          "(печать, Bluetooth, телеметрия…): включай, если нужна. Применяется после перезагрузки.",
                          "hint"))
        pl.addWidget(c, 1)
        self.sv_rows: list = []

    def services_refresh(self):
        self._scan_into("Службы", services_scan, "sv_rows", self._sv_fill)

    def _sv_fill(self):
        vis = [r for r in self.sv_rows if self.sv_all.isChecked() or r["st"] != "ok"]
        t = self.sv_tbl
        t.setRowCount(len(vis))
        for i, r in enumerate(vis):
            t.setItem(i, 0, _cell({"ok": "✓ норма", "warn": "⚠ отключена", "bad": "✗ отключена"}[r["st"]],
                                  ST_COLOR[r["st"]]))
            t.setItem(i, 1, _cell(r["title"]))
            t.setItem(i, 2, _cell(r["name"]))
            t.setItem(i, 3, _cell(START_TXT.get(r["cur"], str(r["cur"]))))
            t.setItem(i, 4, _cell(START_TXT[r["dflt"]] + (" (отложенно)" if r["delayed"] and r["dflt"] == 2 else "")))
            t.setItem(i, 5, _cell("да" if r["important"] else ""))
            t.item(i, 0).setData(Qt.UserRole, r)
        self._status(f"Службы: отключено {sum(1 for r in self.sv_rows if r['st'] != 'ok')}")

    def _sv_fix_sel(self):
        self._apply_items("Служба", [r for r in self._sel_data(self.sv_tbl) if r["cur"] != r["dflt"]], service_fix,
                          self.services_refresh, "Вернуть тип запуска по умолчанию:")

    def _sv_fix_bad(self):
        self._apply_items("Служба", [r for r in self.sv_rows if r["st"] == "bad"], service_fix,
                          self.services_refresh, "Включить важные службы:")

    def _sv_menu(self, pos):
        sel = self._sel_data(self.sv_tbl)
        self._std_menu(self.sv_tbl, pos, [
            ("🛠 Вернуть по умолчанию", self._sv_fix_sel),
            ("▶ Запустить сейчас", lambda: self._apply_items(
                "Запуск", sel, lambda r: run_ps(f"Start-Service -Name {ps_quote(r['name'])}"))),
            ("🔎 Открыть в regedit", lambda: sel and open_regedit(rf"HKLM\{SVC_KEY}\{sel[0]['name']}")),
            ("🔎 Проверить заново", self.services_refresh)])

    # ── 🧭 браузеры ──
    def _page_browsers(self, pl):
        c, cl = _card("Подмены в браузерах: ярлыки с сайтом, политики (стартовая, поиск, расширения)")
        self.br_tbl = _table(["Статус", "Где", "Имя", "Значение"], 3)
        self.br_tbl.customContextMenuRequested.connect(self._br_menu)
        cl.addWidget(self.br_tbl, 1)
        cl.addLayout(_row(self._scan_btn("🔎 Сканировать", "Ярлыки браузеров и политики Chrome/Edge/Firefox/Яндекс…",
                                         self.browsers_refresh),
                          _btn("🛠 Исправить выбранное", "", "Ярлык — убрать сайт; политика — удалить", self._br_fix_sel),
                          _btn("🛠 Исправить все ✗", "danger", "", self._br_fix_bad)))
        cl.addWidget(_lab("✗ ярлык браузера с адресом сайта (открывает рекламу) или политика, навязывающая стартовую "
                          "страницу/поиск/расширения. ⚠ — прочие политики браузера. Закройте браузер перед исправлением; "
                          "политики HKLM — с правами администратора. Всё откатывается (↩ Откат).", "hint"))
        pl.addWidget(c, 1)
        self.br_items: list = []

    def browsers_refresh(self):
        self._scan_into("Браузеры", browsers_scan, "br_items", self._br_fill)

    def _br_fill(self):
        t = self.br_tbl
        t.setRowCount(len(self.br_items))
        for i, it in enumerate(self.br_items):
            t.setItem(i, 0, _cell({"ok": "✓", "warn": "⚠ политика", "bad": "✗ подмена"}[it["st"]], ST_COLOR[it["st"]]))
            t.setItem(i, 1, _cell(it["src"]))
            t.setItem(i, 2, _cell(it["name"], tip=it.get("file") or it.get("path", "")))
            t.setItem(i, 3, _cell(it["val"]))
            t.item(i, 0).setData(Qt.UserRole, it)
        self._status(f"Браузеры: найдено {len(self.br_items)}")

    def _br_done(self):
        self.browsers_refresh()

    def _br_fix_sel(self):
        self._apply_items("Браузер", self._sel_data(self.br_tbl), browser_fix, self._br_done, "Исправить:")

    def _br_fix_bad(self):
        self._apply_items("Браузер", [i for i in self.br_items if i["st"] == "bad"], browser_fix, self._br_done,
                          "Исправить все подмены (✗):")

    def _br_menu(self, pos):
        sel = self._sel_data(self.br_tbl)
        acts = [("🛠 Исправить", self._br_fix_sel)]
        if sel and sel[0]["kind"] == "lnk":
            acts.append(("📂 Показать ярлык", lambda: show_in_explorer(sel[0]["file"])))
        elif sel:
            acts.append(("🔎 Открыть в regedit", lambda: open_regedit(f"{sel[0]['root']}\\{sel[0]['path']}")))
        acts.append(("🔎 Сканировать заново", self.browsers_refresh))
        self._std_menu(self.br_tbl, pos, acts)

    # ── 📋 меню Проводника ──
    def _page_ctx(self, pl):
        c, cl = _card("Пункты контекстного меню (правый клик в Проводнике)")
        self.cx_builtin = Toggle("Показать встроенные Windows")
        self.cx_builtin.clicked.connect(self.ctx_refresh)
        cl.addWidget(self.cx_builtin)
        self.cx_tbl = _table(["Вкл", "Где", "Пункт", "Команда / DLL"], 3)
        self.cx_tbl.customContextMenuRequested.connect(self._cx_menu)
        cl.addWidget(self.cx_tbl, 1)
        cl.addLayout(_row(self._scan_btn("🔎 Сканировать", "HKCR: *, Directory, Folder, Drive, фон рабочего стола",
                                         self.ctx_refresh),
                          _btn("⏸ Скрыть", "", "Обратимо: LegacyDisable / Shell Extensions\\Blocked",
                               lambda: self._cx_set(False)),
                          _btn("▶ Показать", "", "", lambda: self._cx_set(True)),
                          _btn("🗑 Удалить", "danger", "Удалить ключ (сохраняется в ↩ Откат)", self._cx_del),
                          _btn("🔄 Перезапустить Проводник", "", "Чтобы меню обновилось", self.sys_explorer)))
        cl.addWidget(_lab("* — все файлы, Directory — папки, Background — пустое место в папке, Drive — диски. "
                          "Сначала «Скрыть», проверить меню, потом «Удалить». Изменения в HKLM — с правами "
                          "администратора.", "hint"))
        pl.addWidget(c, 1)
        self.cx_items: list = []

    def ctx_refresh(self):
        self._scan_into("Меню Проводника", ctx_scan, "cx_items", self._cx_fill, self.cx_builtin.isChecked())

    def _cx_fill(self):
        t = self.cx_tbl
        t.setRowCount(len(self.cx_items))
        for i, it in enumerate(self.cx_items):
            t.setItem(i, 0, _cell("✓" if it["on"] else "⏸", _OK if it["on"] else _ERR))
            t.setItem(i, 1, _cell(it["where"], tip=it["path"]))
            t.setItem(i, 2, _cell(it["title"] + (" (Windows)" if it["builtin"] else ""), tip=it["name"]))
            t.setItem(i, 3, _cell(it["cmd"]))
            t.item(i, 0).setData(Qt.UserRole, it)
        self._status(f"Меню Проводника: {len(self.cx_items)}")

    def _cx_set(self, on):
        self._apply_items("Показан" if on else "Скрыт", self._sel_data(self.cx_tbl),
                          lambda it: ctx_set_on(it, on), self._cx_fill)

    def _cx_del(self):
        self._apply_items("Удалён", self._sel_data(self.cx_tbl), lambda it: reg_delete_tree("HKCR", it["path"]),
                          self.ctx_refresh, "Удалить из меню Проводника:")

    def _cx_menu(self, pos):
        sel = self._sel_data(self.cx_tbl)
        self._std_menu(self.cx_tbl, pos, [
            ("⏸ Скрыть", lambda: self._cx_set(False)), ("▶ Показать", lambda: self._cx_set(True)),
            ("🗑 Удалить…", self._cx_del), None,
            ("📂 Показать файл", lambda: sel and show_in_explorer(sel[0]["cmd"])),
            ("🔎 Открыть в regedit", lambda: sel and open_regedit(f"HKCR\\{sel[0]['path']}")),
            ("🔎 Сканировать заново", self.ctx_refresh)])

    # ── 🏴 активаторы ──
    def _page_kms(self, pl):
        c, cl = _card("Следы активаторов (KMSAuto, AAct, KMSpico, KMS_VL_ALL…)")
        self.km_tbl = _table(["Статус", "Тип", "Имя", "Значение"], 3)
        self.km_tbl.customContextMenuRequested.connect(self._km_menu)
        cl.addWidget(self.km_tbl, 1)
        cl.addLayout(_row(self._scan_btn("🔎 Сканировать", "Задачи, службы, файлы, IFEO, KMS-сервер, исключения Defender",
                                         self.kms_refresh),
                          _btn("🗑 Удалить выбранное", "danger", "Задача/файл/исключение — откатываются", self._km_del),
                          _btn("🔑 Статус активации", "", "slmgr /dli",
                               lambda: shell_open(os.path.join(WINDIR, "System32", "cscript.exe"),
                                                  "//nologo " + os.path.join(WINDIR, "System32", "slmgr.vbs") + " /dli"))))
        cl.addWidget(_lab("⚠ Удаление следов активатора может сбросить активацию Windows/Office. Исключения Defender "
                          "сборки добавляют, чтобы антивирус не видел активатор: ✗ — исключён весь диск/Windows или "
                          "папка активатора. Удалённая служба при откате не вернётся (только тип запуска).", "hint"))
        pl.addWidget(c, 1)
        self.km_items: list = []

    def kms_refresh(self):
        self._scan_into("Активаторы", kms_scan, "km_items", self._km_fill)

    def _km_fill(self):
        t = self.km_tbl
        t.setRowCount(len(self.km_items))
        for i, it in enumerate(self.km_items):
            t.setItem(i, 0, _cell({"ok": "✓", "warn": "⚠ проверить", "bad": "✗ след"}[it["st"]], ST_COLOR[it["st"]]))
            t.setItem(i, 1, _cell(it["src"]))
            t.setItem(i, 2, _cell(it["name"]))
            t.setItem(i, 3, _cell(it["val"]))
            t.item(i, 0).setData(Qt.UserRole, it)
        self._status(f"Активаторы: найдено {len(self.km_items)}")

    def _km_del(self):
        self._apply_items("Удалено", self._sel_data(self.km_tbl), kms_delete, self.kms_refresh,
                          "Удалить следы активатора?\n(Активация Windows/Office может слететь.)")

    def _km_menu(self, pos):
        sel = self._sel_data(self.km_tbl)
        acts = [("🗑 Удалить…", self._km_del)]
        if sel and sel[0]["kind"] == "file":
            acts.append(("📂 Показать", lambda: show_in_explorer(sel[0]["path"])))
        if sel and sel[0]["kind"] == "reg":
            acts.append(("🔎 Открыть в regedit", lambda: open_regedit(f"HKLM\\{sel[0]['path']}")))
        if sel and sel[0]["kind"] == "task":
            acts.append(("🗓 Планировщик", lambda: shell_open("taskschd.msc")))
        acts.append(("🔎 Сканировать заново", self.kms_refresh))
        self._std_menu(self.km_tbl, pos, acts)

    # ── 🌐 сеть ──
    def _page_net(self, pl):
        c, cl = _card("DNS-серверы адаптеров")
        self.dn_tbl = _table(["Статус", "Адаптер", "DNS", "Чьи"], 3)
        self.dn_tbl.customContextMenuRequested.connect(self._dn_menu)
        cl.addWidget(self.dn_tbl, 1)
        cl.addLayout(_row(self._scan_btn("🔎 Проверить DNS", "Get-DnsClientServerAddress", self.dns_refresh),
                          _btn("↺ DNS автоматически", "", "Сбросить на выдаваемые роутером (DHCP) — для выбранных",
                               self._dn_reset)))
        cl.addWidget(_lab("⚠ неизвестный DNS — сборка или вирус могли подменить сервер (реклама, фишинг). "
                          "Роутер/локальный и известные публичные (Google, Cloudflare, Яндекс…) — норма.", "hint"))
        pl.addWidget(c, 1)
        c, cl = _card("Сброс сети")
        btns = []
        for key, text, tip in (("flushdns", "🧹 Очистить кэш DNS", "ipconfig /flushdns"),
                               ("winsock", "🔧 Сброс Winsock", "netsh winsock reset — после перезагрузки"),
                               ("tcpip", "🔧 Сброс TCP/IP", "netsh int ip reset — после перезагрузки"),
                               ("winhttp", "🔧 Сброс прокси WinHTTP", "netsh winhttp reset proxy")):
            b = _btn(text, "", tip, lambda _=False, k=key: self._net(k))
            self.busy_btns.append(b)
            btns.append(b)
        cl.addLayout(_row(*btns, _btn("🌐 Параметры сети", "chip", "ms-settings:network",
                                      lambda: shell_open("ms-settings:network"))))
        cl.addWidget(_lab("Помогает, если после сборки «нет интернета», не открываются сайты или стоит чужой прокси. "
                          "Нужны права администратора. Прокси браузера — 🩺 Реестр → «Прокси».", "hint"))
        pl.addWidget(c)
        self.dn_rows: list = []

    def dns_refresh(self):
        self._scan_into("DNS", dns_scan, "dn_rows", self._dn_fill)

    def _dn_fill(self):
        t = self.dn_tbl
        t.setRowCount(len(self.dn_rows))
        for i, r in enumerate(self.dn_rows):
            t.setItem(i, 0, _cell("✓ норма" if r["st"] == "ok" else "⚠ проверить", ST_COLOR[r["st"]]))
            t.setItem(i, 1, _cell(r["alias"]))
            t.setItem(i, 2, _cell(", ".join(r["servers"])))
            t.setItem(i, 3, _cell(r["note"]))
            t.item(i, 0).setData(Qt.UserRole, r)

    def _dn_reset(self):
        self._apply_items("DNS автоматически", self._sel_data(self.dn_tbl), dns_reset, self.dns_refresh,
                          "Сбросить DNS на автоматический (от роутера):")

    def _net(self, key):
        if key in ("winsock", "tcpip") and not self._ask(f"{NET_CMDS[key][1]}.\nВыполнить?"):
            return
        self.worker.run("сеть", net_cmd, key, journal=False)

    def _dn_menu(self, pos):
        self._std_menu(self.dn_tbl, pos, [("↺ DNS автоматически", self._dn_reset),
                                          ("🔎 Проверить заново", self.dns_refresh)])

    # ── ↩ откат ──
    def _page_undo(self, pl):
        c, cl = _card("Журнал изменений (backup)")
        self.un_tbl = _table(["Статус", "Когда", "Действие", "Изменений"], 2)
        self.un_tbl.customContextMenuRequested.connect(self._un_menu)
        cl.addWidget(self.un_tbl, 1)
        b = _btn("↩ Откатить выбранное", "primary", "Вернуть всё, что изменило это действие", self._un_undo)
        self.busy_btns.append(b)
        cl.addLayout(_row(b, _btn("🔄 Обновить", "", "", self.undo_refresh),
                          _btn("📁 Папка backup", "", str(BACKUP_DIR), self._un_folder),
                          _btn("🗑 Удалить запись", "danger", "Удалить файл журнала", self._un_delete)))
        cl.addWidget(_lab("Каждое действие WinFix (реестр, файлы, ярлыки, задачи, DNS, исключения) сохраняет "
                          "старые значения в backup\\undo_*.json. Откатывайте сверху вниз — от новых к старым.", "hint"))
        pl.addWidget(c, 1)

    def undo_refresh(self):
        rows = journal_list()
        t = self.un_tbl
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i, 0, _cell("↩ откачено" if r["done"] else "● активно", _WARN if r["done"] else _OK))
            t.setItem(i, 1, _cell(r["time"]))
            t.setItem(i, 2, _cell(r["title"], tip=r["file"]))
            t.setItem(i, 3, _cell(r["n"]))
            t.item(i, 0).setData(Qt.UserRole, r)
        self._status(f"Откат: записей {len(rows)}")

    def _un_undo(self):
        sel = [r for r in self._sel_data(self.un_tbl) if not r["done"]]
        if not sel:
            return log.warning("⚠ Выберите активную запись")
        if not self._ask("Откатить:\n\n" + "\n".join(f"{r['time']}  {r['title']}" for r in sel)):
            return

        def job():
            for r in sel:
                journal_undo(r["file"])
        self.worker.run("откат", job, then=self.undo_refresh, journal=False)

    def _un_folder(self):
        BACKUP_DIR.mkdir(exist_ok=True)
        shell_open(str(BACKUP_DIR))

    def _un_delete(self):
        sel = self._sel_data(self.un_tbl)
        if sel and self._ask(f"Удалить записи журнала ({len(sel)})? Откатить их будет нельзя."):
            for r in sel:
                Path(r["file"]).unlink(missing_ok=True)
            self.undo_refresh()

    def _un_menu(self, pos):
        sel = self._sel_data(self.un_tbl)
        self._std_menu(self.un_tbl, pos, [("↩ Откатить", self._un_undo),
                                          ("📄 Открыть файл", lambda: sel and shell_open(sel[0]["file"])),
                                          ("🗑 Удалить запись…", self._un_delete), ("🔄 Обновить", self.undo_refresh)])

    # ── 🪄 мастер, отчёт, оформление, обновления ──
    def fix_all(self):
        if not self._ask("Исправить всё одной кнопкой?\n\n1. Точка восстановления\n2. Стандартный курсор\n"
                         "3. Стандартные звуки\n4. Реестр — только ✗\n5. Важные отключённые службы\n\n"
                         "Всё попадёт в одну запись ↩ Отката."):
            return
        self.worker.run("исправить всё", fix_all, self.checks, then=self._after_fix_all)

    def _after_fix_all(self):
        self._refresh_light()
        self.undo_refresh()

    def make_report(self):
        def job():
            f = build_report(self.checks)
            log.info(f"✓ Отчёт: {f}")
            ui(lambda: shell_open(str(f)))
        self.worker.run("отчёт", job, journal=False)

    def _theme_default(self):
        if self._ask("Применить стандартную тему Windows (aero.theme)?\nОткроются Параметры → Персонализация."):
            shell_open(str(THEME_FILE))

    def _wallpaper(self):
        self.worker.run("обои", lambda: (wallpaper_default(), log.info(f"✓ Обои: {WALLPAPER}")))

    def _oem_clear(self):
        info = oem_info()
        if not info:
            return log.info("✓ OEM-сведений нет")
        if self._ask("Убрать из «Сведений о системе»:\n\n" + "\n".join(f"{k}: {v}" for k, v in info.items())):
            self.worker.run("OEM-сведения", lambda: (oem_clear(), log.info("✓ OEM-сведения удалены"),
                                                     ui(self._oem_show)))

    def _oem_show(self):
        info = oem_info()
        self.oem_lbl.setText(("OEM: " + " · ".join(f"{k}={v}" for k, v in info.items())) if info
                             else "OEM-сведений нет ✓")

    def check_update(self):
        def job():
            res = update_check()
            if res is None:
                return log.info(f"Релизов на GitHub нет (или репозиторий закрыт): {UPDATE_REPO}")
            tag, url = res
            if _ver(tag) > _ver(VERSION):
                log.warning(f"⚠ Доступна новая версия {tag} (у вас {VERSION})")
                ui(lambda: self._ask(f"Доступна версия {tag}. Открыть страницу загрузки?") and webbrowser.open(url))
            else:
                log.info(f"✓ У вас последняя версия ({VERSION})")
        self.worker.run("проверка обновлений", job, journal=False)

    # ── 🗑 удаление программ ──
    def _page_uninstall(self, pl):
        c, cl = _card("Установленные программы")
        self.ap_filter = QLineEdit()
        self.ap_filter.setPlaceholderText("🔎 Фильтр: название, издатель…")
        self.ap_filter.textChanged.connect(self._ap_fill)
        cl.addWidget(self.ap_filter)
        self.ap_tbl = _table(["Программа", "Версия", "Издатель", "МБ", "Дата", "Для"], 0)
        self.ap_tbl.customContextMenuRequested.connect(self._ap_menu)
        self.ap_tbl.itemDoubleClicked.connect(lambda *_: self._ap_uninstall())
        cl.addWidget(self.ap_tbl, 1)
        b1 = self._scan_btn("🔄 Список", "Программы из реестра (как в «Программах и компонентах»)", self.apps_refresh)
        b2 = _btn("🗑 Удалить программу", "danger", "Деинсталлятор программы → поиск остатков", self._ap_uninstall)
        b3 = _btn("🔎 Найти остатки", "", "Без деинсталлятора — если программа уже удалена или сломана",
                  self._ap_leftovers)
        self.busy_btns += [b2, b3]
        cl.addLayout(_row(b1, b2, b3, _btn("📦 Программы и компоненты", "chip", "appwiz.cpl",
                                           lambda: shell_open("appwiz.cpl"))))
        pl.addWidget(c, 3)

        c, cl = _card("Остатки")
        self.lo_title = _lab("Выберите программу и нажмите «🗑 Удалить программу» или «🔎 Найти остатки».", "hint")
        cl.addWidget(self.lo_title)
        self.lo_tbl = _table(["Статус", "Тип", "Где", "Размер", "Почему"], 2)
        self.lo_tbl.customContextMenuRequested.connect(self._lo_menu)
        cl.addWidget(self.lo_tbl, 1)
        b4 = _btn("🧹 Удалить выбранные остатки", "primary", "Файлы → backup\\uninstall, реестр — с копией (↩ Откат)",
                  self._lo_delete)
        self.busy_btns.append(b4)
        cl.addLayout(_row(b4, _btn("✓ Выделить надёжные", "", "Только ✗ — точно этой программы", self._lo_select_sure),
                          _btn("🗑 Очистить backup\\uninstall", "danger", "Удалить навсегда перенесённые файлы",
                               self._lo_purge)))
        cl.addWidget(_lab("✗ — точно этой программы (папка установки, совпадает имя). ⚠ — похоже, проверьте перед "
                          "удалением. Файлы не стираются, а переносятся в backup\\uninstall — откат вернёт их; "
                          "место освобождает «Очистить backup\\uninstall».", "hint"))
        pl.addWidget(c, 2)
        self.ap_items: list = []
        self.lo_items: list = []
        self.lo_app: dict | None = None

    def apps_refresh(self):
        self._scan_into("Программы", uninstall_list, "ap_items", self._ap_fill)

    def _ap_fill(self):
        q = self.ap_filter.text().lower().strip()
        vis = [a for a in self.ap_items if not q or q in (a["name"] + " " + a["pub"]).lower()]
        t = self.ap_tbl
        t.setSortingEnabled(False)
        t.setRowCount(len(vis))
        for i, a in enumerate(vis):
            t.setItem(i, 0, _cell(a["name"], tip=a["cmd"] or "нет деинсталлятора"))
            t.setItem(i, 1, _cell(a["ver"]))
            t.setItem(i, 2, _cell(a["pub"]))
            sz = _cell("")
            if a["size"]:
                sz.setData(Qt.DisplayRole, a["size"])  # число — сортировка по размеру
            t.setItem(i, 3, sz)
            t.setItem(i, 4, _cell(a["date"]))
            t.setItem(i, 5, _cell(a["src"], tip=f"{a['root']}\\{a['key']}"))
            t.item(i, 0).setData(Qt.UserRole, a)
        t.setSortingEnabled(True)
        self._status(f"Программ: {len(vis)} из {len(self.ap_items)}")

    def _ap_sel(self):
        sel = self._sel_data(self.ap_tbl)
        if not sel:
            log.warning("⚠ Выберите программу")
        return sel[0] if sel else None

    def _ap_uninstall(self, quiet=False):
        a = self._ap_sel()
        if not a or not self._ask(f"Удалить «{a['name']}» {a['ver']}?\n\n1. Запустится её деинсталлятор — пройдите "
                                  "его до конца.\n2. Затем WinFix найдёт остатки (папки, реестр, ярлыки, службы, "
                                  "задачи) — вы выберете, что удалить."):
            return

        def job():
            uninstall_run(a, quiet)
            self._lo_scan_job(a)
        self.worker.run(f"удаление {a['name']}", job, then=self.apps_refresh, journal=False)

    def _ap_leftovers(self):
        a = self._ap_sel()
        if a:
            self.worker.run(f"остатки {a['name']}", self._lo_scan_job, a, journal=False)

    def _lo_scan_job(self, a):
        log.info(f"⏳ Ищу остатки «{a['name']}»…")
        items = leftovers_scan(a)
        sure = sum(1 for i in items if i["st"] == "bad")
        log.info(f"{'⚠' if items else '✓'} Остатки «{a['name']}»: {len(items)}" + (f" (✗ точно: {sure})" if sure else ""))
        ui(lambda: self._lo_show(a, items))

    def _lo_show(self, a, items):
        self.lo_app, self.lo_items = a, items
        self.lo_title.setText(f"Остатки: {a['name']} {a['ver']} — найдено {len(items)}")
        self._lo_fill()
        self._lo_select_sure()

    def _lo_fill(self):
        t = self.lo_tbl
        t.setRowCount(len(self.lo_items))
        kinds = {"dir": "📁 папка", "file": "📄 файл", "reg": "🧬 реестр", "regval": "🚀 автозагрузка",
                 "svc": "⚙ служба", "task": "🗓 задача"}
        for i, it in enumerate(self.lo_items):
            t.setItem(i, 0, _cell("✗ точно" if it["st"] == "bad" else "⚠ похоже", ST_COLOR[it["st"]]))
            t.setItem(i, 1, _cell(kinds.get(it["kind"], it["kind"])))
            t.setItem(i, 2, _cell(it["path"]))
            t.setItem(i, 3, _cell(it.get("size", "")))
            t.setItem(i, 4, _cell(it["why"]))
            t.item(i, 0).setData(Qt.UserRole, it)

    def _lo_select_sure(self):
        t = self.lo_tbl
        t.clearSelection()
        for i, it in enumerate(self.lo_items):
            if it["st"] == "bad":
                t.selectionModel().select(t.model().index(i, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def _lo_delete(self):
        sel = self._sel_data(self.lo_tbl)
        name = self.lo_app["name"] if self.lo_app else "app"
        if not sel:
            return log.warning("⚠ Выберите остатки")
        warn = sum(1 for i in sel if i["st"] != "bad")
        self._apply_items(f"Остаток {name}", [dict(i, title=i["path"]) for i in sel],
                          lambda it: leftover_delete(it, name), self._lo_after,
                          f"Удалить остатки «{name}» ({len(sel)})?" + (f"\n⚠ Среди них «похожих»: {warn}" if warn else ""))

    def _lo_after(self):
        if self.lo_app:
            self.worker.run(f"остатки {self.lo_app['name']}", self._lo_scan_job, self.lo_app, journal=False)

    def _lo_purge(self):
        d = BACKUP_DIR / "uninstall"
        if not d.is_dir():
            return log.info("✓ backup\\uninstall пуст")
        if self._ask(f"Удалить НАВСЕГДА перенесённые файлы ({_human(backup_size())})?\nОткатить их будет нельзя."):
            self.worker.run("очистка backup", lambda: (shutil.rmtree(d, ignore_errors=True),
                                                       log.info("✓ backup\\uninstall очищен")), journal=False)

    def _ap_menu(self, pos):
        sel = self._sel_data(self.ap_tbl)
        a = sel[0] if sel else None
        acts = [("🗑 Удалить программу…", self._ap_uninstall)]
        if a and a["quiet"]:
            acts.append(("🤫 Удалить тихо (без окон)…", lambda: self._ap_uninstall(True)))
        self._std_menu(self.ap_tbl, pos, acts + [
            ("🔎 Найти остатки", self._ap_leftovers), None,
            ("📂 Папка программы", lambda: a and (_install_dir(a) and shell_open(_install_dir(a))
                                                 or log.warning("⚠ Папка программы не найдена"))),
            ("🔎 Открыть в regedit", lambda: a and open_regedit(f"{a['root']}\\{a['key']}")),
            ("🌐 Найти в интернете", lambda: a and webbrowser.open(
                "https://www.google.com/search?q=" + re.sub(r"\s+", "+", a["name"]))),
            ("🔄 Обновить список", self.apps_refresh)])

    def _lo_menu(self, pos):
        sel = self._sel_data(self.lo_tbl)
        it = sel[0] if sel else None
        acts = [("🧹 Удалить выбранные…", self._lo_delete), ("✓ Выделить надёжные", self._lo_select_sure), None]
        if it and it["kind"] in ("dir", "file"):
            acts.append(("📂 Открыть", lambda: shell_open(it["path"] if it["kind"] == "dir" else os.path.dirname(it["path"]))))
        if it and it["kind"] in ("reg", "regval"):
            acts.append(("🔎 Открыть в regedit", lambda: open_regedit(f"{it['root']}\\{it['rpath']}")))
        self._std_menu(self.lo_tbl, pos, acts)

    # ── 🧽 чистка реестра ──
    def _page_regclean(self, pl):
        c, cl = _card("Что искать")
        self.rc_cats = {}
        tg = []
        for key, title in RC_CATS:
            t = Toggle(title)
            t.setChecked(key not in self.cfg.get("rc_off", []))
            self.rc_cats[key] = t
            tg.append(t)
        cl.addLayout(_row(*tg))
        self.rc_nodrive = Toggle("⚠ Неподключённые диски (флешка, сеть) — тоже мусор")
        self.rc_nodrive.setToolTip("Как CCleaner: отмечать записи о файлах на дисках, которых сейчас нет")
        self.rc_nodrive.setChecked(bool(self.cfg.get("rc_nodrive")))
        self.rc_nodrive.clicked.connect(self._rc_nodrive)
        cl.addWidget(self.rc_nodrive)
        pl.addWidget(c)
        c, cl = _card("Проблемы реестра")
        self.rc_info = _lab("Нажмите «🔎 Сканировать».", "hint")
        cl.addWidget(self.rc_info)
        self.rc_tbl = _table(["", "Проблема", "Данные", "Ключ реестра"], 2)
        self.rc_tbl.customContextMenuRequested.connect(self._rc_menu)
        self.rc_tbl.itemChanged.connect(lambda *_: self._rc_count())
        cl.addWidget(self.rc_tbl, 1)
        b1 = self._scan_btn("🔎 Сканировать", "Поиск проблем по отмеченным категориям", self.regclean_refresh)
        b2 = _btn("🧹 Исправить отмеченные", "danger", "Каждое удаление сохраняется в ↩ Откат", self._rc_fix)
        self.busy_btns.append(b2)
        cl.addLayout(_row(b1, b2, _btn("☑ Отметить всё", "", "", lambda: self._rc_check_all(True)),
                          _btn("☐ Снять всё", "", "", lambda: self._rc_check_all(False))))
        cl.addWidget(_lab("Отмечены только надёжные находки. ⚠ — файл на диске, который сейчас не подключён "
                          "(флешка, сетевой диск): не отмечается — подключите диск или включите переключатель выше. "
                          "Копия .reg не нужна: всё удалённое возвращает ↩ Откат.", "hint"))
        pl.addWidget(c, 1)
        self.rc_items: list = []

    def regclean_refresh(self):
        cats = [k for k, t in self.rc_cats.items() if t.isChecked()]
        self.cfg["rc_off"] = [k for k, t in self.rc_cats.items() if not t.isChecked()]
        if not cats:
            return log.warning("⚠ Отметьте хотя бы одну категорию")
        self._scan_into("Чистка реестра", regclean_scan, "rc_items", self._rc_fill, cats)

    def _rc_fill(self):
        t = self.rc_tbl
        t.blockSignals(True)
        t.setRowCount(len(self.rc_items))
        for i, it in enumerate(self.rc_items):
            chk = _cell("", tip=it["note"] or "")
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Checked if it["st"] == "bad" or self.rc_nodrive.isChecked() else Qt.Unchecked)
            chk.setData(Qt.UserRole, it)
            t.setItem(i, 0, chk)
            t.setItem(i, 1, _cell(("⚠ " if it["st"] == "warn" else "") + it["title"],
                                  _WARN if it["st"] == "warn" else None, tip=it["note"] or it["title"]))
            t.setItem(i, 2, _cell(it["data"]))
            t.setItem(i, 3, _cell(it["key"]))
        t.blockSignals(False)
        self._rc_count()

    def _rc_nodrive(self):
        self.cfg["rc_nodrive"] = self.rc_nodrive.isChecked()
        t = self.rc_tbl
        t.blockSignals(True)
        for r in range(t.rowCount()):
            if t.item(r, 0).data(Qt.UserRole)["st"] == "warn":
                t.item(r, 0).setCheckState(Qt.Checked if self.rc_nodrive.isChecked() else Qt.Unchecked)
        t.blockSignals(False)
        self._rc_count()

    def _rc_checked(self):
        t = self.rc_tbl
        return [t.item(r, 0).data(Qt.UserRole) for r in range(t.rowCount())
                if t.item(r, 0) and t.item(r, 0).checkState() == Qt.Checked]

    def _rc_count(self):
        n = len(self.rc_items)
        by = {}
        for it in self.rc_items:
            by[it["title"]] = by.get(it["title"], 0) + 1
        self.rc_info.setText(f"Найдено проблем: {n}, отмечено: {len(self._rc_checked())}" +
                             ("   ·   " + ", ".join(f"{k}: {v}" for k, v in by.items()) if by else ""))

    def _rc_check_all(self, on):
        t = self.rc_tbl
        t.blockSignals(True)
        for r in range(t.rowCount()):
            t.item(r, 0).setCheckState(Qt.Checked if on else Qt.Unchecked)
        t.blockSignals(False)
        self._rc_count()

    def _rc_set_sel(self, on):
        t = self.rc_tbl
        t.blockSignals(True)
        for r in self._sel_rows(t):
            t.item(r, 0).setCheckState(Qt.Checked if on else Qt.Unchecked)
        t.blockSignals(False)
        self._rc_count()

    def _rc_fix(self):
        items = self._rc_checked()
        if not items:
            return log.warning("⚠ Нечего исправлять — отметьте строки")
        if not self._ask(f"Исправить отмеченные проблемы реестра: {len(items)}?\n\nВсё удалённое можно вернуть "
                         "на странице ↩ Откат."):
            return

        def job():
            ok = 0
            for it in items:
                try:
                    regclean_fix(it)
                    ok += 1
                    log.debug(f"исправлено: {it['title']} · {it['key']}")
                except Exception as e:
                    log.error(f"✗ {it['title']}: {it['data']} — {e}")
            log.info(f"✓ Чистка реестра: исправлено {ok} из {len(items)}")
        self.worker.run("чистка реестра", job, then=self.regclean_refresh)

    def _rc_menu(self, pos):
        rows = self._sel_rows(self.rc_tbl)
        it = self.rc_tbl.item(rows[0], 0).data(Qt.UserRole) if rows else None
        acts = [("☑ Отметить выбранные", lambda: self._rc_set_sel(True)),
                ("☐ Снять с выбранных", lambda: self._rc_set_sel(False)), None,
                ("🔎 Открыть в regedit", lambda: it and open_regedit(f"{it['root']}\\{it['path']}"))]
        if it and it["cat"] in ("apppaths", "mui", "run", "installer", "firewall", "uninst", "shareddll"):
            acts.append(("📂 Показать файл", lambda: show_in_explorer(it["data"].split(" — ")[-1].split(": ", 1)[-1])))
        acts.append(("🔎 Сканировать заново", self.regclean_refresh))
        self._std_menu(self.rc_tbl, pos, acts)

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
        c, cl = _card("Обновления")
        b = _btn("🔄 Проверить версию", "", f"GitHub: {UPDATE_REPO}", self.check_update)
        self.busy_btns.append(b)
        cl.addLayout(_row(b, _btn("🌐 Релизы", "chip", "", lambda: webbrowser.open(
            f"https://github.com/{UPDATE_REPO}/releases"))))
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
            for fill in (self._sv_fill, self._br_fill, self._cx_fill, self._km_fill, self._dn_fill, self._ap_fill,
                         self._lo_fill):
                fill()
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
