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
if 'PyQt5' not in sys.modules:
    sys.modules['PyQt5'] = MagicMock()
if 'PyQt5.QtCore' not in sys.modules:
    sys.modules['PyQt5.QtCore'] = MagicMock()
if 'PyQt5.QtWidgets' not in sys.modules:
    sys.modules['PyQt5.QtWidgets'] = MagicMock()
if 'PyQt5.QtGui' not in sys.modules:
    sys.modules['PyQt5.QtGui'] = MagicMock()
