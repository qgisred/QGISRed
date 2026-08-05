# -*- coding: utf-8 -*-
"""Base demand columns of a consumption points theme.

A theme holds one column per base demand — one per billing run, say — from the third
column onwards. The rules live apart from the dialog so they can be checked on their own;
only applyFieldChanges reaches a layer.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

from unittest.mock import MagicMock, call

import pytest

from QGISRed.tools.utils.qgisred_base_demand_fields import (
    MAX_FIELD_NAME_LENGTH,
    NAME_DUPLICATE,
    NAME_EMPTY,
    NAME_INVALID,
    NAME_OK,
    NAME_TOO_LONG,
    applyFieldChanges,
    baseDemandFieldNames,
    planFieldChanges,
    suggestFieldName,
    validateFieldName,
    validateRows,
)


class TestBaseDemandFieldNames:
    def test_the_two_fixed_columns_are_not_base_demands(self):
        assert baseDemandFieldNames(["DemID", "Category", "BaseDem"]) == ["BaseDem"]

    def test_every_further_column_is_one(self):
        names = ["DemID", "Category", "BaseDem", "Fact2024", "Padron"]
        assert baseDemandFieldNames(names) == ["BaseDem", "Fact2024", "Padron"]

    def test_a_theme_with_only_the_fixed_columns_has_none(self):
        assert baseDemandFieldNames(["DemID", "Category"]) == []


class TestValidateFieldName:
    @pytest.mark.parametrize("name", ["BaseDem", "Fact2024", "A", "a_b_c"])
    def test_plain_names_are_accepted(self, name):
        assert validateFieldName(name) == NAME_OK

    def test_a_name_of_exactly_the_limit_is_accepted(self):
        assert validateFieldName("A" * MAX_FIELD_NAME_LENGTH) == NAME_OK

    def test_a_longer_name_is_refused(self):
        """A DBF column name holds ten characters and the file is the contract."""
        assert validateFieldName("A" * (MAX_FIELD_NAME_LENGTH + 1)) == NAME_TOO_LONG

    @pytest.mark.parametrize("name", ["", "   ", None])
    def test_an_empty_name_is_refused(self, name):
        assert validateFieldName(name) == NAME_EMPTY

    @pytest.mark.parametrize("name", ["2024Fact", "Fact 2024", "Fact-24", "Fact%", " Fact"])
    def test_a_name_a_dbf_cannot_hold_is_refused(self, name):
        assert validateFieldName(name) == NAME_INVALID

    def test_an_existing_name_is_refused(self):
        assert validateFieldName("BaseDem", ["BaseDem"]) == NAME_DUPLICATE

    def test_the_comparison_ignores_case(self):
        """A DBF cannot tell BaseDem from basedem."""
        assert validateFieldName("basedem", ["BaseDem"]) == NAME_DUPLICATE


class TestValidateRows:
    def test_a_sound_list_passes(self):
        rows = [("BaseDem", "BaseDem"), (None, "Fact2024")]
        assert validateRows(rows) == (NAME_OK, "")

    def test_a_theme_needs_at_least_one_field(self):
        assert validateRows([]) == (NAME_EMPTY, "")

    def test_two_rows_with_the_same_name_are_refused(self):
        rows = [("BaseDem", "Fact"), (None, "Fact")]
        assert validateRows(rows) == (NAME_DUPLICATE, "Fact")

    def test_the_offending_name_comes_back_for_the_message(self):
        rows = [("BaseDem", "BaseDem"), (None, "2024")]
        assert validateRows(rows) == (NAME_INVALID, "2024")

    def test_a_row_left_blank_is_refused(self):
        assert validateRows([("BaseDem", "")]) == (NAME_EMPTY, "")


class TestSuggestFieldName:
    """Adding a field offers the next free name in the family instead of a blank row."""

    def test_the_first_suggestion_is_the_name_the_dll_writes(self):
        from QGISRed.tools.utils.qgisred_auxiliary_layers import DEFAULT_BASE_DEMAND_FIELD
        assert suggestFieldName([]) == DEFAULT_BASE_DEMAND_FIELD

    def test_a_taken_stem_is_numbered_from_two(self):
        assert suggestFieldName(["BaseDem"]) == "BaseDem2"

    def test_the_number_skips_what_is_already_there(self):
        assert suggestFieldName(["BaseDem", "BaseDem2", "BaseDem3"]) == "BaseDem4"

    def test_a_gap_in_the_numbering_is_filled(self):
        assert suggestFieldName(["BaseDem", "BaseDem3"]) == "BaseDem2"

    def test_the_comparison_ignores_case(self):
        assert suggestFieldName(["basedem"]) == "BaseDem2"

    def test_the_suggestion_never_exceeds_the_dbf_limit(self):
        taken = ["Field"] + ["Field%d" % n for n in range(2, 100000)]
        suggested = suggestFieldName(taken, stem="Field")
        assert suggested == "" or len(suggested) <= MAX_FIELD_NAME_LENGTH

    def test_a_suggestion_is_always_a_valid_name(self):
        suggested = suggestFieldName(["BaseDem", "BaseDem2"])
        assert validateFieldName(suggested, ["BaseDem", "BaseDem2"]) == NAME_OK

    def test_blank_rows_do_not_count_as_taken(self):
        assert suggestFieldName(["", None]) == "BaseDem"


class TestPlanFieldChanges:
    def test_an_untouched_list_changes_nothing(self):
        rows = [("BaseDem", "BaseDem")]
        assert planFieldChanges(["BaseDem"], rows) == ({}, [], [])

    def test_a_new_row_is_an_addition(self):
        rows = [("BaseDem", "BaseDem"), (None, "Fact2024")]
        renames, additions, deletions = planFieldChanges(["BaseDem"], rows)
        assert (renames, additions, deletions) == ({}, ["Fact2024"], [])

    def test_a_missing_row_is_a_deletion(self):
        rows = [("BaseDem", "BaseDem")]
        renames, additions, deletions = planFieldChanges(["BaseDem", "Fact2024"], rows)
        assert (renames, additions, deletions) == ({}, [], ["Fact2024"])

    def test_an_edited_row_is_a_rename_not_a_delete_and_add(self):
        """Renaming keeps the column's values; only a real deletion throws them away."""
        rows = [("BaseDem", "Fact2023")]
        renames, additions, deletions = planFieldChanges(["BaseDem"], rows)
        assert renames == {"BaseDem": "Fact2023"}
        assert additions == []
        assert deletions == []

    def test_the_three_kinds_can_happen_at_once(self):
        rows = [("BaseDem", "Fact2023"), (None, "Fact2025")]
        renames, additions, deletions = planFieldChanges(["BaseDem", "Fact2024"], rows)
        assert renames == {"BaseDem": "Fact2023"}
        assert additions == ["Fact2025"]
        assert deletions == ["Fact2024"]

    def test_reusing_a_deleted_name_on_a_new_row_still_reads_as_both(self):
        rows = [(None, "BaseDem")]
        renames, additions, deletions = planFieldChanges(["BaseDem"], rows)
        assert additions == ["BaseDem"]
        assert deletions == ["BaseDem"]


def _layer(fieldNames):
    layer = MagicMock()
    fields = []
    for name in fieldNames:
        field = MagicMock()
        field.name.return_value = name
        fields.append(field)
    layer.fields.return_value = fields
    provider = layer.dataProvider.return_value
    provider.deleteAttributes.return_value = True
    provider.renameAttributes.return_value = True
    provider.addAttributes.return_value = True
    return layer, provider


class TestApplyFieldChanges:
    def test_nothing_to_do_touches_no_provider(self):
        layer, provider = _layer(["DemID", "Category", "BaseDem"])
        assert applyFieldChanges(layer, {}, [], []) == ""
        provider.deleteAttributes.assert_not_called()
        provider.renameAttributes.assert_not_called()
        provider.addAttributes.assert_not_called()

    def test_a_deletion_uses_the_index_in_the_file(self):
        layer, provider = _layer(["DemID", "Category", "BaseDem", "Fact2024"])
        applyFieldChanges(layer, {}, [], ["Fact2024"])
        provider.deleteAttributes.assert_called_once_with([3])

    def test_several_deletions_go_from_the_back(self):
        """Deleting a low index first would shift the ones still to come."""
        layer, provider = _layer(["DemID", "Category", "A", "B", "C"])
        applyFieldChanges(layer, {}, [], ["A", "C"])
        provider.deleteAttributes.assert_called_once_with([4, 2])

    def test_a_rename_maps_the_index_to_the_new_name(self):
        layer, provider = _layer(["DemID", "Category", "BaseDem"])
        applyFieldChanges(layer, {"BaseDem": "Fact2023"}, [], [])
        provider.renameAttributes.assert_called_once_with({2: "Fact2023"})

    def test_an_addition_creates_one_field(self):
        layer, provider = _layer(["DemID", "Category", "BaseDem"])
        applyFieldChanges(layer, {}, ["Fact2025"], [])
        provider.addAttributes.assert_called_once()
        assert len(provider.addAttributes.call_args[0][0]) == 1

    def test_the_provider_is_reloaded_between_steps(self):
        """OGR does not publish the new field list to the next call otherwise, and the
        columns end up in the wrong order."""
        layer, provider = _layer(["DemID", "Category", "A", "B"])
        applyFieldChanges(layer, {"B": "C"}, ["D"], ["A"])
        assert provider.reloadData.call_count == 2
        assert layer.updateFields.call_args_list == [call(), call(), call()]

    def test_a_provider_refusal_is_reported(self):
        layer, provider = _layer(["DemID", "Category", "A"])
        provider.deleteAttributes.return_value = False
        assert applyFieldChanges(layer, {}, [], ["A"]) != ""

    def test_a_failed_deletion_stops_before_renaming(self):
        layer, provider = _layer(["DemID", "Category", "A", "B"])
        provider.deleteAttributes.return_value = False
        applyFieldChanges(layer, {"B": "C"}, [], ["A"])
        provider.renameAttributes.assert_not_called()


class TestFieldsDialogValidation:
    """A bad name must be caught before the dialog closes, or the edits are thrown away."""

    def _dialog(self, rows):
        from QGISRed.ui.project.qgisred_layermanagement_dialog import _BaseDemandFieldsDialog

        dialog = _BaseDemandFieldsDialog.__new__(_BaseDemandFieldsDialog)
        dialog.messageBar = MagicMock()
        dialog.rows = lambda: rows
        return dialog

    def _accept(self, dialog):
        from QGISRed.ui.project.qgisred_layermanagement_dialog import _BaseDemandFieldsDialog

        base = _BaseDemandFieldsDialog.__mro__[1]
        accepted = []
        original = getattr(base, "accept", None)
        base.accept = lambda self: accepted.append(True)
        try:
            _BaseDemandFieldsDialog.accept(dialog)
        finally:
            if original is None:
                del base.accept
            else:
                base.accept = original
        return bool(accepted)

    def test_a_duplicate_keeps_the_dialog_open(self):
        dialog = self._dialog([("BaseDem", "Fact"), (None, "Fact")])
        assert self._accept(dialog) is False

    def test_the_complaint_is_shown_in_this_dialog(self):
        dialog = self._dialog([("BaseDem", "Fact"), (None, "Fact")])
        self._accept(dialog)
        assert dialog.messageBar.pushMessage.call_count == 1

    def test_an_empty_row_keeps_the_dialog_open(self):
        dialog = self._dialog([("BaseDem", "")])
        assert self._accept(dialog) is False

    def test_a_name_that_is_too_long_keeps_the_dialog_open(self):
        dialog = self._dialog([(None, "A" * (MAX_FIELD_NAME_LENGTH + 1))])
        assert self._accept(dialog) is False

    def test_sound_rows_let_it_close(self):
        dialog = self._dialog([("BaseDem", "BaseDem"), (None, "BaseDem2")])
        assert self._accept(dialog) is True
        dialog.messageBar.pushMessage.assert_not_called()
