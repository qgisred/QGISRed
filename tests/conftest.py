# -*- coding: utf-8 -*-
import sys
import os
from unittest.mock import MagicMock

# Calculate plugin root and parent directory
_PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_PARENT = os.path.dirname(_PLUGIN_ROOT)

# Add plugin parent to sys.path so we can import QGISRed as a package
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)


def _realQgisRequested():
    flag = os.environ.get('QGISRED_REAL_QGIS', '').strip().lower()
    if flag and flag not in ('0', 'false', 'no'):
        return True
    # conftest runs before pytest parses its arguments, so the flag is read from argv.
    return '--real-qgis' in sys.argv


def _bootstrapRealQgis():
    """Import the real QGIS so the mock block below finds sys.modules taken."""
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

    import qgis
    import qgis.core  # noqa: F401
    import qgis.gui  # noqa: F401
    import qgis.utils
    import qgis.PyQt.QtCore  # noqa: F401
    import qgis.PyQt.QtGui  # noqa: F401
    import qgis.PyQt.QtWidgets  # noqa: F401

    # 'processing' is a QGIS plugin, not part of the qgis package, so it sits
    # outside sys.path until its plugins directory is added.
    pluginsDir = os.path.join(os.path.dirname(os.path.dirname(qgis.__file__)), 'plugins')
    if pluginsDir not in sys.path:
        sys.path.append(pluginsDir)
    import processing  # noqa: F401

    from qgis.testing import start_app
    from qgis.testing.mocked import get_iface
    app = start_app()
    qgis.utils.iface = get_iface()
    return app


REAL_QGIS = _realQgisRequested()
QGIS_APP = None
if REAL_QGIS:
    try:
        QGIS_APP = _bootstrapRealQgis()
    except Exception as exc:
        # Falling back to the mocks here would let CI report a green real-QGIS
        # run that never loaded QGIS at all.
        raise RuntimeError(
            'Real QGIS was requested (QGISRED_REAL_QGIS / --real-qgis) but could '
            'not be loaded: %s: %s' % (type(exc).__name__, exc)
        )


# Shared Mocks for QGIS and PyQt5
# This ensures that even if tests import plugin code at the top level,
# the modules are already mocked.
if 'qgis' not in sys.modules:
    sys.modules['qgis'] = MagicMock()
if 'qgis.core' not in sys.modules:
    sys.modules['qgis.core'] = MagicMock()
if 'qgis.gui' not in sys.modules:
    sys.modules['qgis.gui'] = MagicMock()
if 'qgis.utils' not in sys.modules:
    sys.modules['qgis.utils'] = MagicMock()
if 'qgis.PyQt' not in sys.modules:
    mock_pyqt = MagicMock()
    mock_pyqt.__path__ = []
    sys.modules['qgis.PyQt'] = mock_pyqt
if 'qgis.PyQt.QtCore' not in sys.modules:
    sys.modules['qgis.PyQt.QtCore'] = MagicMock()
if 'qgis.PyQt.QtGui' not in sys.modules:
    sys.modules['qgis.PyQt.QtGui'] = MagicMock()
if 'qgis.PyQt.QtWidgets' not in sys.modules:
    sys.modules['qgis.PyQt.QtWidgets'] = MagicMock()
if 'processing' not in sys.modules:
    sys.modules['processing'] = MagicMock()
if 'PyQt5' not in sys.modules:
    sys.modules['PyQt5'] = MagicMock()
if 'PyQt5.QtCore' not in sys.modules:
    sys.modules['PyQt5.QtCore'] = MagicMock()
if 'PyQt5.QtWidgets' not in sys.modules:
    sys.modules['PyQt5.QtWidgets'] = MagicMock()
if 'PyQt5.QtGui' not in sys.modules:
    sys.modules['PyQt5.QtGui'] = MagicMock()


# Qt widget classes used as base classes must be real types (not MagicMock
# instances) to avoid metaclass conflicts in `class Foo(QDialog, FORM_CLASS):`
# constructs.  The metaclass also returns a MagicMock for any unknown class
# attribute (e.g. QDialog.DialogCode) so imports don't fail on attribute access.
class _QtStubMeta(type):
    def __getattr__(cls, name):
        return MagicMock()


def _qt_stub(name):
    return _QtStubMeta(name, (), {
        "__init__": lambda self, *a, **kw: None,
        "__getattr__": lambda self, attr: MagicMock(),
    })


_FORM_STUB = _qt_stub("FORM_CLASS")
_QT_WIDGET_STUBS = (
    "QDialog", "QDockWidget", "QWidget", "QMainWindow", "QFrame", "QTableView",
    "QStyledItemDelegate",
)

# Against the real QGIS only the bases the suite builds with object.__new__ need a
# stub; leaving the rest real lets widgets be passed to real Qt constructors.
_QT_WIDGET_STUBS_REAL = ("QDialog", "QDockWidget", "QMainWindow")

# Symbol classes the legend editor feeds to isinstance() to tell a marker from a
# line (see effectiveGeometryHint).  A MagicMock attribute is an instance, not a
# type, so isinstance() raises TypeError against it.  Test symbols are plain
# MagicMocks and match none of these stubs, so those checks come out False and
# the caller falls back to the layer's geometry hint.
_QGIS_SYMBOL_STUBS = ("QgsLineSymbol", "QgsMarkerSymbol", "QgsFillSymbol")


def _apply_qt_mock_config():
    """Apply uic.loadUiType and Qt widget stub configuration.

    Some test modules replace sys.modules['qgis.PyQt*'] at collection time,
    wiping out configuration done here at conftest import time.  This function
    re-applies the configuration so it can be called from a fixture as well.

    The Qt widget scaffolding is stubbed even in real-QGIS mode: the suite builds
    dialogs with object.__new__(Dialog), which sip rejects on real Qt bases.
    """
    _pyqt = sys.modules.get('qgis.PyQt')
    if _pyqt is not None:
        _pyqt.uic.loadUiType.return_value = (_FORM_STUB, None)
    _qtw = sys.modules.get('qgis.PyQt.QtWidgets')
    if _qtw is not None:
        for _name in (_QT_WIDGET_STUBS_REAL if REAL_QGIS else _QT_WIDGET_STUBS):
            setattr(_qtw, _name, _qt_stub(_name))
    _qgis_core = sys.modules.get('qgis.core')
    if _qgis_core is not None and not REAL_QGIS:
        for _name in _QGIS_SYMBOL_STUBS:
            setattr(_qgis_core, _name, _qt_stub(_name))
    _qgis_gui = sys.modules.get('qgis.gui')
    if _qgis_gui is not None:
        # QgsSymbolButton is subclassed (QGISRedSymbolColorSelector); it must be
        # a real type so the subclass keeps its methods instead of becoming a mock.
        _qgis_gui.QgsSymbolButton = _qt_stub("QgsSymbolButton")


_apply_qt_mock_config()

import pytest


@pytest.fixture(autouse=True)
def _ensure_qt_mock_config():
    """Re-apply Qt mock configuration before every test.

    Needed because test_map_tools_create_line.py replaces sys.modules['qgis.PyQt']
    at module-import (collection) time, resetting uic.loadUiType and widget stubs.
    """
    _apply_qt_mock_config()


def pytest_addoption(parser):
    parser.addoption(
        '--real-qgis', action='store_true', default=False,
        help='Run against the real QGIS instead of the mocks (needs a QGIS Python).',
    )
