# -*- coding: utf-8 -*-
"""Render cache of the results dock.

It remembers how each (layer, variable) looked so switching variables and coming back
does not throw the style away — including styles the user built through the QGIS
symbology panel, which never pass through this plugin's legend editor.
"""
from unittest.mock import MagicMock, patch

from QGISRed.ui.analysis.qgisred_results_rendering import _ResultsRenderingMixin


LAYER_PATH = "C:/proj/Results/Net_Base_Link.shp"


class _FakeRenderer:
    """Renderer double. Cloning yields an equal but distinct object, as QGIS does —
    the cache clones both on the way in and on the way out."""

    def __init__(self, kind="graduatedSymbol", tag="original"):
        self._kind = kind
        self.tag = tag

    def type(self):
        return self._kind

    def clone(self):
        return _FakeRenderer(self._kind, self.tag)

    def symbols(self, ctx):
        return []

    def __eq__(self, other):
        return isinstance(other, _FakeRenderer) and (other._kind, other.tag) == (self._kind, self.tag)


class _Unmatched:
    """Stands in for a QGIS renderer class so no isinstance() check in the code matches.

    Keeps setGraduatedPalette on the plain path — no class-attribute rewriting, no NULL
    rule handling — so these tests only exercise where the renderer comes from.
    """


class _CacheDock(_ResultsRenderingMixin):
    def __init__(self):
        self.Renders = {}
        self._renderKeyInUse = {}
        self._statsMode = False
        self._currentStat = None

    def getLayerPath(self, layer):
        return layer.path


def _layer(kind="graduatedSymbol", tag="original", path=LAYER_PATH):
    layer = MagicMock()
    layer.path = path
    layer.renderer.return_value = _FakeRenderer(kind, tag)
    return layer


class TestStorageKey:
    def test_time_mode_and_stat_mode_do_not_collide(self):
        dock = _CacheDock()
        timeKey = dock._getRenderStorageKey(LAYER_PATH, "Flow")

        dock._statsMode = True
        dock._currentStat = "Maximum"

        assert dock._getRenderStorageKey(LAYER_PATH, "Flow") != timeKey

    def test_each_statistic_gets_its_own_entry(self):
        dock = _CacheDock()
        dock._statsMode = True
        dock._currentStat = "Maximum"
        maxKey = dock._getRenderStorageKey(LAYER_PATH, "Flow")
        dock._currentStat = "Minimum"

        assert dock._getRenderStorageKey(LAYER_PATH, "Flow") != maxKey


class TestRememberCurrentRender:
    def test_files_the_renderer_under_the_key_it_was_applied_with(self):
        # Not under the current state: by the time a restyle happens, the variable and
        # the statistic have usually moved on already.
        dock = _CacheDock()
        key = "time|" + LAYER_PATH + "|Flow"
        dock._renderKeyInUse[LAYER_PATH] = key
        dock._statsMode = True
        dock._currentStat = "Maximum"

        dock.rememberCurrentRender(_layer(tag="flow-style"))

        assert list(dock.Renders) == [key]
        assert dock.Renders[key].tag == "flow-style"

    def test_a_layer_never_styled_by_us_is_not_remembered(self):
        dock = _CacheDock()

        dock.rememberCurrentRender(_layer())

        assert dock.Renders == {}

    def test_rule_based_renderers_are_remembered_whole(self):
        # Result layers end up rule-based after applyNullStyle adds the NULL class; the
        # old cache rebuilt their ranges with a regex and dropped whatever did not match.
        dock = _CacheDock()
        dock._renderKeyInUse[LAYER_PATH] = "k"

        dock.rememberCurrentRender(_layer("RuleRenderer", "rules"))

        assert dock.Renders["k"] == _FakeRenderer("RuleRenderer", "rules")

    def test_a_freshly_opened_layer_does_not_overwrite_a_real_style(self):
        # A result layer shows a single symbol only while it is being opened, before any
        # style reaches it. Caching that would replace the entry with an empty one.
        dock = _CacheDock()
        dock._renderKeyInUse[LAYER_PATH] = "k"
        dock.Renders["k"] = _FakeRenderer(tag="the-user-style")

        dock.rememberCurrentRender(_layer("singleSymbol"))

        assert dock.Renders["k"].tag == "the-user-style"

    def test_a_renderer_that_cannot_be_cloned_is_skipped(self):
        dock = _CacheDock()
        dock._renderKeyInUse[LAYER_PATH] = "k"
        layer = _layer()
        layer.renderer.return_value.clone = MagicMock(side_effect=RuntimeError("gone"))

        dock.rememberCurrentRender(layer)

        assert dock.Renders == {}


class TestLookupCachedRenderer:
    def test_returns_a_clone_so_the_entry_survives_being_used(self):
        dock = _CacheDock()
        entry = _FakeRenderer(tag="stored")
        dock.Renders["time|" + LAYER_PATH + "|Flow"] = entry

        found = dock._lookupCachedRenderer(_layer(), "Flow")

        assert found == entry and found is not entry

    def test_unknown_variable_returns_none(self):
        dock = _CacheDock()

        assert dock._lookupCachedRenderer(_layer(), "Velocity") is None


class TestRoundTripThroughSetGraduatedPalette:
    """The behaviour the cache exists for: leave a variable and come back to it."""

    def _dock(self):
        dock = _CacheDock()
        dock.ProjectDirectory = "C:/proj"
        dock.NetworkName = "Net"
        dock.iface = MagicMock()
        dock._flowDirectionField = MagicMock(return_value=None)
        dock.applySymbolScaleFactors = MagicMock()
        dock._warnIfNoClasses = MagicMock()
        return dock

    def _run(self, dock, layer, field, previous):
        with patch("QGISRed.ui.analysis.qgisred_results_rendering.QGISRedStylingUtils") as styling, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsProject"), \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsRuleBasedRenderer", _Unmatched), \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsGraduatedSymbolRenderer", _Unmatched):
            dock.setGraduatedPalette(layer, field, True, "Link", previously_displayed=previous)
            return styling.return_value.setStyle

    def test_the_style_the_user_left_behind_comes_back_untouched(self):
        dock = self._dock()
        layer = _layer()

        # Showing Flow. Whatever renderer sits on the layer now — ours, or one the user
        # built in the QGIS symbology panel — is what has to come back later.
        self._run(dock, layer, "Flow", None)
        layer.renderer.return_value = _FakeRenderer("RuleRenderer", "the-user-style")

        self._run(dock, layer, "Velocity", "Flow")            # switch away
        setStyle = self._run(dock, layer, "Flow", "Velocity")  # and back

        assert layer.setRenderer.call_args.args[0].tag == "the-user-style"
        assert not setStyle.called, "coming back to a remembered variable must not reload the QML"

    def test_a_variable_never_shown_before_loads_its_qml(self):
        dock = self._dock()

        setStyle = self._run(dock, _layer(), "Velocity", None)

        assert setStyle.call_args.args[1] == "LinkVelocity"


class TestCacheLifetime:
    def test_forgetting_a_key_stops_the_next_snapshot(self):
        dock = _CacheDock()
        dock._renderKeyInUse[LAYER_PATH] = "k"

        dock.forgetRenderKey(LAYER_PATH)
        dock.rememberCurrentRender(_layer())

        assert dock.Renders == {}

    def test_clearing_drops_everything(self):
        dock = _CacheDock()
        dock.Renders["k"] = _FakeRenderer()
        dock._renderKeyInUse[LAYER_PATH] = "k"

        dock.clearRenderCache()

        assert dock.Renders == {} and dock._renderKeyInUse == {}
