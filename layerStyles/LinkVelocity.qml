<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis autoRefreshTime="0" simplifyDrawingTol="1" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" version="3.40.0-Bratislava" styleCategories="LayerConfiguration|Symbology|Labeling|Fields|MapTips|AttributeTable|Rendering|CustomProperties|Notes" symbologyReferenceScale="-1" simplifyDrawingHints="1" simplifyLocal="1" autoRefreshMode="Disabled" readOnly="0" minScale="100000000" maxScale="0" labelsEnabled="0" simplifyMaxScale="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <renderer-v2 type="graduatedSymbol" graduatedMethod="GraduatedColor" enableorderby="0" forceraster="0" referencescale="-1" attr="Time" symbollevels="0">
    <ranges>
      <range lower="-10000000000.000000000000000" upper="0.100000000000000" uuid="{3c75bd72-cb7c-4a75-93df-560352c2bc05}" symbol="0" render="true" label="&lt;0.1"/>
      <range lower="0.100000000000000" upper="0.500000000000000" uuid="{fa4c49a4-f8cf-41e2-b7b7-c546d8a7358b}" symbol="1" render="true" label="0.1-0.5"/>
      <range lower="0.500000000000000" upper="1.000000000000000" uuid="{c758a661-85ce-4f69-ae18-1712bccdbc36}" symbol="2" render="true" label="0.5-1"/>
      <range lower="1.000000000000000" upper="2.000000000000000" uuid="{9268d5cc-fc96-42bf-a68a-34a164caa8a4}" symbol="3" render="true" label="1-2"/>
      <range lower="2.000000000000000" upper="10000000000.000000000000000" uuid="{70ed052f-5573-4daf-871c-e097cf7db8e7}" symbol="4" render="true" label=">2"/>
    </ranges>
    <symbols>
      <symbol clip_to_extent="1" type="line" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="0">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" id="{0c72d34b-69d9-4868-92bc-6b247e45f01b}" pass="0" class="SimpleLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="0,0,255,255,rgb:0,0,1,1" name="line_color"/>
            <Option type="QString" value="solid" name="line_style"/>
            <Option type="QString" value="0.26" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" id="{8508dd19-33a4-48e1-89fc-22de9b4ab501}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@0@1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{92e527df-f50f-4c64-bb23-97021ead9da2}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='PUMP', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{1012121d-0a2a-4507-b90c-48be85a31e92}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@0@2">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{4ccf35e3-7cab-4137-a0ba-ded2276c7b47}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='VALVE', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{7e1f0d17-69a5-4cfd-8302-65c742d17535}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@0@3">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{a1c4ea3f-29f5-4b71-bc90-04eb05d4163b}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{55d1d816-fb6c-4033-8f1a-a02f791c5041}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@0@4">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{82ff4439-b131-4e6c-b4f3-45f53d70c7ef}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="180" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" type="line" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="1">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" id="{0c72d34b-69d9-4868-92bc-6b247e45f01b}" pass="0" class="SimpleLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="0,255,255,255,rgb:0,1,1,1" name="line_color"/>
            <Option type="QString" value="solid" name="line_style"/>
            <Option type="QString" value="0.26" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" id="{8508dd19-33a4-48e1-89fc-22de9b4ab501}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@1@1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{92e527df-f50f-4c64-bb23-97021ead9da2}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='PUMP', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{1012121d-0a2a-4507-b90c-48be85a31e92}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@1@2">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{4ccf35e3-7cab-4137-a0ba-ded2276c7b47}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='VALVE', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{7e1f0d17-69a5-4cfd-8302-65c742d17535}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@1@3">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{a1c4ea3f-29f5-4b71-bc90-04eb05d4163b}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{55d1d816-fb6c-4033-8f1a-a02f791c5041}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@1@4">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{82ff4439-b131-4e6c-b4f3-45f53d70c7ef}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="180" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" type="line" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="2">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" id="{0c72d34b-69d9-4868-92bc-6b247e45f01b}" pass="0" class="SimpleLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="0,255,0,255,rgb:0,1,0,1" name="line_color"/>
            <Option type="QString" value="solid" name="line_style"/>
            <Option type="QString" value="0.26" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" id="{8508dd19-33a4-48e1-89fc-22de9b4ab501}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@2@1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{92e527df-f50f-4c64-bb23-97021ead9da2}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='PUMP', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{1012121d-0a2a-4507-b90c-48be85a31e92}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@2@2">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{4ccf35e3-7cab-4137-a0ba-ded2276c7b47}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='VALVE', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{7e1f0d17-69a5-4cfd-8302-65c742d17535}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@2@3">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{a1c4ea3f-29f5-4b71-bc90-04eb05d4163b}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{55d1d816-fb6c-4033-8f1a-a02f791c5041}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@2@4">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{82ff4439-b131-4e6c-b4f3-45f53d70c7ef}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="180" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" type="line" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="3">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" id="{0c72d34b-69d9-4868-92bc-6b247e45f01b}" pass="0" class="SimpleLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="255,255,0,255,rgb:1,1,0,1" name="line_color"/>
            <Option type="QString" value="solid" name="line_style"/>
            <Option type="QString" value="0.26" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" id="{8508dd19-33a4-48e1-89fc-22de9b4ab501}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@3@1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{92e527df-f50f-4c64-bb23-97021ead9da2}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='PUMP', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{1012121d-0a2a-4507-b90c-48be85a31e92}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@3@2">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{4ccf35e3-7cab-4137-a0ba-ded2276c7b47}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='VALVE', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{7e1f0d17-69a5-4cfd-8302-65c742d17535}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@3@3">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{a1c4ea3f-29f5-4b71-bc90-04eb05d4163b}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{55d1d816-fb6c-4033-8f1a-a02f791c5041}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@3@4">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{82ff4439-b131-4e6c-b4f3-45f53d70c7ef}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="180" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol clip_to_extent="1" type="line" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="4">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" id="{0c72d34b-69d9-4868-92bc-6b247e45f01b}" pass="0" class="SimpleLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="165,0,0,255,rgb:0.6470588235294118,0,0,1" name="line_color"/>
            <Option type="QString" value="solid" name="line_style"/>
            <Option type="QString" value="0.26" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" id="{8508dd19-33a4-48e1-89fc-22de9b4ab501}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@4@1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{92e527df-f50f-4c64-bb23-97021ead9da2}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='PUMP', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{1012121d-0a2a-4507-b90c-48be85a31e92}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@4@2">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{4ccf35e3-7cab-4137-a0ba-ded2276c7b47}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(&quot;Type&quot;='VALVE', 6, 0)" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{7e1f0d17-69a5-4cfd-8302-65c742d17535}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@4@3">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{a1c4ea3f-29f5-4b71-bc90-04eb05d4163b}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" id="{55d1d816-fb6c-4033-8f1a-a02f791c5041}" pass="0" class="MarkerLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="4" name="average_angle_length"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="average_angle_map_unit_scale"/>
            <Option type="QString" value="MM" name="average_angle_unit"/>
            <Option type="QString" value="3" name="interval"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="interval_map_unit_scale"/>
            <Option type="QString" value="MM" name="interval_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="0" name="offset_along_line"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_along_line_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_along_line_unit"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="bool" value="true" name="place_on_every_part"/>
            <Option type="QString" value="CentralPoint" name="placements"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="1" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol clip_to_extent="1" type="marker" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="@4@4">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" id="{82ff4439-b131-4e6c-b4f3-45f53d70c7ef}" pass="0" class="SvgMarker" locked="0">
              <Option type="Map">
                <Option type="QString" value="180" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="0" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="0" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                  </Option>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
    <classificationMethod id="Custom">
      <symmetricMode enabled="0" astride="0" symmetrypoint="0"/>
      <labelFormat format="%1 - %2" labelprecision="4" trimtrailingzeroes="1"/>
      <parameters>
        <Option/>
      </parameters>
      <extraInformation/>
    </classificationMethod>
    <rotation/>
    <sizescale/>
    <data-defined-properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol clip_to_extent="1" type="line" is_animated="0" frame_rate="10" alpha="1" force_rhr="0" name="">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" id="{57c1d95b-c39e-418a-84c4-ffff7e12a6eb}" pass="0" class="SimpleLine" locked="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="line_color"/>
            <Option type="QString" value="solid" name="line_style"/>
            <Option type="QString" value="0.26" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <customproperties>
    <Option type="Map">
      <Option type="int" value="0" name="embeddedWidgets/count"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <fieldConfiguration>
    <field name="Id" configurationFlags="NoFlag"/>
    <field name="Type" configurationFlags="NoFlag"/>
    <field name="Time" configurationFlags="NoFlag"/>
    <field name="T0" configurationFlags="NoFlag"/>
    <field name="T1" configurationFlags="NoFlag"/>
    <field name="T2" configurationFlags="NoFlag"/>
    <field name="T3" configurationFlags="NoFlag"/>
    <field name="T4" configurationFlags="NoFlag"/>
    <field name="T5" configurationFlags="NoFlag"/>
    <field name="T6" configurationFlags="NoFlag"/>
    <field name="T7" configurationFlags="NoFlag"/>
    <field name="T8" configurationFlags="NoFlag"/>
    <field name="T9" configurationFlags="NoFlag"/>
    <field name="T10" configurationFlags="NoFlag"/>
    <field name="T11" configurationFlags="NoFlag"/>
    <field name="T12" configurationFlags="NoFlag"/>
    <field name="T13" configurationFlags="NoFlag"/>
    <field name="T14" configurationFlags="NoFlag"/>
    <field name="T15" configurationFlags="NoFlag"/>
    <field name="T16" configurationFlags="NoFlag"/>
    <field name="T17" configurationFlags="NoFlag"/>
    <field name="T18" configurationFlags="NoFlag"/>
    <field name="T19" configurationFlags="NoFlag"/>
    <field name="T20" configurationFlags="NoFlag"/>
    <field name="T21" configurationFlags="NoFlag"/>
    <field name="T22" configurationFlags="NoFlag"/>
    <field name="T23" configurationFlags="NoFlag"/>
    <field name="T24" configurationFlags="NoFlag"/>
    <field name="T25" configurationFlags="NoFlag"/>
    <field name="T26" configurationFlags="NoFlag"/>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="Id" name=""/>
    <alias index="1" field="Type" name=""/>
    <alias index="2" field="Time" name=""/>
    <alias index="3" field="T0" name=""/>
    <alias index="4" field="T1" name=""/>
    <alias index="5" field="T2" name=""/>
    <alias index="6" field="T3" name=""/>
    <alias index="7" field="T4" name=""/>
    <alias index="8" field="T5" name=""/>
    <alias index="9" field="T6" name=""/>
    <alias index="10" field="T7" name=""/>
    <alias index="11" field="T8" name=""/>
    <alias index="12" field="T9" name=""/>
    <alias index="13" field="T10" name=""/>
    <alias index="14" field="T11" name=""/>
    <alias index="15" field="T12" name=""/>
    <alias index="16" field="T13" name=""/>
    <alias index="17" field="T14" name=""/>
    <alias index="18" field="T15" name=""/>
    <alias index="19" field="T16" name=""/>
    <alias index="20" field="T17" name=""/>
    <alias index="21" field="T18" name=""/>
    <alias index="22" field="T19" name=""/>
    <alias index="23" field="T20" name=""/>
    <alias index="24" field="T21" name=""/>
    <alias index="25" field="T22" name=""/>
    <alias index="26" field="T23" name=""/>
    <alias index="27" field="T24" name=""/>
    <alias index="28" field="T25" name=""/>
    <alias index="29" field="T26" name=""/>
  </aliases>
  <splitPolicies>
    <policy policy="Duplicate" field="Id"/>
    <policy policy="Duplicate" field="Type"/>
    <policy policy="Duplicate" field="Time"/>
    <policy policy="Duplicate" field="T0"/>
    <policy policy="Duplicate" field="T1"/>
    <policy policy="Duplicate" field="T2"/>
    <policy policy="Duplicate" field="T3"/>
    <policy policy="Duplicate" field="T4"/>
    <policy policy="Duplicate" field="T5"/>
    <policy policy="Duplicate" field="T6"/>
    <policy policy="Duplicate" field="T7"/>
    <policy policy="Duplicate" field="T8"/>
    <policy policy="Duplicate" field="T9"/>
    <policy policy="Duplicate" field="T10"/>
    <policy policy="Duplicate" field="T11"/>
    <policy policy="Duplicate" field="T12"/>
    <policy policy="Duplicate" field="T13"/>
    <policy policy="Duplicate" field="T14"/>
    <policy policy="Duplicate" field="T15"/>
    <policy policy="Duplicate" field="T16"/>
    <policy policy="Duplicate" field="T17"/>
    <policy policy="Duplicate" field="T18"/>
    <policy policy="Duplicate" field="T19"/>
    <policy policy="Duplicate" field="T20"/>
    <policy policy="Duplicate" field="T21"/>
    <policy policy="Duplicate" field="T22"/>
    <policy policy="Duplicate" field="T23"/>
    <policy policy="Duplicate" field="T24"/>
    <policy policy="Duplicate" field="T25"/>
    <policy policy="Duplicate" field="T26"/>
  </splitPolicies>
  <duplicatePolicies>
    <policy policy="Duplicate" field="Id"/>
    <policy policy="Duplicate" field="Type"/>
    <policy policy="Duplicate" field="Time"/>
    <policy policy="Duplicate" field="T0"/>
    <policy policy="Duplicate" field="T1"/>
    <policy policy="Duplicate" field="T2"/>
    <policy policy="Duplicate" field="T3"/>
    <policy policy="Duplicate" field="T4"/>
    <policy policy="Duplicate" field="T5"/>
    <policy policy="Duplicate" field="T6"/>
    <policy policy="Duplicate" field="T7"/>
    <policy policy="Duplicate" field="T8"/>
    <policy policy="Duplicate" field="T9"/>
    <policy policy="Duplicate" field="T10"/>
    <policy policy="Duplicate" field="T11"/>
    <policy policy="Duplicate" field="T12"/>
    <policy policy="Duplicate" field="T13"/>
    <policy policy="Duplicate" field="T14"/>
    <policy policy="Duplicate" field="T15"/>
    <policy policy="Duplicate" field="T16"/>
    <policy policy="Duplicate" field="T17"/>
    <policy policy="Duplicate" field="T18"/>
    <policy policy="Duplicate" field="T19"/>
    <policy policy="Duplicate" field="T20"/>
    <policy policy="Duplicate" field="T21"/>
    <policy policy="Duplicate" field="T22"/>
    <policy policy="Duplicate" field="T23"/>
    <policy policy="Duplicate" field="T24"/>
    <policy policy="Duplicate" field="T25"/>
    <policy policy="Duplicate" field="T26"/>
  </duplicatePolicies>
  <defaults>
    <default field="Id" expression="" applyOnUpdate="0"/>
    <default field="Type" expression="" applyOnUpdate="0"/>
    <default field="Time" expression="" applyOnUpdate="0"/>
    <default field="T0" expression="" applyOnUpdate="0"/>
    <default field="T1" expression="" applyOnUpdate="0"/>
    <default field="T2" expression="" applyOnUpdate="0"/>
    <default field="T3" expression="" applyOnUpdate="0"/>
    <default field="T4" expression="" applyOnUpdate="0"/>
    <default field="T5" expression="" applyOnUpdate="0"/>
    <default field="T6" expression="" applyOnUpdate="0"/>
    <default field="T7" expression="" applyOnUpdate="0"/>
    <default field="T8" expression="" applyOnUpdate="0"/>
    <default field="T9" expression="" applyOnUpdate="0"/>
    <default field="T10" expression="" applyOnUpdate="0"/>
    <default field="T11" expression="" applyOnUpdate="0"/>
    <default field="T12" expression="" applyOnUpdate="0"/>
    <default field="T13" expression="" applyOnUpdate="0"/>
    <default field="T14" expression="" applyOnUpdate="0"/>
    <default field="T15" expression="" applyOnUpdate="0"/>
    <default field="T16" expression="" applyOnUpdate="0"/>
    <default field="T17" expression="" applyOnUpdate="0"/>
    <default field="T18" expression="" applyOnUpdate="0"/>
    <default field="T19" expression="" applyOnUpdate="0"/>
    <default field="T20" expression="" applyOnUpdate="0"/>
    <default field="T21" expression="" applyOnUpdate="0"/>
    <default field="T22" expression="" applyOnUpdate="0"/>
    <default field="T23" expression="" applyOnUpdate="0"/>
    <default field="T24" expression="" applyOnUpdate="0"/>
    <default field="T25" expression="" applyOnUpdate="0"/>
    <default field="T26" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="Id" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="Type" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="Time" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T0" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T1" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T2" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T3" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T4" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T5" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T6" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T7" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T8" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T9" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T10" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T11" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T12" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T13" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T14" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T15" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T16" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T17" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T18" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T19" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T20" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T21" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T22" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T23" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T24" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T25" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" notnull_strength="0" field="T26" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="Id" desc=""/>
    <constraint exp="" field="Type" desc=""/>
    <constraint exp="" field="Time" desc=""/>
    <constraint exp="" field="T0" desc=""/>
    <constraint exp="" field="T1" desc=""/>
    <constraint exp="" field="T2" desc=""/>
    <constraint exp="" field="T3" desc=""/>
    <constraint exp="" field="T4" desc=""/>
    <constraint exp="" field="T5" desc=""/>
    <constraint exp="" field="T6" desc=""/>
    <constraint exp="" field="T7" desc=""/>
    <constraint exp="" field="T8" desc=""/>
    <constraint exp="" field="T9" desc=""/>
    <constraint exp="" field="T10" desc=""/>
    <constraint exp="" field="T11" desc=""/>
    <constraint exp="" field="T12" desc=""/>
    <constraint exp="" field="T13" desc=""/>
    <constraint exp="" field="T14" desc=""/>
    <constraint exp="" field="T15" desc=""/>
    <constraint exp="" field="T16" desc=""/>
    <constraint exp="" field="T17" desc=""/>
    <constraint exp="" field="T18" desc=""/>
    <constraint exp="" field="T19" desc=""/>
    <constraint exp="" field="T20" desc=""/>
    <constraint exp="" field="T21" desc=""/>
    <constraint exp="" field="T22" desc=""/>
    <constraint exp="" field="T23" desc=""/>
    <constraint exp="" field="T24" desc=""/>
    <constraint exp="" field="T25" desc=""/>
    <constraint exp="" field="T26" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column type="field" hidden="0" width="-1" name="Id"/>
      <column type="field" hidden="0" width="-1" name="Type"/>
      <column type="field" hidden="0" width="-1" name="Time"/>
      <column type="field" hidden="0" width="-1" name="T0"/>
      <column type="field" hidden="0" width="-1" name="T1"/>
      <column type="field" hidden="0" width="-1" name="T2"/>
      <column type="field" hidden="0" width="-1" name="T3"/>
      <column type="field" hidden="0" width="-1" name="T4"/>
      <column type="field" hidden="0" width="-1" name="T5"/>
      <column type="field" hidden="0" width="-1" name="T6"/>
      <column type="field" hidden="0" width="-1" name="T7"/>
      <column type="field" hidden="0" width="-1" name="T8"/>
      <column type="field" hidden="0" width="-1" name="T9"/>
      <column type="field" hidden="0" width="-1" name="T10"/>
      <column type="field" hidden="0" width="-1" name="T11"/>
      <column type="field" hidden="0" width="-1" name="T12"/>
      <column type="field" hidden="0" width="-1" name="T13"/>
      <column type="field" hidden="0" width="-1" name="T14"/>
      <column type="field" hidden="0" width="-1" name="T15"/>
      <column type="field" hidden="0" width="-1" name="T16"/>
      <column type="field" hidden="0" width="-1" name="T17"/>
      <column type="field" hidden="0" width="-1" name="T18"/>
      <column type="field" hidden="0" width="-1" name="T19"/>
      <column type="field" hidden="0" width="-1" name="T20"/>
      <column type="field" hidden="0" width="-1" name="T21"/>
      <column type="field" hidden="0" width="-1" name="T22"/>
      <column type="field" hidden="0" width="-1" name="T23"/>
      <column type="field" hidden="0" width="-1" name="T24"/>
      <column type="field" hidden="0" width="-1" name="T25"/>
      <column type="field" hidden="0" width="-1" name="T26"/>
      <column type="actions" hidden="1" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <previewExpression>COALESCE( "Id", '&lt;NULL>' )</previewExpression>
  <mapTip enabled="1">Velocity: [% "T0" %]</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
