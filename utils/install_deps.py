# -*- coding: utf-8 -*-
"""
/***************************************************************************
#Arquivo: install_deps.py

                                 A QGIS plugin

                              -------------------
        begin                : 2018-08-15
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Gustavo Willam Pereira
                                           Domingos Sárvio Magalhães Valente
                                           Daniel Marçal de Queiroz
                                           Andre Luiz de Freitas Coelho
                                           Sandro Manuel Carmelino Hurtado
        email                : gustavowillam@gmail.com
 ***************************************************************************/
"""

import importlib
import os
import platform
import subprocess
import sys
import zipfile

from qgis.PyQt.QtWidgets import QApplication, QMessageBox, QProgressDialog
from qgis.PyQt.QtCore import Qt


system = platform.system()  # [Windows, Linux, Darwin]
print('\nOperation System:', system)

# (import_name, pip_spec) — packages required at runtime that are not vendored.
# numpy/scipy/pandas/matplotlib ship with most QGIS installs but are verified too.
REQUIRED_PACKAGES = [
    ('numpy', 'numpy'),
    ('scipy', 'scipy'),
    ('pandas', 'pandas'),
    ('matplotlib', 'matplotlib'),
    ('sklearn', 'scikit-learn'),
]

# Optional extras used by some workflows (safe to install if missing).
OPTIONAL_PACKAGES = [
    ('skopt', 'scikit-optimize'),
    ('pykrige', 'pykrige'),
]


def _python_minor_tuple(qgis_python_version):
    """Return (major, minor) from a sys.version string when possible."""
    try:
        parts = qgis_python_version.split()[0].split('.')
        return int(parts[0]), int(parts[1])
    except Exception:
        return 0, 0


def _plugin_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _wheels_dir():
    return os.path.join(_plugin_root(), 'wheels')


def _user_site_packages():
    """Writable site-packages under the active QGIS user profile (never Program Files)."""
    # .../python/plugins/Smart_Map/utils -> .../python/site-packages
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    python_dir = os.path.abspath(os.path.join(utils_dir, os.pardir, os.pardir, os.pardir))
    site = os.path.join(python_dir, 'site-packages')
    try:
        os.makedirs(site, exist_ok=True)
    except OSError:
        site = os.path.join(os.path.expanduser('~'), '.smart_map', 'site-packages')
        os.makedirs(site, exist_ok=True)
    if site not in sys.path:
        sys.path.insert(0, site)
    return site


def _ensure_pip():
    try:
        import pip  # noqa: F401
        return True
    except Exception:
        pass
    try:
        import ensurepip
        ensurepip.bootstrap(upgrade=True)
        return True
    except Exception as exc:
        print('ensurepip failed:', exc)
        return False


def _pip_install(pip_spec, target_dir=None, no_deps=False):
    """Install a package with the running QGIS Python interpreter."""
    if not _ensure_pip():
        raise RuntimeError('pip is not available in the QGIS Python environment')

    cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
    wheels = _wheels_dir()
    wheel_files = [
        f for f in (os.listdir(wheels) if os.path.isdir(wheels) else [])
        if f.endswith('.whl')
    ]
    if wheel_files:
        # Prefer offline / bundled wheels when present (Windows QGIS 4 package).
        cmd.extend(['--no-index', '--find-links', wheels])
    if no_deps:
        # Avoid shadowing QGIS-bundled numpy/scipy/GDAL with --target copies.
        cmd.append('--no-deps')
    if target_dir:
        cmd.extend(['--target', target_dir])
    else:
        cmd.append('--user')
    cmd.append(pip_spec)

    print('Running:', ' '.join(cmd))
    subprocess.check_call(cmd)


def _try_import(import_name):
    """Return (module, None) on success or (None, exception) on failure."""
    try:
        return importlib.import_module(import_name), None
    except Exception as exc:
        return None, exc


def _show_warning(text):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle('Smart-Map')
    msg_box.setText(text)
    msg_box.exec()


# Runtime helpers for scikit-learn / joblib when installing with --no-deps.
# Order matters: cloudpickle must be present before joblib can import.
SKLEARN_HELPERS = (
    ('cloudpickle', 'cloudpickle'),
    ('joblib', 'joblib'),
    ('threadpoolctl', 'threadpoolctl'),
    ('narwhals', 'narwhals'),
)

SKOPT_HELPERS = (
    ('cloudpickle', 'cloudpickle'),
    ('joblib', 'joblib'),
    ('pyaml', 'pyaml'),
    ('packaging', 'packaging'),
)


def _missing_helpers(helper_specs):
    missing = []
    for import_name, pip_spec in helper_specs:
        mod, _err = _try_import(import_name)
        if mod is None:
            missing.append((import_name, pip_spec))
    return missing


def _install_specs(specs, target, no_deps=True):
    for _import_name, pip_spec in specs:
        try:
            _pip_install(pip_spec, target_dir=target, no_deps=no_deps)
        except Exception as helper_err:
            print('target install failed for %s: %s' % (pip_spec, helper_err))
            _pip_install(pip_spec, target_dir=None, no_deps=no_deps)


def ensure_package(import_name, pip_spec, required=True):
    """Return True if import_name is available after optional install."""
    mod, err = _try_import(import_name)
    if mod is not None:
        ver = getattr(mod, '__version__', 'n/a')
        loc = getattr(mod, '__file__', 'n/a')
        print('%s already installed. version: %s Locale: %s' % (import_name, ver, loc))
        return True

    print('%s missing — attempting install (%s)' % (import_name, pip_spec))
    if err is not None:
        print('  import error before install:', err)

    target = _user_site_packages()
    # If QGIS already provides numpy/scipy, install leaf packages without deps
    # so --target cannot override the QGIS binary stack.
    numpy_mod, _ = _try_import('numpy')
    scipy_mod, _ = _try_import('scipy')
    core_ok = numpy_mod is not None and scipy_mod is not None
    no_deps = import_name in ('sklearn', 'skopt', 'pykrige') and core_ok

    helper_specs = []
    if no_deps and import_name == 'sklearn':
        helper_specs = _missing_helpers(SKLEARN_HELPERS)
    elif no_deps and import_name == 'skopt':
        helper_specs = _missing_helpers(SKOPT_HELPERS)

    progress = None
    try:
        progress = QProgressDialog(
            'Installing Python dependency:\n%s\n\nPlease wait…' % pip_spec,
            None,
            0,
            0,
        )
        progress.setWindowTitle('Smart-Map')
        try:
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        except AttributeError:
            # Qt5 fallback without scoped enum nesting
            progress.setWindowModality(getattr(Qt, 'ApplicationModal', 2))
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        if helper_specs:
            _install_specs(helper_specs, target, no_deps=True)

        try:
            _pip_install(pip_spec, target_dir=target, no_deps=no_deps)
        except Exception as first_err:
            print('target install failed:', first_err)
            # Fallback: --user into the roaming Python site-packages.
            _pip_install(pip_spec, target_dir=None, no_deps=no_deps)

        importlib.invalidate_caches()
        # Drop any half-imported dependency modules from a previous failed attempt.
        for stale in (
            'sklearn', 'joblib', 'cloudpickle', 'threadpoolctl', 'narwhals',
            'skopt', 'pyaml', 'pykrige',
        ):
            sys.modules.pop(stale, None)
            for key in list(sys.modules):
                if key.startswith(stale + '.'):
                    sys.modules.pop(key, None)

        mod, import_err = _try_import(import_name)
        if mod is not None:
            print('%s installed successfully.' % import_name)
            return True
        raise RuntimeError(
            'import still failing after pip install: %s' % import_err
        )
    except Exception as exc:
        print('Failed to install %s: %s' % (pip_spec, exc))
        if required:
            _show_warning(
                'Could not install required package "%s".\n\n'
                'Open the OSGeo4W / QGIS Python shell and run:\n'
                '  python -m pip install %s\n\n'
                'Details: %s' % (pip_spec, pip_spec, exc)
            )
        return False
    finally:
        if progress is not None:
            progress.close()


def unzip_external_package(qgis_python_version, library_name, path_to_zip_file, directory_to_extract_to):
    print('uncompressing:', library_name)

    major, minor = _python_minor_tuple(qgis_python_version)

    # Bundled wheels target CPython 3.7 / 3.9 only. Never extract them on
    # Python 3.10+ (QGIS 4 / Windows) — ABI and path issues will crash import.
    if major > 3 or (major == 3 and minor >= 10):
        print(library_name + ' zip skipped: no compatible bundled binary for Python '
              + str(major) + '.' + str(minor))
        return False

    os.makedirs(directory_to_extract_to, exist_ok=True)

    if "v3.9" in qgis_python_version or (major == 3 and minor == 9):
        zip_name = library_name + '39.zip'
    else:
        zip_name = library_name + '37.zip'

    with zipfile.ZipFile(os.path.join(path_to_zip_file, zip_name), 'r') as zip_ref:
        zip_ref.extractall(directory_to_extract_to)

    return True


def load_external_package(qgis_python_version, library_name, library_version, exec_number, unzip):
    directory_to_extract_to = os.path.dirname(os.path.abspath(__file__))
    if unzip is False:
        directory_to_extract_to = directory_to_extract_to[:-5]
    else:
        # Prefer the writable user profile python folder (APPDATA), never Program Files.
        directory_to_extract_to = directory_to_extract_to[:-23]

    directory_to_extract_to = os.path.join(directory_to_extract_to, 'site-packages')
    print('directory_to_extract_to', directory_to_extract_to)

    if (int(exec_number) == 0) and (unzip is True):
        path_to_zip_file = os.path.dirname(os.path.abspath(__file__))
        path_to_zip_file = path_to_zip_file[:-5]
        print('path_to_zip_file', path_to_zip_file)

        extracted = unzip_external_package(
            qgis_python_version, library_name, path_to_zip_file, directory_to_extract_to
        )
        if not extracted:
            return False

    if directory_to_extract_to not in sys.path:
        sys.path.append(directory_to_extract_to)
    print(library_name + " loaded.       version: " + library_version
          + " Locale: " + directory_to_extract_to)
    return True


# check qgis architecture / Python version
qgis_architecture = sys.version
qgis_python_version = sys.version


if "32 bit" in qgis_architecture:
    print("\nQGIS 32 bit")
    _show_warning(
        'This plugin only works on QGIS 64-bit. Please install 64-bit QGIS before installing the plugin.'
    )
else:
    print("\nQGIS 64 bit")
    print("\nChecking dependencies!")

    major, minor = _python_minor_tuple(qgis_python_version)

    # Legacy Windows QGIS 3 (Python < 3.10): keep sklearn37/39.zip fallback.
    if system == 'Windows' and (major < 3 or (major == 3 and minor < 10)):
        _sklearn_mod, _ = _try_import('sklearn')
        if _sklearn_mod is None:
            file_dir = os.path.dirname(os.path.abspath(__file__))
            exec_path = os.path.join(file_dir, 'execute_number.txt')
            if os.path.isfile(exec_path):
                with open(exec_path, 'r') as f:
                    exec_number = f.read().strip() or '0'
            else:
                exec_number = '0'
                with open(exec_path, 'w') as f:
                    f.write(exec_number)
            if "v3.9" in qgis_python_version or (major == 3 and minor == 9):
                dep = 'scikit-learn==0.24.2'
            else:
                dep = 'scikit-learn==0.22.2'
            load_external_package(qgis_python_version, 'sklearn', dep, exec_number, unzip=True)

    for import_name, pip_spec in REQUIRED_PACKAGES:
        ensure_package(import_name, pip_spec, required=True)

    for import_name, pip_spec in OPTIONAL_PACKAGES:
        ensure_package(import_name, pip_spec, required=False)

    print("Dependencies checked!")
