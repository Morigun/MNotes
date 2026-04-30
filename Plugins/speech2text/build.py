import py_compile
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

STDLIB_IMPORTS = ["wave", "audioop", "zipfile", "urllib.request"]

SRC = Path(__file__).resolve().parent
DIST = SRC / "dist"
PLUGIN_DIST = DIST / "plugins" / "speech2text"
PLUGIN_LIB = PLUGIN_DIST / "lib"
SITE_PKGS = Path(sysconfig.get_paths()["purelib"])
VOSK_SRC = SITE_PKGS / "vosk"

if DIST.exists():
    shutil.rmtree(DIST)
PLUGIN_DIST.mkdir(parents=True)
PLUGIN_LIB.mkdir(parents=True)

print("Compiling plugin files...")
for py_file in SRC.glob("*.py"):
    if py_file.name in ("build.py", "vosk_shim.py"):
        continue
    print(f"  {py_file.name}")
    pyc = py_compile.compile(str(py_file), doraise=True)
    shutil.copy2(pyc, PLUGIN_DIST / (py_file.stem + ".pyc"))

shutil.copy2(SRC / "plugin.json", PLUGIN_DIST / "plugin.json")

print("Copying vosk shim...")
shutil.copy2(SRC / "vosk_shim.py", PLUGIN_DIST / "vosk_shim.pyc" if False else PLUGIN_DIST / "vosk_shim.py")
pyc = py_compile.compile(str(SRC / "vosk_shim.py"), doraise=True)
shutil.copy2(pyc, PLUGIN_DIST / "vosk_shim.pyc")
(PLUGIN_DIST / "vosk_shim.py").unlink(missing_ok=True)

with open(DIST / "hidden_imports.txt", "w") as f:
    for mod in STDLIB_IMPORTS:
        f.write(mod + "\n")

print("Installing vosk (for DLLs)...")
subprocess.run([sys.executable, "-m", "pip", "install", "vosk", "-q"], check=True)

print("Copying vosk native library...")
shutil.copy2(VOSK_SRC / "vosk_cffi.py", PLUGIN_LIB / "vosk_cffi.py")
for dll in VOSK_SRC.glob("*.dll"):
    print(f"  {dll.name}")
    shutil.copy2(dll, PLUGIN_LIB / dll.name)

print(f"Plugin built: {DIST}")
