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
_QT_WIDGET_STUBS = ("QDialog", "QDockWidget", "QWidget", "QMainWindow", "QFrame", "QTableView")


def _apply_qt_mock_config():
    """Apply uic.loadUiType and Qt widget stub configuration.

    Some test modules replace sys.modules['qgis.PyQt*'] at collection time,
    wiping out configuration done here at conftest import time.  This function
    re-applies the configuration so it can be called from a fixture as well.
    """
    _pyqt = sys.modules.get('qgis.PyQt')
    if _pyqt is not None:
        _pyqt.uic.loadUiType.return_value = (_FORM_STUB, None)
    _qtw = sys.modules.get('qgis.PyQt.QtWidgets')
    if _qtw is not None:
        for _name in _QT_WIDGET_STUBS:
            setattr(_qtw, _name, _qt_stub(_name))


_apply_qt_mock_config()

import pytest


@pytest.fixture(autouse=True)
def _ensure_qt_mock_config():
    """Re-apply Qt mock configuration before every test.

    Needed because test_map_tools_create_line.py replaces sys.modules['qgis.PyQt']
    at module-import (collection) time, resetting uic.loadUiType and widget stubs.
    """
    _apply_qt_mock_config()
