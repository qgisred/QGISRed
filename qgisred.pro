SOURCES = qgisred.py \
          resources3x.py \
          sections/menu_section.py \
          sections/lifecycle_section.py \
          sections/project_management_section.py \
          sections/layer_management_section.py \
          sections/network_editing_section.py \
          sections/analysis_section.py \
          sections/queries_section.py \
          sections/tools_section.py \
          sections/debug_validation_section.py \
          sections/digital_twin_section.py \
          sections/utils_section.py \
          tools/qgisred_dependencies.py \
          ui/analysis/qgisred_results_binary.py \
          tools/qgisred_translatable_strings.py \
          tools/utils/qgisred_filesystem_utils.py \
          tools/utils/qgisred_field_utils.py \
          tools/utils/qgisred_styling_utils.py \
          tools/utils/qgisred_identifier_utils.py \
          tools/utils/qgisred_layer_utils.py \
          tools/utils/qgisred_project_io.py \
          tools/map_tools/qgisred_createConnection.py \
          tools/map_tools/qgisred_createPipe.py \
          tools/map_tools/qgisred_createLineTool.py \
          tools/map_tools/qgisred_editLinksGeometry.py \
          tools/map_tools/qgisred_identifyFeature.py \
          tools/map_tools/qgisred_moveNodes.py \
          tools/map_tools/qgisred_multilayerSelection.py \
          tools/map_tools/qgisred_selectPoint.py \
          ui/general/qgisred_about_dialog.py \
          ui/general/qgisred_cloneproject_dialog.py \
          ui/general/qgisred_createproject_dialog.py \
          ui/general/qgisred_import_dialog.py \
          ui/general/qgisred_loadproject_dialog.py \
          ui/general/qgisred_projectmanager_dialog.py \
          ui/general/qgisred_renameproject_dialog.py \
          ui/project/qgisred_custom_dialogs.py \
          ui/project/qgisred_layermanagement_dialog.py \
          ui/project/qgisred_legends_dialog.py \
          ui/queries/qgisred_element_explorer_dock.py \
          ui/queries/qgisred_queriesbyproperties_dock.py \
          ui/queries/qgisred_statisticsandgraphs_dock.py \
          ui/queries/qgisred_thematicmaps_dialog.py \
          ui/analysis/qgisred_results_dock.py \
          ui/analysis/qgisred_results_data.py \
          ui/analysis/qgisred_results_rendering.py \
          ui/analysis/qgisred_timeseries_dock.py \
          ui/analysis/timeseries_actions.py \
          ui/analysis/timeseries_legend_interaction.py \
          ui/analysis/timeseries_plot_layout.py \
          ui/analysis/timeseries_plot_renderer.py \
          ui/analysis/timeseries_plot_style.py \
          ui/analysis/qgisred_export_csv_dialog.py \
          ui/debug/qgisred_toolConnectivity_dialog.py \
          ui/debug/qgisred_toolLength_dialog.py \
          ui/digitaltwin/qgisred_toolConnections_dialog.py

FORMS = ui/general/qgisred_about_dialog.ui \
        ui/general/qgisred_cloneproject_dialog.ui \
        ui/general/qgisred_createproject_dialog.ui \
        ui/general/qgisred_import_dialog.ui \
        ui/general/qgisred_loadproject_dialog.ui \
        ui/general/qgisred_projectmanager_dialog.ui \
        ui/general/qgisred_renameproject_dialog.ui \
        ui/project/qgisred_layermanagement_dialog.ui \
        ui/project/qgisred_legends_dialog.ui \
        ui/queries/qgisred_element_explorer_dock.ui \
        ui/queries/qgisred_queriesbyproperties_dock.ui \
        ui/queries/qgisred_statisticsandgraphs_dock.ui \
        ui/queries/qgisred_thematicmaps_dialog.ui \
        ui/analysis/qgisred_results_dock.ui \
        ui/analysis/qgisred_timeseries_dock.ui \
        ui/analysis/qgisred_export_csv_dialog.ui \
        ui/debug/qgisred_toolConnectivity_dialog.ui \
        ui/debug/qgisred_toolLength_dialog.ui \
        ui/digitaltwin/qgisred_toolConnections_dialog.ui

TRANSLATIONS = i18n/qgisred.ts \
               i18n/qgisred_es.ts \
               i18n/qgisred_fr.ts \
               i18n/qgisred_pt.ts
