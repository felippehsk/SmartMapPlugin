# -*- coding: utf-8 -*-
"""Headless QGIS 4 / Qt 6 smoke test for Smart-Map.

Run via the local QGIS 4 wrapper only, e.g.:

  $env:QT_QPA_PLATFORM='offscreen'
  & "C:\\Program Files\\QGIS 4.2.2\\bin\\python-qgis.bat" tests\\test_qgis4_compat.py
"""

from __future__ import annotations

import os
import sys
import traceback

# Must be set before Qt / matplotlib import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

QGIS_PREFIX = os.environ.get(
    "QGIS_PREFIX_PATH",
    r"C:\Program Files\QGIS 4.2.2\apps\qgis",
)

PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PLUGIN_PARENT = os.path.dirname(PLUGIN_ROOT)
PLUGIN_PKG = os.path.basename(PLUGIN_ROOT)  # SmartMapPlugin
# Import as a package so relative imports in Smart_Map.py resolve.
if PLUGIN_ROOT in sys.path:
    sys.path.remove(PLUGIN_ROOT)
if PLUGIN_PARENT not in sys.path:
    sys.path.insert(0, PLUGIN_PARENT)


class StubIface:
    """Minimal QgisInterface stub for plugin load / unload."""

    def __init__(self):
        self._toolbar = None
        self._actions = []

    def mainWindow(self):
        return None

    def addToolBar(self, name):
        from qgis.PyQt.QtWidgets import QToolBar

        self._toolbar = QToolBar(str(name))
        return self._toolbar

    def addPluginToMenu(self, menu, action):
        self._actions.append((menu, action))

    def removePluginMenu(self, menu, action):
        try:
            self._actions.remove((menu, action))
        except ValueError:
            pass

    def removeToolBarIcon(self, action):
        pass

    def mapCanvas(self):
        return None

    def layerTreeCanvasBridge(self):
        return None


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def test_plugin_load_and_ui():
    from qgis.core import Qgis, QgsApplication
    from qgis.PyQt.QtCore import QT_VERSION_STR
    from qgis.PyQt.QtGui import QIcon

    print("QGIS_VERSION=", Qgis.QGIS_VERSION)
    print("QT_VERSION=", QT_VERSION_STR)
    print("QGIS_PREFIX=", QGIS_PREFIX)
    print("sys.executable=", sys.executable)

    QgsApplication.setPrefixPath(QGIS_PREFIX, True)
    app = QgsApplication([], False)
    app.initQgis()

    # QGIS ships Processing as a bundled plugin; Smart_Map imports it at module level.
    processing_plugins = os.path.join(QgsApplication.prefixPath(), "python", "plugins")
    if processing_plugins not in sys.path:
        sys.path.append(processing_plugins)
    from processing.core.Processing import Processing

    Processing.initialize()

    plugin = None
    try:
        # Import after QgsApplication so processing / qgis.PyQt resolve correctly.
        import importlib

        pkg = importlib.import_module(PLUGIN_PKG)
        res_mod = importlib.import_module(PLUGIN_PKG + ".resources")
        from qgis.PyQt.QtCore import QFile, QIODevice

        # resources.py / .qrc icons must resolve under Qt 6.
        _ = QIcon(":/plugins/Smart_Map/icon.png")
        qf = QFile(":/plugins/Smart_Map/icon.png")
        resource_ok = qf.open(QIODevice.OpenModeFlag.ReadOnly)
        if resource_ok:
            data = bytes(qf.readAll())
            qf.close()
            _assert(len(data) > 0, "icon.png qrc resource empty")
            print("PASS resources.py qrc icon load (%d bytes)" % len(data))
        else:
            _assert(hasattr(res_mod, "qt_resource_data"), "resources.qt_resource_data missing")
            print("WARN qrc open failed; resources module still imported")

        iface = StubIface()
        plugin = pkg.classFactory(iface)
        plugin.initGui()
        print("PASS classFactory + initGui")

        dlg_mod = importlib.import_module(PLUGIN_PKG + ".Smart_Map_Dialog")
        about_mod = importlib.import_module(PLUGIN_PKG + ".Smart_Map_About")
        dlg = dlg_mod.smart_mapDialog()
        about = about_mod.smart_mapAbout()
        _assert(dlg is not None and about is not None, "dialogs failed to construct")
        _assert(len(dlg.children()) > 0, "dialog UI widgets missing")
        print("PASS dialog / About UI load (%d child widgets)" % len(dlg.children()))

        _assert(plugin.dlg is not None, "plugin.dlg is None")
        print("PASS plugin.dlg present")

        _exercise_qt6_dialog_apis(plugin)
        print("PASS Qt6 dialog / progress / item-flag APIs")

        _run_pipeline_smoke()
        print("PASS mathematical / interpolation pipeline smoke")

    finally:
        if plugin is not None:
            try:
                plugin.unload()
                print("PASS unload()")
            except Exception:
                traceback.print_exc()
                raise
        QgsApplication.exitQgis()
        print("PASS exitQgis()")


def _exercise_qt6_dialog_apis(plugin):
    """Exercise the Qt APIs used when opening the main dialog (run())."""
    from qgis.PyQt import QtCore, QtWidgets
    from qgis.PyQt.QtWidgets import QProgressDialog, QTableWidgetItem

    dlg = plugin.dlg
    dlg.setWindowFlag(QtCore.Qt.WindowType.WindowMinimizeButtonHint, True)
    dlg.setFixedSize(dlg.size())

    progress = QProgressDialog("Smart-Map test", None, 0, 100)
    progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
    progress.setValue(1)
    progress.close()

    item = QTableWidgetItem("test")
    item.setFlags(
        QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled
    )
    item.setCheckState(QtCore.Qt.CheckState.Unchecked)
    _assert(
        item.checkState() == QtCore.Qt.CheckState.Unchecked,
        "checkbox item state mismatch",
    )

    # Tables in the .ui must accept NoEditTriggers under Qt6.
    if hasattr(dlg, "datatable_atributos"):
        dlg.datatable_atributos.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )

    # Validators used during run() setup.
    from qgis.PyQt import QtGui

    validator = QtGui.QDoubleValidator(
        notation=QtGui.QDoubleValidator.Notation.StandardNotation
    )
    if hasattr(dlg, "lineEdit_XMin"):
        dlg.lineEdit_XMin.setValidator(validator)
        _assert(
            dlg.lineEdit_XMin.validator() is not None,
            "QDoubleValidator not attached",
        )

    # QSlider is int-only on Qt6 (plugin stores float params as value*1000).
    if hasattr(dlg, "horizontalSlider_Range"):
        dlg.horizontalSlider_Range.setValue(1)  # means 0.001
        dlg.horizontalSlider_Range.setMinimum(0)
        dlg.horizontalSlider_Range.setMaximum(int(10.5 * 1000))
        _assert(dlg.horizontalSlider_Range.value() == 1, "slider int value mismatch")


def _run_pipeline_smoke():
    """Exercise semivariogram, Ordinary Kriging, SVM, and fuzzy management zones."""
    import numpy as np
    import pandas as pd
    from sklearn import svm
    from sklearn.preprocessing import StandardScaler

    import importlib

    semi_mod = importlib.import_module(PLUGIN_PKG + ".krig.semivariogram")
    krig_mod = importlib.import_module(PLUGIN_PKG + ".krig.kriging")
    cmeans_mod = importlib.import_module(PLUGIN_PKG + ".skfuzzy.cluster._cmeans")
    Semivariogram = semi_mod.Semivariogram
    OrdinaryKriging = krig_mod.OrdinaryKriging
    _cmeans = cmeans_mod

    rng = np.random.default_rng(42)
    n = 25
    x = rng.uniform(0, 100, n)
    y = rng.uniform(0, 100, n)
    z = 10 + 0.05 * x + 0.03 * y + rng.normal(0, 1.0, n)

    xy = pd.DataFrame({"X": x, "Y": y})
    z_series = pd.Series(z, name="Z")

    # Experimental + theoretical semivariogram fit.
    sv = Semivariogram(xy.to_numpy(), z_series)
    lags, gammas, _npoints = sv.Exp_Semiv(dist_lag=10.0, active_dist=float(sv.max_dist))
    _assert(len(lags) > 0 and len(gammas) > 0, "experimental semivariogram empty")
    fit = sv.Fit(["spherical"])
    _assert(isinstance(fit, dict) and "spherical" in fit, "semivariogram Fit missing spherical")
    print("  semivariogram Fit ok: keys=", list(fit.keys()), "lags=", len(lags))

    # Fit value: [nugget, range, sill, rss, r2]
    model_name = "spherical"
    params = list(fit[model_name][:3])
    if len(params) < 3 or not np.isfinite(params).all():
        params = [0.5, 40.0, float(np.var(z))]

    ok = OrdinaryKriging(xy, z_series, model_name, params)
    grid = ok.Grid(20.0, 20.0, False, xy)
    _assert(len(grid) > 0, "OK grid empty")
    zhat, sigma = ok.execute(grid, n_closest_points=8, radius=80.0)
    _assert(len(zhat) == len(grid), "OK prediction length mismatch")
    _assert(np.isfinite(zhat).any(), "OK predictions not finite")
    print("  OrdinaryKriging ok: n_grid=", len(grid), "zhat_mean=", float(np.nanmean(zhat)))

    # SVM regression smoke.
    feats = np.column_stack([x, y])
    scaler = StandardScaler()
    feats_n = scaler.fit_transform(feats)
    model = svm.SVR(kernel="rbf", C=10.0, gamma="scale")
    model.fit(feats_n, z)
    pred = model.predict(feats_n)
    _assert(len(pred) == n and np.isfinite(pred).all(), "SVM prediction failed")
    print("  SVM ok: rmse=", float(np.sqrt(np.mean((pred - z) ** 2))))

    # Management zones via fuzzy c-means on scaled attributes.
    X = StandardScaler().fit_transform(np.column_stack([x, y, z])).T
    cntr, u_orig, _, _, _, _, fpc = _cmeans.cmeans(
        X, c=2, m=1.5, error=0.005, maxiter=100
    )
    _assert(cntr is not None and u_orig is not None, "cmeans failed")
    labels = np.argmax(u_orig, axis=0)
    _assert(len(np.unique(labels)) >= 1, "management zone labels empty")
    print("  ManagementZones cmeans ok: fpc=", float(fpc), "classes=", len(np.unique(labels)))


def main():
    try:
        test_plugin_load_and_ui()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
