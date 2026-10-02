# -*- coding: utf-8 -*-
"""Fakes for driving the Queries by Properties dock without Qt.

The dock is built with object.__new__; the stubbed QDockWidget answers every unset
attribute with a MagicMock, so only what a test asserts on needs a fake that keeps
state: combo boxes (text plus per-role item data), layers (fields and features) and
QgsProject.instance().readEntry.
"""
from unittest.mock import MagicMock

from qgis.PyQt.QtCore import Qt

from QGISRed.ui.queries.qgisred_queriesbyproperties_dock import QGISRedQueriesByPropertiesDock

DOCK_MODULE = "QGISRed.ui.queries.qgisred_queriesbyproperties_dock"
PROJECT_UTILS_MODULE = "QGISRed.tools.utils.qgisred_project_utils"

_WIDGET_BUILDERS = ("setupValueStack", "initializeElementTypes", "setupConnections",
                    "setupButtonIcons", "updateProperties")


class FakeCombo:
    """Items hold a text and data per role, like QComboBox; separators are blank items."""

    def __init__(self, items=()):
        self._items = []
        self._current = -1
        self._enabled = True
        for text, data in items:
            self.addItem(text, data)

    def addItem(self, text, data=None):
        self._items.append({"text": text, "roles": {}})
        if data is not None:
            self.setItemData(self.count() - 1, data, Qt.ItemDataRole.UserRole)
        if self._current < 0:
            self._current = 0

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def insertSeparator(self, index):
        self._items.insert(index, {"text": "", "roles": {}})

    def insertItem(self, index, text, data=None):
        self._items.insert(index, {"text": text, "roles": {}})
        if data is not None:
            self.setItemData(index, data, Qt.ItemDataRole.UserRole)

    def setItemData(self, index, value, role=Qt.ItemDataRole.UserRole):
        self._items[index]["roles"][role] = value

    def itemData(self, index, role=Qt.ItemDataRole.UserRole):
        if 0 <= index < self.count():
            return self._items[index]["roles"].get(role)
        return None

    def itemText(self, index):
        return self._items[index]["text"] if 0 <= index < self.count() else ""

    def count(self):
        return len(self._items)

    def clear(self):
        self._items = []
        self._current = -1

    def currentIndex(self):
        return self._current

    def setCurrentIndex(self, index):
        self._current = index if 0 <= index < self.count() else -1

    def currentText(self):
        return self.itemText(self._current)

    def setCurrentText(self, text):
        self.setCurrentIndex(self.findText(text))

    def currentData(self, role=Qt.ItemDataRole.UserRole):
        return self.itemData(self._current, role)

    def findText(self, text):
        for index, item in enumerate(self._items):
            if item["text"] == text:
                return index
        return -1

    def findData(self, data, role=Qt.ItemDataRole.UserRole):
        for index, item in enumerate(self._items):
            if item["roles"].get(role) == data:
                return index
        return -1

    def internalNames(self):
        """The UserRole data of every item, '' for separators: what a query would use."""
        return [self.itemData(index) or "" for index in range(self.count())]

    def blockSignals(self, blocked):
        return False

    def setStyleSheet(self, text):
        pass

    def setEnabled(self, enabled):
        self._enabled = enabled

    def isEnabled(self):
        return self._enabled


class FakeField:
    def __init__(self, name, typeName="double"):
        self._name = name
        self._typeName = typeName

    def name(self):
        return self._name

    def typeName(self):
        return self._typeName


class FakeFields:
    def __init__(self, fields):
        self._fields = list(fields)

    def __iter__(self):
        return iter(self._fields)

    def indexFromName(self, name):
        for index, field in enumerate(self._fields):
            if field.name() == name:
                return index
        return -1

    def indexOf(self, name):
        return self.indexFromName(name)

    def field(self, index):
        return self._fields[index]


class FakeFeature:
    def __init__(self, fields, values, fid=0):
        self._fields = fields
        self._values = dict(values)
        self._fid = fid

    def id(self):
        return self._fid

    def __getitem__(self, name):
        return self._values.get(name)

    def attribute(self, index):
        return self._values.get(self._fields.field(index).name())

    def attributes(self):
        return [self._values.get(field.name()) for field in self._fields]

    def geometry(self):
        return MagicMock()


class FakeLayer:
    def __init__(self, identifier, fields, rows=(), name="", source=""):
        self._identifier = identifier
        self._fields = FakeFields(fields)
        self._features = [FakeFeature(self._fields, row, fid) for fid, row in enumerate(rows)]
        self._name = name or identifier
        self._source = source

    def customProperty(self, key, default=None):
        return self._identifier if key == "qgisred_identifier" else default

    def fields(self):
        return self._fields

    def getFeatures(self, request=None):
        return iter(self._features)

    def name(self):
        return self._name

    def id(self):
        return self._name

    def dataProvider(self):
        provider = MagicMock()
        provider.dataSourceUri.return_value = self._source
        return provider

    def removeSelection(self):
        pass


def makeProject(**entries):
    """QgsProject.instance() stand-in answering readEntry('QGISRed', key) from entries."""
    project = MagicMock()

    def readEntry(section, key, default=""):
        if section == "QGISRed" and key in entries:
            return entries[key], True
        return default, False

    project.readEntry.side_effect = readEntry
    return project


def makeDock():
    """A dock with its real lookup tables and fake combos, built without a form."""
    dock = object.__new__(QGISRedQueriesByPropertiesDock)
    dock.tr = lambda text: text
    for name in _WIDGET_BUILDERS:
        setattr(dock, name, lambda: None)
    dock.initializeQueriesByProperties()
    for name in _WIDGET_BUILDERS:
        delattr(dock, name)
    dock.cbElementType = FakeCombo()
    dock.cbProperty = FakeCombo()
    dock.cbStatisticsFor = FakeCombo()
    dock.cbCondition = FakeCombo()
    dock.cbValueList = FakeCombo()
    dock.cbValue = MagicMock()
    dock.cbValue.value.return_value = ""
    dock.valueStack = MagicMock()
    dock.valueStack.currentWidget.return_value = dock.cbValue
    dock.labelValueUnit = MagicMock()
    dock.labelStatisticsUnit = MagicMock()
    dock.labelResults = MagicMock()
    dock.lineResults = MagicMock()
    dock.radioSingleCriteria = MagicMock()
    dock.radioSingleCriteria.isChecked.return_value = True
    dock.radioMultipleCriteria = MagicMock()
    dock.radioMultipleCriteria.isChecked.return_value = False
    dock.multipleCriteriaComment = MagicMock()
    dock.multipleCriteriaComment.text.return_value = ""
    dock.iface = MagicMock()
    dock.canvas = MagicMock()
    dock.updateComboBoxBackground = lambda combo: None
    return dock
