# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files


raiz = Path(SPECPATH)
analise = Analysis(
    [str(raiz / "packaging" / "studenthub_entry.py")],
    pathex=[str(raiz)],
    datas=collect_data_files("customtkinter"),
    # O código nativo do Pillow importa _tkinter_finder em tempo de execução.
    hiddenimports=["PIL._imagingtk", "PIL._tkinter_finder"],
    hooksconfig={"matplotlib": {"backends": ["TkAgg"]}},
)
# A aplicação usa fontes e estilos do Matplotlib, sem os conjuntos de exemplo.
analise.datas = [
    item for item in analise.datas
    if not Path(item[0]).as_posix().startswith("matplotlib/mpl-data/sample_data/")
]
pyz = PYZ(analise.pure)
exe = EXE(
    pyz,
    analise.scripts,
    exclude_binaries=True,
    name="StudentHub",
    console=False,
    upx=False,
    version=str(raiz / "packaging" / "windows-version.txt") if sys.platform == "win32" else None,
)
pacote = COLLECT(
    exe,
    analise.binaries,
    analise.datas,
    name="StudentHub",
    upx=False,
)
