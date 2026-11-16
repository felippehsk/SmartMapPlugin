# -*- coding: utf-8 -*-
"""Build a QGIS Install-from-ZIP package for Smart-Map.

Creates dist/Smart_Map.zip with top-level folder Smart_Map/ (required by
QGIS and by plugins['Smart_Map'] / :/plugins/Smart_Map/).

Optionally downloads platform wheels for offline first-run installs:

  & "C:\\Program Files\\QGIS 4.2.2\\bin\\python-qgis.bat" scripts\\build_plugin_zip.py --with-wheels
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DIST = os.path.join(ROOT, 'dist')
STAGE = os.path.join(DIST, '_stage', 'Smart_Map')
ZIP_PATH = os.path.join(DIST, 'Smart_Map.zip')
PLUGIN_NAME = 'Smart_Map'

INCLUDE_FILES = [
    '__init__.py',
    'Smart_Map.py',
    'Smart_Map_Dialog.py',
    'Smart_Map_Dialog.ui',
    'Smart_Map_About.py',
    'Smart_Map_About.ui',
    'metadata.txt',
    'resources.py',
    'resources.qrc',
    'icon.png',
    'icon_bra.png',
    'icon_usa.png',
    'LICENSE.txt',
    'sklearn37.zip',
    'sklearn39.zip',
]

INCLUDE_DIRS = [
    'utils',
    'krig',
    'pysal',
    'skfuzzy',
    'i18n',
    'wheels',
]

EXCLUDE_DIR_NAMES = {
    '__pycache__',
    '.git',
    '.github',
    'dist',
    'tests',
    'test',
    'tools',
    'scripts',
    'help',
}

EXCLUDE_FILE_GLOBS = [
    '*.pyc',
    '*.pyo',
    'execute_number.txt',
    'log.txt',
    '.DS_Store',
    'Thumbs.db',
]


def _ignored(name: str) -> bool:
    for pat in EXCLUDE_FILE_GLOBS:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def download_wheels(packages: list[str]) -> None:
    wheels = os.path.join(ROOT, 'wheels')
    os.makedirs(wheels, exist_ok=True)
    # Clear stale wheels so the zip stays coherent with this Python ABI.
    for name in os.listdir(wheels):
        path = os.path.join(wheels, name)
        if os.path.isfile(path) and (name.endswith('.whl') or name.endswith('.tar.gz')):
            os.remove(path)

    # --no-deps: do NOT vendor numpy/scipy (QGIS already ships them; shadowing breaks GDAL).
    for package in packages:
        cmd = [
            sys.executable,
            '-m',
            'pip',
            'download',
            '--dest',
            wheels,
            '--only-binary=:all:',
            '--no-deps',
            package,
        ]
        print('Downloading wheel:', ' '.join(cmd))
        subprocess.check_call(cmd)
    print('Wheels saved to', wheels)


def copy_tree(src: str, dst: str) -> None:
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES and not d.endswith('.egg-info')]
        rel = os.path.relpath(root, src)
        out_dir = dst if rel == '.' else os.path.join(dst, rel)
        os.makedirs(out_dir, exist_ok=True)
        for name in files:
            if _ignored(name):
                continue
            shutil.copy2(os.path.join(root, name), os.path.join(out_dir, name))


def stage_plugin() -> None:
    if os.path.isdir(os.path.join(DIST, '_stage')):
        shutil.rmtree(os.path.join(DIST, '_stage'))
    os.makedirs(STAGE, exist_ok=True)

    for name in INCLUDE_FILES:
        src = os.path.join(ROOT, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(STAGE, name))
        else:
            print('WARN missing file:', name)

    for name in INCLUDE_DIRS:
        src = os.path.join(ROOT, name)
        if os.path.isdir(src):
            copy_tree(src, os.path.join(STAGE, name))
        else:
            print('WARN missing dir:', name)

    # Ensure empty wheels dir exists so install_deps can look for it.
    os.makedirs(os.path.join(STAGE, 'wheels'), exist_ok=True)
    keep = os.path.join(STAGE, 'wheels', '.gitkeep')
    if not os.listdir(os.path.join(STAGE, 'wheels')):
        with open(keep, 'w', encoding='utf-8') as f:
            f.write('')


def write_zip() -> str:
    if os.path.isfile(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(STAGE):
            for name in files:
                full = os.path.join(root, name)
                # Archive path must start with Smart_Map/
                arc = os.path.join(PLUGIN_NAME, os.path.relpath(full, STAGE)).replace('\\', '/')
                zf.write(full, arcname=arc)
    return ZIP_PATH


def verify_zip(path: str) -> None:
    with zipfile.ZipFile(path, 'r') as zf:
        names = zf.namelist()
    required = [
        'Smart_Map/metadata.txt',
        'Smart_Map/__init__.py',
        'Smart_Map/Smart_Map.py',
        'Smart_Map/resources.py',
        'Smart_Map/utils/install_deps.py',
    ]
    missing = [r for r in required if r not in names]
    if missing:
        raise SystemExit('ZIP missing required entries: %s' % missing)
    # Guard against wrong top-level (Install from ZIP needs one plugin folder).
    tops = {n.split('/')[0] for n in names if n.strip()}
    if tops != {'Smart_Map'}:
        raise SystemExit('ZIP top-level must be only Smart_Map/, got: %s' % tops)
    print('ZIP OK: %d entries, top-level=%s' % (len(names), tops))


def main() -> int:
    parser = argparse.ArgumentParser(description='Build Smart_Map QGIS plugin ZIP')
    parser.add_argument(
        '--with-wheels',
        action='store_true',
        help='Download binary wheels for the current QGIS Python into ./wheels',
    )
    args = parser.parse_args()

    os.makedirs(DIST, exist_ok=True)

    if args.with_wheels:
        # Leaf packages only — numpy/scipy/pandas come from QGIS itself.
        download_wheels([
            'scikit-learn',
            'joblib',
            'threadpoolctl',
            'narwhals',
            'scikit-optimize',
            'pykrige',
            'pyaml',
            'cloudpickle',
        ])

    stage_plugin()
    path = write_zip()
    verify_zip(path)
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print('Created:', path)
    print('Size: %.2f MB' % size_mb)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
