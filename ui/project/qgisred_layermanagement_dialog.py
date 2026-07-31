# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog, QApplication, QLayout
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector

from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
from ...tools.qgisred_dependencies import QGISRedDependencies as GISRed

import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_layermanagement_dialog.ui"))

# Element name, checkbox, create button, and which GISRed.CreateLayer argument the
# element travels in. The name doubles as the shapefile suffix and, lowercased, as the
# qgisred_identifier suffix, so it must stay free of spaces.
_ELEMENTS = (
    ("Pipes", "cbPipes", "btPipes", False),
    ("Junctions", "cbJunctions", "btJunctions", False),
    ("Tanks", "cbTanks", "btTanks", False),
    ("Reservoirs", "cbReservoirs", "btReservoirs", False),
    ("Valves", "cbValves", "btValves", False),
    ("Pumps", "cbPumps", "btPumps", False),
    ("Demands", "cbDemands", "btDemands", True),
    ("Sources", "cbSources", "btSources", True),
    ("IsolationValves", "cbIsolatedValves", "btIsolatedValves", True),
    ("ServiceConnections", "cbConnections", "btConnections", True),
    ("Meters", "cbMeters", "btMeters", True),
)


class _Element:
    """One managed element type and the widgets that stand for it in the dialog."""

    def __init__(self, name, checkBox, createButton, complementary):
        self.name = name
        self.identifier = "qgisred_" + name.lower()
        self.checkBox = checkBox
        self.createButton = createButton
        self.complementary = complementary
        # The .ui text, already translated by setupUi. Used whenever the layer is not
        # open and there is no real layer name to show instead.
        self.defaultText = checkBox.text()


class QGISRedLayerManagementDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLayerManagementDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = None
        self.NetworkName = ""
        self.ProjectDirectory = ""

        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)
        self.btSelectCRS.clicked.connect(self.selectCRS)

        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)
        # Every row is a fixed-height checkbox, so there is nothing worth resizing. This
        # also keeps the dialog honest when the banner appears: SetFixedSize re-reads the
        # layout's hint, so the window grows to fit the message instead of squashing the
        # tabs, and shrinks back when it hides.
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.elements = [
            _Element(name, getattr(self, checkBox), getattr(self, button), complementary)
            for name, checkBox, button, complementary in _ELEMENTS
        ]
        for element in self.elements:
            element.createButton.clicked.connect(lambda _checked=False, e=element: self.createElement(e))

    def config(self, ifac, direct, netw, parent):
        self.iface = ifac
        self.parent = parent
        self.NetworkName = netw
        self.ProjectDirectory = direct

        self.utils = QGISRedLayerUtils(direct, netw, ifac)
        self.crs = self.utils.getProjectCrs()
        self.originalCrs = self.crs
        self.tbCRS.setText(self.crs.description())

        self.setProperties()

    """Element rows"""

    def getOpenLayersByIdentifier(self):
        """Map qgisred_identifier -> open layer for everything currently in the project."""
        found = {}
        for layer in self.utils.getLayers():
            identifier = layer.customProperty("qgisred_identifier")
            if identifier and identifier not in found:
                found[identifier] = layer
        return found

    def setProperties(self):
        """Refresh every row against what is on disk and what is open in QGIS."""
        existingFiles = set(os.listdir(self.ProjectDirectory))
        openLayers = self.getOpenLayersByIdentifier()

        for element in self.elements:
            onDisk = self.NetworkName + "_" + element.name + ".shp" in existingFiles
            layer = openLayers.get(element.identifier)
            # Projects saved before identifiers existed can only be matched by path.
            isOpen = layer is not None or self.utils.isLayerOpened(element.name)

            # The create button and the checkbox are exclusive: the button materialises
            # the missing shapefile, the checkbox decides whether an existing one loads.
            element.createButton.setVisible(not onDisk)
            element.checkBox.setChecked(isOpen)
            element.checkBox.setText(layer.name() if layer is not None else element.defaultText)
            # Pipes carry the network: once loaded they may not be unloaded.
            locked = element.name == "Pipes" and isOpen
            element.checkBox.setEnabled(onDisk and not locked)

    """Actions"""

    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if not projSelector.exec():
            return
        crs = projSelector.crs()
        if not crs.isValid():
            return
        # The DLL reprojects from an EPSG code alone. A custom CRS reaches it as a
        # "USER:xxxxx" identifier it cannot resolve, so refuse it here instead.
        if not crs.authid().startswith("EPSG:"):
            self.pushMessage(self.tr("Warning"), self.tr("Only coordinate systems with an EPSG code are supported"), level=1)
            return
        self.crs = crs
        self.tbCRS.setText(self.crs.description())

    def createElement(self, element):
        layer = "" if element.complementary else element.name
        complLayer = element.name if element.complementary else ""
        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.CreateLayer(self.ProjectDirectory, self.NetworkName, layer, complLayer)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            self.parent.openElementLayer(element.name)
            # The row now has a shapefile and an open layer. Redraw it and stay open, so
            # several elements can be created in one visit and any message stays readable.
            self.setProperties()
        elif resMessage == "False":
            self.pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1)
        else:
            self.pushMessage(self.tr("Error"), resMessage, level=2)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def accept(self):
        selected = [element.name for element in self.elements if element.checkBox.isChecked()]
        managed = [element.name for element in self.elements]

        epsg = None
        if self.crs != self.originalCrs:
            epsg = self.crs.authid().replace("EPSG:", "")
        self.parent.applyInputLayerSelection(selected, managed, epsg)

        super(QGISRedLayerManagementDialog, self).accept()
