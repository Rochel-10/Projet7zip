"""
build.py — Script de construction de l'exécutable Projet7Zip
Usage : python build.py
"""

import os
import sys
import subprocess
import shutil

def build():
    base = os.path.dirname(os.path.abspath(__file__))
    print("=" * 55)
    print("  Construction de Projet7Zip")
    print("=" * 55)

    # Vérifier PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} détecté.")
    except ImportError:
        print("  Installation de PyInstaller…")
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "pyinstaller", "--break-system-packages"])

    print("\n  Lancement de la construction…\n")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "Projet7Zip",
        "--add-data", f"algorithms.py{os.pathsep}.",
        os.path.join(base, "projet7zip.py"),
    ]
    result = subprocess.run(cmd, cwd=base)

    if result.returncode == 0:
        dist = os.path.join(base, "dist")
        exe_name = "Projet7Zip.exe" if sys.platform == "win32" else "Projet7Zip"
        exe_path = os.path.join(dist, exe_name)
        print(f"\n{'='*55}")
        print(f"  ✅ Exécutable créé :")
        print(f"     {exe_path}")
        print(f"{'='*55}")
    else:
        print("\n  ❌ Échec de la construction.")

if __name__ == "__main__":
    build()