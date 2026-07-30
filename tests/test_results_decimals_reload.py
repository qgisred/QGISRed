# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
import pytest
from QGISRed.ui.analysis.qgisred_results_appearance import _ResultsAppearanceMixin
from QGISRed.ui.analysis.qgisred_results_data import NODE_RESULT_FIELDS, LINK_RESULT_FIELDS
from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils


@pytest.fixture(autouse=True)
def flowUnits():
    """getDecimals resolves rows by flow unit, so the units entry must answer."""
    project = MagicMock()
    project.readEntry.return_value = ("LPS", True)
    with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj:
        MockProj.instance.return_value = project
        yield


class _StubField:
    def __init__(self, name, precision):
        self._name = name
        self._precision = precision

    def precision(self):
        return self._precision


class _StubFields:
    def __init__(self, fields):
        self._fields = list(fields)

    def names(self):
        return [f._name for f in self._fields]

    def indexOf(self, name):
        for index, field in enumerate(self._fields):
            if field._name == name:
                return index
        return -1

    def at(self, index):
        return self._fields[index]


def _layer(fields):
    layer = MagicMock()
    layer.fields.return_value = _StubFields(fields)
    return layer


def _defaultDecimals(element, fields_def, overrides=None):
    """Fields as prepareResultFields would create them: CSV default unless overridden."""
    utils = QGISRedFieldUtils()
    overrides = overrides or {}
    return [
        _StubField(name, overrides.get(name, utils.getDecimals(element, name)))
        for name, type_str, *_ in fields_def
        if type_str == "Double"
    ]


class MockDock(_ResultsAppearanceMixin):
    def __init__(self, node_layer=None, link_layer=None):
        self._varDecimals = {}
        self._statsMode = False
        self._layers = {"Node": node_layer, "Link": link_layer}
        self.rebuilt = 0

    def _findResultLayer(self, layer_type):
        return self._layers.get(layer_type)

    # Everything below is only reached when the guard decides a rebuild is needed.
    def _deferIfBusyReading(self, callback):
        self.rebuilt += 1
        return True  # stop before touching the providers


def test_matches_when_layers_use_csv_defaults():
    dock = MockDock(node_layer=_layer(_defaultDecimals("Nodes", NODE_RESULT_FIELDS)),
                    link_layer=_layer(_defaultDecimals("Links", LINK_RESULT_FIELDS)))
    assert dock._resultFieldsMatchDecimals()
    dock._reloadResultsWithNewDecimals()
    assert dock.rebuilt == 0


def test_reset_twice_does_not_reread_results():
    """Clearing an override rebuilds once; a second reset finds the defaults already in
    place and must not re-read the results."""
    dock = MockDock(node_layer=_layer(_defaultDecimals("Nodes", NODE_RESULT_FIELDS,
                                                       {"Pressure": 5})),
                    link_layer=_layer(_defaultDecimals("Links", LINK_RESULT_FIELDS)))
    dock._varDecimals = {}  # reset-all already cleared the overrides
    dock._reloadResultsWithNewDecimals()
    assert dock.rebuilt == 1

    # Second reset: the layers now carry the default precisions.
    dock._layers["Node"] = _layer(_defaultDecimals("Nodes", NODE_RESULT_FIELDS))
    dock._reloadResultsWithNewDecimals()
    assert dock.rebuilt == 1


def test_override_differing_from_layer_triggers_rebuild():
    dock = MockDock(node_layer=_layer(_defaultDecimals("Nodes", NODE_RESULT_FIELDS)))
    dock._varDecimals = {"Pressure": 4}
    assert not dock._resultFieldsMatchDecimals()
    dock._reloadResultsWithNewDecimals()
    assert dock.rebuilt == 1


def test_missing_double_field_triggers_rebuild():
    fields = _defaultDecimals("Nodes", NODE_RESULT_FIELDS)[1:]  # drop the first Double field
    dock = MockDock(node_layer=_layer(fields))
    assert not dock._resultFieldsMatchDecimals()


def test_signed_and_unsigned_flow_follow_the_flow_override():
    """Flow_Unsig / Flow_Sig alias to Flow, so an override on Flow applies to all three."""
    utils = QGISRedFieldUtils()
    flow_dec = utils.getDecimals("Links", "Flow")
    dock = MockDock(link_layer=_layer(_defaultDecimals("Links", LINK_RESULT_FIELDS)))
    dock._varDecimals = {"Flow": flow_dec + 1}
    assert not dock._resultFieldsMatchDecimals()

    dock._layers["Link"] = _layer(_defaultDecimals(
        "Links", LINK_RESULT_FIELDS,
        {"Flow": flow_dec + 1, "Flow_Unsig": flow_dec + 1, "Flow_Sig": flow_dec + 1}))
    assert dock._resultFieldsMatchDecimals()


def test_no_layers_is_a_noop():
    dock = MockDock()
    dock._reloadResultsWithNewDecimals()
    assert dock.rebuilt == 0
