# win_fix.spec  v1.7.0
# Журнал:
# v1.7.0: без изменений сборки.
# v1.6.3: без изменений сборки.
# v1.6.2: без изменений сборки.
# v1.6.1: без изменений сборки.
# v1.6.0: без изменений сборки.
# v1.5.0: без изменений сборки.
# v1.4.0: без изменений сборки.
# v1.3.5: без изменений сборки.
# v1.3.4: без изменений сборки.
# v1.3.3: uac_admin=False — права просит сама программа (иначе --selftest в build_exe.bat падает: ошибка 740).
# v1.3.2: без изменений сборки.
# v1.3.1: без изменений сборки.
# v1.3.0: без изменений сборки.
# v1.2.1: без изменений сборки.
# v1.2.0: без изменений сборки.
# v1.1.0: без изменений сборки.
# v1.0.0: первая версия (onefile, без консоли, uac_admin).
a = Analysis(['win_fix.py'], pathex=[], binaries=[], datas=[], hiddenimports=[],
             excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.Qt3DCore',
                       'PySide6.QtMultimedia', 'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtCharts',
                       'tkinter'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='win_fix', debug=False, strip=False,
          upx=False, console=False, uac_admin=False)
