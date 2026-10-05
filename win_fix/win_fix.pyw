"""
win_fix.pyw  v1.3.3
Запуск двойным кликом (pythonw, без консоли).

Журнал:
v1.3.3: версия в ногу с win_fix.py.
v1.3.2: версия в ногу с win_fix.py.
v1.3.1: версия в ногу с win_fix.py.
v1.3.0: версия в ногу с win_fix.py.
v1.2.1: версия в ногу с win_fix.py.
v1.2.0: версия в ногу с win_fix.py.
v1.1.0: версия в ногу с win_fix.py.
v1.0.0: первая версия.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from win_fix import main  # noqa: E402

main()
