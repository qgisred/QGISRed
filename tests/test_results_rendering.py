# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
import pytest
from QGISRed.ui.analysis.qgisred_results_rendering import _ResultsRenderingMixin
from QGISRed.ui.analysis.qgisred_results_appearance import _ResultsAppearanceMixin
from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils


# Helper to build a mock QgsProject
def _make_project(flow_unit="LPS"):
    proj = MagicMock()

    def read_entry(section, key, default=""):
        if section == "QGISRed" and key == "project_units":
            return flow_unit, True
        return default, False
    proj.readEntry.side_effect = read_entry
    return proj


class MockDock(_ResultsRenderingMixin):
    def __init__(self):
        self.cbNodeLabels = MagicMock()
        self.cbLinkLabels = MagicMock()
        self.spNodeDecimals = MagicMock()
        self.spLinkDecimals = MagicMock()
        self.lbNodesMagnitude = MagicMock()
        self.lbLinksMagnitude = MagicMock()
        self._labelFontSize = 10
        self._labelColorByRange = False
        self._labelShowId = False

    def tr(self, text):
        return text


@pytest.fixture(autouse=True)
def clear_cache():
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None


class TestResultsLabels:
    def test_set_layer_labels_show_id(self):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            
            MockProj.instance.return_value = _make_project("LPS")

            dock = MockDock()
            dock._labelShowId = True
            dock.cbNodeLabels.isChecked.return_value = True
            dock.spNodeDecimals.value.return_value = 2

            layer = MagicMock()
            layer.geometryType.return_value = 0  # Node

            # Call method under test
            dock.setLayerLabels(layer, "Pressure")

            # Extract the layer_settings passed to QgsVectorLayerSimpleLabeling
            assert MockLabeling.call_args is not None
            layer_settings = MockLabeling.call_args[0][0]

            # The fieldName attribute on settings contains the expression
            expr = layer_settings.fieldName
            
            # When show_id is True, first line should be the "Id" field
            assert '"Id"' in expr
            # Type case/when should NOT be present
            assert 'CASE' not in expr
            assert 'JUNCTION' not in expr
            # Second line should contain the formatted value
            assert 'format_number' in expr

    def test_set_layer_labels_no_show_id(self):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            
            MockProj.instance.return_value = _make_project("LPS")

            dock = MockDock()
            dock._labelShowId = False
            dock.cbNodeLabels.isChecked.return_value = True
            dock.spNodeDecimals.value.return_value = 2

            layer = MagicMock()
            layer.geometryType.return_value = 0  # Node

            dock.setLayerLabels(layer, "Pressure")

            assert MockLabeling.call_args is not None
            layer_settings = MockLabeling.call_args[0][0]

            expr = layer_settings.fieldName

            # When show_id is False, it should only show the value expression
            assert '"Id"' not in expr
            assert 'format_number("Pressure", 2)' in expr

    def test_set_layer_labels_status_groups_into_closed_and_active(self):
        # Status is a categorical string field: labels must group the 13 link
        # states into just "Closed" and "Active" (Open* → no label), never the
        # numeric format_number() that returns NULL for a text field.
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:

            MockProj.instance.return_value = _make_project("LPS")

            dock = MockDock()
            dock._labelShowId = True  # ignored for categorical Status
            dock.cbLinkLabels.isChecked.return_value = True
            dock.spLinkDecimals.value.return_value = 2

            layer = MagicMock()
            layer.geometryType.return_value = 1  # Link

            dock.setLayerLabels(layer, "Status")

            assert MockLabeling.call_args is not None
            expr = MockLabeling.call_args[0][0].fieldName

            assert "LIKE '%Closed%'" in expr
            assert "LIKE 'Active%'" in expr
            assert "'Closed'" in expr
            assert "'Active'" in expr
            # No Open group and no numeric formatting of the string field
            assert "Open" not in expr
            assert 'format_number("Status"' not in expr


# Regression tests: Flow labels must never show the sign — the label always uses abs().
class TestFlowLabelsNeverShowSign:
    def _get_expr(self, dock, layer, fieldName):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            MockProj.instance.return_value = _make_project("LPS")
            dock.setLayerLabels(layer, fieldName)
            assert MockLabeling.call_args is not None
            return MockLabeling.call_args[0][0].fieldName

    def _make_link_dock(self, show_id=False):
        dock = MockDock()
        dock._labelShowId = show_id
        dock.cbLinkLabels.isChecked.return_value = True
        dock.spLinkDecimals.value.return_value = 2
        return dock

    def _make_link_layer(self):
        layer = MagicMock()
        layer.geometryType.return_value = 1  # Link
        return layer

    def test_flow_label_is_absolute(self):
        dock = self._make_link_dock()
        expr = self._get_expr(dock, self._make_link_layer(), "Flow")
        assert 'abs("Flow")' in expr

    def test_flow_sig_label_is_absolute(self):
        dock = self._make_link_dock()
        expr = self._get_expr(dock, self._make_link_layer(), "Flow_Sig")
        assert 'abs("Flow_Sig")' in expr

    def test_non_flow_label_is_not_wrapped_in_abs(self):
        dock = self._make_link_dock()
        expr = self._get_expr(dock, self._make_link_layer(), "Velocity")
        assert 'abs(' not in expr
        assert '"Velocity"' in expr

    def test_flow_label_with_show_id_is_absolute(self):
        dock = self._make_link_dock(show_id=True)
        expr = self._get_expr(dock, self._make_link_layer(), "Flow")
        assert 'abs("Flow")' in expr


# Regression tests: the occurrence time (Max/Min stats) must NEVER appear in the map
# label — it is shown only in the tooltip. The label carries just the value.
class TestLabelsNeverShowOccurrenceTime:
    def _get_expr(self, dock, layer, fieldName):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            MockProj.instance.return_value = _make_project("LPS")
            dock.setLayerLabels(layer, fieldName)
            assert MockLabeling.call_args is not None
            return MockLabeling.call_args[0][0].fieldName

    def _make_link_dock(self, show_id=False):
        dock = MockDock()
        dock._labelShowId = show_id
        dock.cbLinkLabels.isChecked.return_value = True
        dock.spLinkDecimals.value.return_value = 2
        return dock

    def _make_link_layer(self):
        layer = MagicMock()
        layer.geometryType.return_value = 1  # Link
        return layer

    def test_label_has_no_time_reference(self):
        dock = self._make_link_dock()
        expr = self._get_expr(dock, self._make_link_layer(), "Velocity")
        assert "(@ " not in expr
        assert "Time" not in expr

    def test_label_with_show_id_has_no_time_reference(self):
        dock = self._make_link_dock(show_id=True)
        expr = self._get_expr(dock, self._make_link_layer(), "Velocity")
        assert "(@ " not in expr
        assert "Time" not in expr


# Regression tests: the map tooltip must show the occurrence time as a final "@ time"
# line when displaying a Maximum/Minimum statistic, and must not show any time line
# for regular (non-statistics) results.
class TestMapTipOccurrenceTime:
    def _make_dock(self, stats_mode, stat_label="Maximum"):
        dock = MockDock()
        dock._statsMode = stats_mode
        dock.lbl_maximum = "Maximum"
        dock.lbl_minimum = "Minimum"
        dock.TimeLabels = ["0:00"]
        dock.cbTimes = MagicMock()
        dock.cbTimes.currentIndex.return_value = 0
        dock._updateCivilDisplay = MagicMock()
        dock.timeTextChanged = MagicMock()

        dock.cbStatistics = MagicMock()
        dock.cbStatistics.currentText.return_value = stat_label

        dock.cbNodes = MagicMock()
        dock.cbNodes.currentIndex.return_value = 0  # None selected — Node side is skipped

        dock.cbLinks = MagicMock()
        dock.cbLinks.currentIndex.return_value = 1
        dock.cbLinks.currentText.return_value = "Flow"
        dock._link_field_map = {"Flow": "Flow"}

        dock.Scenario = "Base"
        dock.displayingLinkField = ""
        dock.setGraduatedPalette = MagicMock()
        dock.setLayerLabels = MagicMock()

        return dock

    def _paint_and_get_tip(self, dock):
        link_layer = MagicMock()
        dock._findResultLayer = MagicMock(side_effect=lambda name: link_layer if name == "Link" else None)

        with patch("QGISRed.ui.analysis.qgisred_results_rendering.QGISRedFieldUtils") as MockFieldUtils:
            MockFieldUtils.return_value.getUnitAbbreviation.return_value = ""
            dock.paintIntervalTimeResults(setRender=True)

        assert link_layer.setMapTipTemplate.call_args is not None
        return link_layer.setMapTipTemplate.call_args[0][0]

    def test_max_stat_tooltip_shows_time_as_last_line(self):
        dock = self._make_dock(stats_mode=True, stat_label="Maximum")
        tip = self._paint_and_get_tip(dock)
        lines = tip.split("<br>")
        assert lines[-1] == '@ [% "Time_H" %]'

    def test_min_stat_tooltip_shows_time_as_last_line(self):
        dock = self._make_dock(stats_mode=True, stat_label="Minimum")
        tip = self._paint_and_get_tip(dock)
        lines = tip.split("<br>")
        assert lines[-1] == '@ [% "Time_H" %]'

    def test_regular_result_tooltip_has_no_time_line(self):
        dock = self._make_dock(stats_mode=False)
        tip = self._paint_and_get_tip(dock)
        assert "@ [%" not in tip


# Regression test for a bug where switching a result variable to/from a rule-based
# renderer (Status) silently kept the previous style. Root cause: paintIntervalTimeResults
# used to overwrite self.displayingLinkField/NodeField with the NEW field *before* calling
# setGraduatedPalette, which used that same attribute to detect the OLD field. The check
# always compared the new field against itself, so the style reload was skipped.
class _FakeGraduatedRenderer:
    def __init__(self, field, ranges=None):
        self._field = field
        self._ranges = ranges or []

    def classAttribute(self):
        return self._field

    def setClassAttribute(self, field):
        self._field = field

    def ranges(self):
        return self._ranges

    def symbols(self, ctx):
        return []


class _FakeRule:
    def __init__(self, label="rule"):
        self._label = label

    def label(self):
        return self._label

    def children(self):
        return []

    def clone(self):
        return self


class _FakeRuleBasedRenderer:
    Rule = _FakeRule

    def __init__(self, root=None):
        self._root = root or _FakeRule()

    def rootRule(self):
        return self._root

    def symbols(self, ctx):
        return []


class TestPaintIntervalTimeResultsVariableOrdering:
    """Verifies the contract between paintIntervalTimeResults and setGraduatedPalette:
    the OLD field must be captured before self.displayingLinkField is overwritten."""

    def test_previous_field_is_captured_before_overwrite(self):
        dock = MockDock()
        dock._statsMode = False
        dock.TimeLabels = ["0:00"]
        dock.cbTimes = MagicMock()
        dock.cbTimes.currentIndex.return_value = 0
        dock._updateCivilDisplay = MagicMock()
        dock.timeTextChanged = MagicMock()

        dock.cbNodes = MagicMock()
        dock.cbNodes.currentIndex.return_value = 0  # None selected — Node side is skipped

        dock.cbLinks = MagicMock()
        dock.cbLinks.currentIndex.return_value = 1
        dock._link_field_map = {"Flow": "Flow", "Status": "Status"}

        link_layer = MagicMock()
        dock._findResultLayer = MagicMock(side_effect=lambda name: link_layer if name == "Link" else None)

        dock.Scenario = "Base"
        dock.setGraduatedPalette = MagicMock()

        with patch("QGISRed.ui.analysis.qgisred_results_rendering.QGISRedFieldUtils") as MockFieldUtils:
            MockFieldUtils.return_value.getUnitAbbreviation.return_value = ""

            # First paint: nothing displayed yet, variable is Flow
            dock.displayingLinkField = ""
            dock.cbLinks.currentText.return_value = "Flow"
            dock.paintIntervalTimeResults(setRender=True)

            args, _ = dock.setGraduatedPalette.call_args
            assert args[1] == "Flow"
            assert args[4] == ""  # previously_displayed: nothing shown before
            assert dock.displayingLinkField == "Flow"

            # Switch to Status: previously_displayed must still be "Flow" (the OLD value),
            # not "Status" (the bug compared the new field against itself).
            dock.cbLinks.currentText.return_value = "Status"
            dock.paintIntervalTimeResults(setRender=True)

            args, _ = dock.setGraduatedPalette.call_args
            assert args[1] == "Status"
            assert args[4] == "Flow"
            assert dock.displayingLinkField == "Status"


class TestSetGraduatedPaletteVariableSwitch:
    """End-to-end check that setGraduatedPalette actually swaps the renderer type
    when switching to/from Status, given a correctly-captured previously_displayed."""

    def test_switch_to_status_and_back_reloads_style(self):
        class _FakeNullHiddenLegend:
            pass

        with patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsGraduatedSymbolRenderer", _FakeGraduatedRenderer), \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsRuleBasedRenderer", _FakeRuleBasedRenderer), \
             patch("QGISRed.ui.analysis.qgisred_results_rendering._NullHiddenLegend", _FakeNullHiddenLegend), \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QGISRedStylingUtils") as MockStylingUtils:

            dock = MockDock()
            dock.ProjectDirectory = "C:/proj"
            dock.NetworkName = "Net"
            dock.iface = MagicMock()
            dock.Scenario = "Base"
            dock.Renders = {}
            dock._statsMode = False
            dock._currentStat = None
            dock._flowDirectionField = MagicMock(return_value=None)
            dock.getLayerPath = MagicMock(return_value="C:/proj/Results/Net_Base_Link.shp")
            dock.applySymbolScaleFactors = MagicMock()

            layer = MagicMock()
            layer.geometryType.return_value = 1  # Link

            state = {"renderer": _FakeGraduatedRenderer("Flow")}
            layer.renderer.side_effect = lambda: state["renderer"]
            layer.setRenderer.side_effect = lambda r: state.update(renderer=r)

            def fake_set_style(lyr, qml_name):
                if qml_name.endswith("_Status"):
                    state["renderer"] = _FakeRuleBasedRenderer()
                else:
                    state["renderer"] = _FakeGraduatedRenderer(qml_name.split("_", 1)[1])

            MockStylingUtils.return_value.setStyle.side_effect = fake_set_style

            # Displaying Flow, switch to Status
            dock.setGraduatedPalette(layer, "Status", True, "Link", previously_displayed="Flow")
            assert isinstance(state["renderer"], _FakeRuleBasedRenderer), (
                "Switching to Status must reload the Status style instead of keeping "
                "the previous numeric renderer"
            )

            # Switch back to Flow
            dock.setGraduatedPalette(layer, "Flow", True, "Link", previously_displayed="Status")
            assert isinstance(state["renderer"], _FakeGraduatedRenderer), (
                "Switching away from Status must reload a graduated style"
            )


# Regression tests: every real caller of setLayerLabels must match its signature.
# A previous change dropped the `time_field` argument from setLayerLabels but left
# a caller (_refreshLabelsIfShowing) passing it, raising TypeError at runtime. The
# existing setLayerLabels tests didn't catch it (they call it directly), and the
# paintIntervalTimeResults tests mock setLayerLabels away — a MagicMock accepts any
# signature. These tests exercise the caller chain with the REAL setLayerLabels.
class _AppearanceDock(_ResultsRenderingMixin, _ResultsAppearanceMixin):
    """Combines the rendering + appearance mixins to drive the real caller chain
    _onLabelStyleChanged -> _refreshLabelsIfShowing -> setLayerLabels."""

    def __init__(self, show_id=False):
        self.cbNodeLabels = MagicMock(); self.cbNodeLabels.isChecked.return_value = True
        self.cbLinkLabels = MagicMock(); self.cbLinkLabels.isChecked.return_value = True
        self.spNodeDecimals = MagicMock(); self.spNodeDecimals.value.return_value = 2
        self.spLinkDecimals = MagicMock(); self.spLinkDecimals.value.return_value = 2
        self.lbNodesMagnitude = MagicMock()
        self.lbLinksMagnitude = MagicMock()
        self.spFontSize = MagicMock(); self.spFontSize.value.return_value = 10
        self.rbColorByRange = MagicMock(); self.rbColorByRange.isChecked.return_value = False
        self.cbShowId = MagicMock(); self.cbShowId.isChecked.return_value = show_id
        self._labelFontSize = 10
        self._labelColorByRange = False
        self._labelShowId = show_id
        self._labelBgColor = None
        self._labelBgColorLocked = False
        self.cbNodes = MagicMock()
        self.cbNodes.currentIndex.return_value = 1
        self.cbNodes.currentText.return_value = "Pressure"
        self.cbLinks = MagicMock()
        self.cbLinks.currentIndex.return_value = 1
        self.cbLinks.currentText.return_value = "Velocity"
        self._node_field_map = {"Pressure": "Pressure"}
        self._link_field_map = {"Velocity": "Velocity"}
        self._saveAppearanceSettings = MagicMock()

    def tr(self, text):
        return text

    def _findResultLayer(self, layer_type, scenario=None):
        layer = MagicMock()
        layer.geometryType.return_value = 0 if layer_type == "Node" else 1
        return layer


class TestLabelStyleCallersMatchSignature:
    @pytest.mark.parametrize("show_id", [False, True])
    def test_on_label_style_changed_calls_real_setLayerLabels(self, show_id):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            MockProj.instance.return_value = _make_project("LPS")
            dock = _AppearanceDock(show_id=show_id)

            # Must not raise TypeError from a caller/setLayerLabels signature mismatch.
            dock._onLabelStyleChanged()

            # setLayerLabels ran for real for both Node and Link.
            assert MockLabeling.call_count == 2
