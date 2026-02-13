<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="0" version="3.40.0-Bratislava" simplifyDrawingTol="1" simplifyMaxScale="1" styleCategories="LayerConfiguration|Symbology|Labeling|Fields|MapTips|AttributeTable|Rendering|CustomProperties|Notes" simplifyAlgorithm="0" minScale="100000000" maxScale="0" simplifyLocal="1" readOnly="0" autoRefreshTime="0" symbologyReferenceScale="-1" hasScaleBasedVisibilityFlag="0" autoRefreshMode="Disabled" simplifyDrawingHints="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <renderer-v2 forceraster="0" type="RuleRenderer" referencescale="-1" symbollevels="0" enableorderby="0">
    <rules key="{f08f9265-f9c8-4415-8702-7f02d66f9e01}">
      <rule label="1-Temp Closed" filter="Time=1" symbol="0" key="{b28287e4-38ca-4d3e-85a5-45df9a70d3ec}"/>
      <rule label="2-Closed" filter="Time=2" symbol="1" key="{0a3caf29-1961-439e-88a0-2e177db20c8c}"/>
      <rule label="5-Closed (H > Hmax)" filter="Time=5" symbol="2" key="{c63f17f5-157c-4ad6-9350-1b8a21749724}"/>
      <rule label="8-Closed (Q &lt; 0)" filter="Time=8" symbol="3" key="{126a8529-02ef-42e3-b5f2-dcb8a9c11639}"/>
      <rule label="9-Closed (P &lt; Pset)" filter="Time=9" symbol="4" key="{ef569774-42b2-4843-bb3c-6291f5b800e0}"/>
      <rule label="11-Closed (P > Pset)" filter="Time=11" symbol="5" key="{3e145831-5734-4772-8322-49503985dda9}"/>
      <rule label="3-Open" filter="Time=3" symbol="6" key="{a0b30374-642e-444b-9f61-50303bc4ff6a}"/>
      <rule label="6-Open (Q > Qmax)" filter="Time=6" symbol="7" key="{9fa0eeab-3d15-49bc-827a-f5bbfd2ceabd}"/>
      <rule label="7-Open (Q &lt; Qset)" filter="Time=7" symbol="8" key="{c0d4b16e-38ff-453e-8373-1d56d9bcef65}"/>
      <rule label="10-Open (P > Pset)" filter="Time=10" symbol="9" key="{45f0ca5f-d032-4f06-8978-4fc40bea5a96}"/>
      <rule label="12-Open (P &lt; Pset)" filter="Time=12" symbol="10" key="{9cfc31c9-814f-40ce-b1ff-1e253eed1d0c}"/>
      <rule label="4-Active" filter="Time=4" symbol="11" key="{545e58c7-f287-4df6-aa46-3792ed01047a}"/>
      <rule label="13-Active (Rev Pump)" filter="Time=13" symbol="12" key="{cebcd8b4-b64a-4428-ad79-60f83184c5a1}"/>
    </rules>
    <symbols>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="0" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,0,0,255,rgb:1,0,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@0@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@0@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@0@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@0@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="1" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,0,0,255,rgb:1,0,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@1@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@1@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@1@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@1@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="10" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,128,0,255,rgb:0,0.50196078431372548,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@10@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@10@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@10@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@10@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="11" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,165,0,255,rgb:1,0.6470588235294118,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@11@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@11@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@11@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@11@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="12" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,165,0,255,rgb:1,0.6470588235294118,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@12@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@12@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@12@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@12@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="2" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,0,0,255,rgb:1,0,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@2@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@2@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="2" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@2@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@2@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="3" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,0,0,255,rgb:1,0,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@3@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@3@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@3@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@3@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="4" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,0,0,255,rgb:1,0,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@4@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@4@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@4@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@4@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="5" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="255,0,0,255,rgb:1,0,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@5@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@5@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@5@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@5@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="6" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,128,0,255,rgb:0,0.50196078431372548,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@6@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@6@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@6@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@6@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="7" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,128,0,255,rgb:0,0.50196078431372548,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@7@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@7@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@7@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@7@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="8" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,128,0,255,rgb:0,0.50196078431372548,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@8@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@8@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@8@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@8@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="9" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{f3d42bf2-8ae6-4890-8fbe-953903b60d5c}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="0,128,0,255,rgb:0,0.50196078431372548,0,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{0722ca74-c4b1-4bd7-99de-1018c80de796}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@9@1" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{472685fd-af8e-4dbf-a0c4-5b109535fc8d}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIj4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGU+PC9kYzp0aXRsZT4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0iICBNIDI4OS42Nzc4NSwxNTUuMDM4ODUgICBDIDIxNS4yNzg0MSwxNTUuMDM4ODUgMTU0LjYzODg1LDIxNS41OTg0IDE1NC42Mzg4NSwyODkuOTk3ODUgICBDIDE1NC42Mzg4NSwzNjQuMzk3MyAyMTUuMjc4NDEsNDI1LjAzNjg1IDI4OS42Nzc4NSw0MjUuMDM2ODUgICBDIDM2NC4wNzczLDQyNS4wMzY4NSA0MjQuNjM2ODUsMzY0LjM5NzMgNDI0LjYzNjg1LDI4OS45OTc4NSAgIEMgNDI0LjYzNjg1LDIxNS41OTg0IDM2NC4wNzczLDE1NS4wMzg4NSAyODkuNjc3ODUsMTU1LjAzODg1ICAgeiAiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4KICA8cGF0aAogICAgIGlkPSJwYXRoNyIKICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+Cjwvc3ZnPgo=" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='PUMP', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{e33492fd-4aef-4087-8602-60686b9c7f45}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@9@2" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{1f253fef-de46-4d86-81d8-2ceec1a2db03}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgaWQ9InN2ZzkiCiAgIGhlaWdodD0iMTU0bW0iCiAgIHdpZHRoPSIxNTRtbSIKICAgdmVyc2lvbj0iMS4wIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ2YWx2ZXMuc3ZnIgogICBpbmtzY2FwZTp2ZXJzaW9uPSIwLjkyLjMgKDI0MDU1NDYsIDIwMTgtMDMtMTEpIj4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iOTYxIgogICAgIGlkPSJuYW1lZHZpZXc4IgogICAgIHNob3dncmlkPSJmYWxzZSIKICAgICBpbmtzY2FwZTp6b29tPSIwLjQwNTQ2NTM3IgogICAgIGlua3NjYXBlOmN4PSIyOTEuMDIzNjIiCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iLTgiCiAgICAgaW5rc2NhcGU6d2luZG93LXk9Ii04IgogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0ic3ZnOSIgLz4KICA8bWV0YWRhdGEKICAgICBpZD0ibWV0YWRhdGExMyI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgICA8ZGM6dGl0bGUgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczMiPgogICAgPHBhdHRlcm4KICAgICAgIHk9IjAiCiAgICAgICB4PSIwIgogICAgICAgaGVpZ2h0PSI2IgogICAgICAgd2lkdGg9IjYiCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIgogICAgICAgaWQ9IkVNRmhiYXNlcGF0dGVybiIgLz4KICA8L2RlZnM+CiAgPHBhdGgKICAgICBpZD0icGF0aDUiCiAgICAgZD0ibSAxMTUuNjMyNDYsMTc2LjQwMDMxIGMgLTYuMDI2MTMsMC4wNzQ0IC0xMS40NTcwOSw0LjkxMDE4IC0xMS41MzE0OSwxMS42MDU4OCBsIC0wLjU5NTE3LDEwMS4zMjgzNiAtMC41OTUxOCwxMDEuNDAyNzUgYyAwLDguOTI3NjEgOS42NzE1OCwxNC41ODE3NiAxNy40MDg4MywxMC4xMTc5NiBsIDg4LjA4NTc0LC01MC4xNDM0IDgyLjIwODQsLTQ2Ljg2OTk1IDgxLjMxNTYzLDQ4LjM1Nzg5IDg3LjExODU3LDUxLjc4MDEyIGMgNy42NjI4Niw0LjYxMjYgMTcuNDA4ODQsLTAuODkyNzYgMTcuNTU3NjMsLTkuODIwMzcgbCAxLjI2NDc0LC0xMDEuMzI4MzUgMS4yNjQ3NSwtMTAxLjQwMjc1IGMgMC4xNDg3OSwtOC45Mjc2MSAtOS40NDgzOCwtMTQuNjU2MTYgLTE3LjI2MDA0LC0xMC4yNjY3NSBsIC04OC40NTc3Miw0OS41NDgyMiAtODIuNTgwMzgsNDYuMzQ5MTcgLTgxLjc2MjAxLC00Ny44MzcxMSAtODcuNDkwNTYsLTUxLjE4NDk1IGMgLTEuOTM0MzEsLTEuMTE1OTUgLTMuOTQzMDMsLTEuNjM2NzIgLTUuOTUxNzQsLTEuNjM2NzIgeiBtIDM0MC4wNjc0OCwzNC44OTIwNyAtMS4wNDE1NSw4MS4yNDEyMyAtMS4wNDE1Niw4MS4xNjY4MyAtNjkuODU4NTQsLTQxLjQzODk4IC02OS43ODQxMywtNDEuNTEzMzggNzAuODI1NywtMzkuNzI3ODUgeiIKICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIgogICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSIKICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiCiAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIgogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+CiAgPHBhdGgKICAgICBpZD0icGF0aDciCiAgICAgZD0ibSAzMTEuNTE5MDcsMjkxLjcxNTI1IDcyLjAxNjA0LDQyLjc3ODEyIDcyLjAxNjA0LDQyLjg1MjUxIDEuMTE1OTUsLTgzLjg0NTEyIC0wLjk2NzE2LC04Mi4yMDgzOCBjIC0yNC4zODExNiwxMy42NTczNiAtNDYuNzQ2NTcsMjUuNzY0OTUgLTcxLjEyMzI4LDM5LjQzMDI2IHoiCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSIKICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIiAvPgo8L3N2Zz4K" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="if(&quot;Type&quot;='VALVE', 6, 0)" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{96ffda55-4f91-442d-98fd-0435dc9ca90c}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@9@3" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{65ef37d9-5e1e-4cd9-a344-5379019efde5}" locked="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
        <layer enabled="1" pass="0" class="MarkerLine" id="{4a91994b-393f-4153-9905-ffe77fdb56c2}" locked="0">
          <Option type="Map">
            <Option value="4" type="QString" name="average_angle_length"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="average_angle_map_unit_scale"/>
            <Option value="MM" type="QString" name="average_angle_unit"/>
            <Option value="3" type="QString" name="interval"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="interval_map_unit_scale"/>
            <Option value="MM" type="QString" name="interval_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="0" type="QString" name="offset_along_line"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_along_line_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_along_line_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="true" type="bool" name="place_on_every_part"/>
            <Option value="CentralPoint" type="QString" name="placements"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="1" type="QString" name="rotate"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol frame_rate="10" force_rhr="0" type="marker" alpha="1" name="@9@4" is_animated="0" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" pass="0" class="SvgMarker" id="{dce8434b-a6ca-4b0f-9671-08e468e3bc0b}" locked="0">
              <Option type="Map">
                <Option value="180" type="QString" name="angle"/>
                <Option value="0,0,0,255,rgb:0,0,0,1" type="QString" name="color"/>
                <Option value="0" type="QString" name="fixedAspectRatio"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgaWQ9InN2ZzciCiAgIGhlaWdodD0iMTVtbSIKICAgd2lkdGg9IjE1bW0iCiAgIHZlcnNpb249IjEuMCI+CiAgPG1ldGFkYXRhCiAgICAgaWQ9Im1ldGFkYXRhMTEiPgogICAgPHJkZjpSREY+CiAgICAgIDxjYzpXb3JrCiAgICAgICAgIHJkZjphYm91dD0iIj4KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4KICAgICAgICA8ZGM6dHlwZQogICAgICAgICAgIHJkZjpyZXNvdXJjZT0iaHR0cDovL3B1cmwub3JnL2RjL2RjbWl0eXBlL1N0aWxsSW1hZ2UiIC8+CiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+CiAgICAgIDwvY2M6V29yaz4KICAgIDwvcmRmOlJERj4KICA8L21ldGFkYXRhPgogIDxkZWZzCiAgICAgaWQ9ImRlZnMzIj4KICAgIDxwYXR0ZXJuCiAgICAgICB5PSIwIgogICAgICAgeD0iMCIKICAgICAgIGhlaWdodD0iNiIKICAgICAgIHdpZHRoPSI2IgogICAgICAgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIKICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+CiAgPC9kZWZzPgogIDxwYXRoCiAgICAgaWQ9InBhdGg1IgogICAgIGQ9IiAgTSA1My41OTk2MDMsMjYuNDc5ODA0ICAgQyA1My41OTk2MDMsMjYuMDc5ODA3IDUzLjM1OTYwNSwyNS42Nzk4MSA1Mi45NTk2MDgsMjUuNTE5ODExICAgTCAxLjkxOTk4NTgsNy45MTk5NDEzICAgQyAxLjUxOTk4ODcsNy43NTk5NDI1IDEuMDM5OTkyMyw3LjkxOTk0MTMgMC43OTk5OTQwNyw4LjIzOTkzOSAgIEMgMC41NTk5OTU4NSw4LjYzOTkzNiAwLjQ3OTk5NjQ0LDkuMTE5OTMyNCAwLjc5OTk5NDA3LDkuNDM5OTMwMSAgIEwgMTMuNzU5ODk4LDI3LjUxOTc5NiAgIEwgMC41NTk5OTU4NSw0NC41NTk2NyAgIEMgMC4zMTk5OTc2Myw0NC44Nzk2NjggMC4zMTk5OTc2Myw0NS4zNTk2NjQgMC41NTk5OTU4NSw0NS43NTk2NjEgICBDIDAuNTU5OTk1ODUsNDUuNzU5NjYxIDAuNjM5OTk1MjYsNDUuODM5NjYgMC42Mzk5OTUyNiw0NS44Mzk2NiAgIEMgMC45NTk5OTI4OSw0Ni4xNTk2NTggMS4zNTk5ODk5LDQ2LjIzOTY1NyAxLjY3OTk4NzYsNDYuMDc5NjU5ICAgTCA1Mi45NTk2MDgsMjcuNDM5Nzk3ICAgQyA1My4zNTk2MDUsMjcuMjc5Nzk4IDUzLjU5OTYwMywyNi44Nzk4MDEgNTMuNTk5NjAzLDI2LjQ3OTgwNCAgIHogIgogICAgIGZpbGw9InBhcmFtKGZpbGwpICMwMDAiCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIgogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiIKICAgICBzdHJva2Utb3BhY2l0eT0icGFyYW0ob3V0bGluZS1vcGFjaXR5KSIKICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4KPC9zdmc+Cg==" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="outline_color"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="0" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option type="Map" name="properties">
                    <Option type="Map" name="size">
                      <Option value="true" type="bool" name="active"/>
                      <Option value="0" type="QString" name="expression"/>
                      <Option value="3" type="int" name="type"/>
                    </Option>
                  </Option>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
    <data-defined-properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol frame_rate="10" force_rhr="0" type="line" alpha="1" name="" is_animated="0" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" class="SimpleLine" id="{b724eaf4-c9da-4b1e-9990-8dcb29332165}" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <customproperties>
    <Option type="Map">
      <Option value="0" type="int" name="embeddedWidgets/count"/>
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
    <field name="T27" configurationFlags="NoFlag"/>
    <field name="T28" configurationFlags="NoFlag"/>
    <field name="T29" configurationFlags="NoFlag"/>
    <field name="T30" configurationFlags="NoFlag"/>
    <field name="T31" configurationFlags="NoFlag"/>
    <field name="T32" configurationFlags="NoFlag"/>
    <field name="T33" configurationFlags="NoFlag"/>
    <field name="T34" configurationFlags="NoFlag"/>
    <field name="T35" configurationFlags="NoFlag"/>
    <field name="T36" configurationFlags="NoFlag"/>
    <field name="T37" configurationFlags="NoFlag"/>
    <field name="T38" configurationFlags="NoFlag"/>
    <field name="T39" configurationFlags="NoFlag"/>
    <field name="T40" configurationFlags="NoFlag"/>
    <field name="T41" configurationFlags="NoFlag"/>
    <field name="T42" configurationFlags="NoFlag"/>
    <field name="T43" configurationFlags="NoFlag"/>
    <field name="T44" configurationFlags="NoFlag"/>
    <field name="T45" configurationFlags="NoFlag"/>
    <field name="T46" configurationFlags="NoFlag"/>
    <field name="T47" configurationFlags="NoFlag"/>
    <field name="T48" configurationFlags="NoFlag"/>
    <field name="T49" configurationFlags="NoFlag"/>
    <field name="T50" configurationFlags="NoFlag"/>
    <field name="T51" configurationFlags="NoFlag"/>
    <field name="T52" configurationFlags="NoFlag"/>
    <field name="T53" configurationFlags="NoFlag"/>
    <field name="T54" configurationFlags="NoFlag"/>
    <field name="T55" configurationFlags="NoFlag"/>
    <field name="T56" configurationFlags="NoFlag"/>
    <field name="T57" configurationFlags="NoFlag"/>
    <field name="T58" configurationFlags="NoFlag"/>
    <field name="T59" configurationFlags="NoFlag"/>
    <field name="T60" configurationFlags="NoFlag"/>
    <field name="T61" configurationFlags="NoFlag"/>
    <field name="T62" configurationFlags="NoFlag"/>
    <field name="T63" configurationFlags="NoFlag"/>
    <field name="T64" configurationFlags="NoFlag"/>
    <field name="T65" configurationFlags="NoFlag"/>
    <field name="T66" configurationFlags="NoFlag"/>
    <field name="T67" configurationFlags="NoFlag"/>
    <field name="T68" configurationFlags="NoFlag"/>
    <field name="T69" configurationFlags="NoFlag"/>
    <field name="T70" configurationFlags="NoFlag"/>
    <field name="T71" configurationFlags="NoFlag"/>
    <field name="T72" configurationFlags="NoFlag"/>
    <field name="T73" configurationFlags="NoFlag"/>
    <field name="T74" configurationFlags="NoFlag"/>
    <field name="T75" configurationFlags="NoFlag"/>
    <field name="T76" configurationFlags="NoFlag"/>
    <field name="T77" configurationFlags="NoFlag"/>
    <field name="T78" configurationFlags="NoFlag"/>
    <field name="T79" configurationFlags="NoFlag"/>
    <field name="T80" configurationFlags="NoFlag"/>
    <field name="T81" configurationFlags="NoFlag"/>
    <field name="T82" configurationFlags="NoFlag"/>
    <field name="T83" configurationFlags="NoFlag"/>
    <field name="T84" configurationFlags="NoFlag"/>
    <field name="T85" configurationFlags="NoFlag"/>
    <field name="T86" configurationFlags="NoFlag"/>
    <field name="T87" configurationFlags="NoFlag"/>
    <field name="T88" configurationFlags="NoFlag"/>
    <field name="T89" configurationFlags="NoFlag"/>
    <field name="T90" configurationFlags="NoFlag"/>
    <field name="T91" configurationFlags="NoFlag"/>
    <field name="T92" configurationFlags="NoFlag"/>
    <field name="T93" configurationFlags="NoFlag"/>
    <field name="T94" configurationFlags="NoFlag"/>
    <field name="T95" configurationFlags="NoFlag"/>
    <field name="T96" configurationFlags="NoFlag"/>
    <field name="T97" configurationFlags="NoFlag"/>
    <field name="T98" configurationFlags="NoFlag"/>
    <field name="T99" configurationFlags="NoFlag"/>
    <field name="T100" configurationFlags="NoFlag"/>
    <field name="T101" configurationFlags="NoFlag"/>
    <field name="T102" configurationFlags="NoFlag"/>
    <field name="T103" configurationFlags="NoFlag"/>
    <field name="T104" configurationFlags="NoFlag"/>
    <field name="T105" configurationFlags="NoFlag"/>
    <field name="T106" configurationFlags="NoFlag"/>
    <field name="T107" configurationFlags="NoFlag"/>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="Id"/>
    <alias index="1" name="" field="Type"/>
    <alias index="2" name="" field="Time"/>
    <alias index="3" name="" field="T0"/>
    <alias index="4" name="" field="T1"/>
    <alias index="5" name="" field="T2"/>
    <alias index="6" name="" field="T3"/>
    <alias index="7" name="" field="T4"/>
    <alias index="8" name="" field="T5"/>
    <alias index="9" name="" field="T6"/>
    <alias index="10" name="" field="T7"/>
    <alias index="11" name="" field="T8"/>
    <alias index="12" name="" field="T9"/>
    <alias index="13" name="" field="T10"/>
    <alias index="14" name="" field="T11"/>
    <alias index="15" name="" field="T12"/>
    <alias index="16" name="" field="T13"/>
    <alias index="17" name="" field="T14"/>
    <alias index="18" name="" field="T15"/>
    <alias index="19" name="" field="T16"/>
    <alias index="20" name="" field="T17"/>
    <alias index="21" name="" field="T18"/>
    <alias index="22" name="" field="T19"/>
    <alias index="23" name="" field="T20"/>
    <alias index="24" name="" field="T21"/>
    <alias index="25" name="" field="T22"/>
    <alias index="26" name="" field="T23"/>
    <alias index="27" name="" field="T24"/>
    <alias index="28" name="" field="T25"/>
    <alias index="29" name="" field="T26"/>
    <alias index="30" name="" field="T27"/>
    <alias index="31" name="" field="T28"/>
    <alias index="32" name="" field="T29"/>
    <alias index="33" name="" field="T30"/>
    <alias index="34" name="" field="T31"/>
    <alias index="35" name="" field="T32"/>
    <alias index="36" name="" field="T33"/>
    <alias index="37" name="" field="T34"/>
    <alias index="38" name="" field="T35"/>
    <alias index="39" name="" field="T36"/>
    <alias index="40" name="" field="T37"/>
    <alias index="41" name="" field="T38"/>
    <alias index="42" name="" field="T39"/>
    <alias index="43" name="" field="T40"/>
    <alias index="44" name="" field="T41"/>
    <alias index="45" name="" field="T42"/>
    <alias index="46" name="" field="T43"/>
    <alias index="47" name="" field="T44"/>
    <alias index="48" name="" field="T45"/>
    <alias index="49" name="" field="T46"/>
    <alias index="50" name="" field="T47"/>
    <alias index="51" name="" field="T48"/>
    <alias index="52" name="" field="T49"/>
    <alias index="53" name="" field="T50"/>
    <alias index="54" name="" field="T51"/>
    <alias index="55" name="" field="T52"/>
    <alias index="56" name="" field="T53"/>
    <alias index="57" name="" field="T54"/>
    <alias index="58" name="" field="T55"/>
    <alias index="59" name="" field="T56"/>
    <alias index="60" name="" field="T57"/>
    <alias index="61" name="" field="T58"/>
    <alias index="62" name="" field="T59"/>
    <alias index="63" name="" field="T60"/>
    <alias index="64" name="" field="T61"/>
    <alias index="65" name="" field="T62"/>
    <alias index="66" name="" field="T63"/>
    <alias index="67" name="" field="T64"/>
    <alias index="68" name="" field="T65"/>
    <alias index="69" name="" field="T66"/>
    <alias index="70" name="" field="T67"/>
    <alias index="71" name="" field="T68"/>
    <alias index="72" name="" field="T69"/>
    <alias index="73" name="" field="T70"/>
    <alias index="74" name="" field="T71"/>
    <alias index="75" name="" field="T72"/>
    <alias index="76" name="" field="T73"/>
    <alias index="77" name="" field="T74"/>
    <alias index="78" name="" field="T75"/>
    <alias index="79" name="" field="T76"/>
    <alias index="80" name="" field="T77"/>
    <alias index="81" name="" field="T78"/>
    <alias index="82" name="" field="T79"/>
    <alias index="83" name="" field="T80"/>
    <alias index="84" name="" field="T81"/>
    <alias index="85" name="" field="T82"/>
    <alias index="86" name="" field="T83"/>
    <alias index="87" name="" field="T84"/>
    <alias index="88" name="" field="T85"/>
    <alias index="89" name="" field="T86"/>
    <alias index="90" name="" field="T87"/>
    <alias index="91" name="" field="T88"/>
    <alias index="92" name="" field="T89"/>
    <alias index="93" name="" field="T90"/>
    <alias index="94" name="" field="T91"/>
    <alias index="95" name="" field="T92"/>
    <alias index="96" name="" field="T93"/>
    <alias index="97" name="" field="T94"/>
    <alias index="98" name="" field="T95"/>
    <alias index="99" name="" field="T96"/>
    <alias index="100" name="" field="T97"/>
    <alias index="101" name="" field="T98"/>
    <alias index="102" name="" field="T99"/>
    <alias index="103" name="" field="T100"/>
    <alias index="104" name="" field="T101"/>
    <alias index="105" name="" field="T102"/>
    <alias index="106" name="" field="T103"/>
    <alias index="107" name="" field="T104"/>
    <alias index="108" name="" field="T105"/>
    <alias index="109" name="" field="T106"/>
    <alias index="110" name="" field="T107"/>
  </aliases>
  <splitPolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="Type" policy="Duplicate"/>
    <policy field="Time" policy="Duplicate"/>
    <policy field="T0" policy="Duplicate"/>
    <policy field="T1" policy="Duplicate"/>
    <policy field="T2" policy="Duplicate"/>
    <policy field="T3" policy="Duplicate"/>
    <policy field="T4" policy="Duplicate"/>
    <policy field="T5" policy="Duplicate"/>
    <policy field="T6" policy="Duplicate"/>
    <policy field="T7" policy="Duplicate"/>
    <policy field="T8" policy="Duplicate"/>
    <policy field="T9" policy="Duplicate"/>
    <policy field="T10" policy="Duplicate"/>
    <policy field="T11" policy="Duplicate"/>
    <policy field="T12" policy="Duplicate"/>
    <policy field="T13" policy="Duplicate"/>
    <policy field="T14" policy="Duplicate"/>
    <policy field="T15" policy="Duplicate"/>
    <policy field="T16" policy="Duplicate"/>
    <policy field="T17" policy="Duplicate"/>
    <policy field="T18" policy="Duplicate"/>
    <policy field="T19" policy="Duplicate"/>
    <policy field="T20" policy="Duplicate"/>
    <policy field="T21" policy="Duplicate"/>
    <policy field="T22" policy="Duplicate"/>
    <policy field="T23" policy="Duplicate"/>
    <policy field="T24" policy="Duplicate"/>
    <policy field="T25" policy="Duplicate"/>
    <policy field="T26" policy="Duplicate"/>
    <policy field="T27" policy="Duplicate"/>
    <policy field="T28" policy="Duplicate"/>
    <policy field="T29" policy="Duplicate"/>
    <policy field="T30" policy="Duplicate"/>
    <policy field="T31" policy="Duplicate"/>
    <policy field="T32" policy="Duplicate"/>
    <policy field="T33" policy="Duplicate"/>
    <policy field="T34" policy="Duplicate"/>
    <policy field="T35" policy="Duplicate"/>
    <policy field="T36" policy="Duplicate"/>
    <policy field="T37" policy="Duplicate"/>
    <policy field="T38" policy="Duplicate"/>
    <policy field="T39" policy="Duplicate"/>
    <policy field="T40" policy="Duplicate"/>
    <policy field="T41" policy="Duplicate"/>
    <policy field="T42" policy="Duplicate"/>
    <policy field="T43" policy="Duplicate"/>
    <policy field="T44" policy="Duplicate"/>
    <policy field="T45" policy="Duplicate"/>
    <policy field="T46" policy="Duplicate"/>
    <policy field="T47" policy="Duplicate"/>
    <policy field="T48" policy="Duplicate"/>
    <policy field="T49" policy="Duplicate"/>
    <policy field="T50" policy="Duplicate"/>
    <policy field="T51" policy="Duplicate"/>
    <policy field="T52" policy="Duplicate"/>
    <policy field="T53" policy="Duplicate"/>
    <policy field="T54" policy="Duplicate"/>
    <policy field="T55" policy="Duplicate"/>
    <policy field="T56" policy="Duplicate"/>
    <policy field="T57" policy="Duplicate"/>
    <policy field="T58" policy="Duplicate"/>
    <policy field="T59" policy="Duplicate"/>
    <policy field="T60" policy="Duplicate"/>
    <policy field="T61" policy="Duplicate"/>
    <policy field="T62" policy="Duplicate"/>
    <policy field="T63" policy="Duplicate"/>
    <policy field="T64" policy="Duplicate"/>
    <policy field="T65" policy="Duplicate"/>
    <policy field="T66" policy="Duplicate"/>
    <policy field="T67" policy="Duplicate"/>
    <policy field="T68" policy="Duplicate"/>
    <policy field="T69" policy="Duplicate"/>
    <policy field="T70" policy="Duplicate"/>
    <policy field="T71" policy="Duplicate"/>
    <policy field="T72" policy="Duplicate"/>
    <policy field="T73" policy="Duplicate"/>
    <policy field="T74" policy="Duplicate"/>
    <policy field="T75" policy="Duplicate"/>
    <policy field="T76" policy="Duplicate"/>
    <policy field="T77" policy="Duplicate"/>
    <policy field="T78" policy="Duplicate"/>
    <policy field="T79" policy="Duplicate"/>
    <policy field="T80" policy="Duplicate"/>
    <policy field="T81" policy="Duplicate"/>
    <policy field="T82" policy="Duplicate"/>
    <policy field="T83" policy="Duplicate"/>
    <policy field="T84" policy="Duplicate"/>
    <policy field="T85" policy="Duplicate"/>
    <policy field="T86" policy="Duplicate"/>
    <policy field="T87" policy="Duplicate"/>
    <policy field="T88" policy="Duplicate"/>
    <policy field="T89" policy="Duplicate"/>
    <policy field="T90" policy="Duplicate"/>
    <policy field="T91" policy="Duplicate"/>
    <policy field="T92" policy="Duplicate"/>
    <policy field="T93" policy="Duplicate"/>
    <policy field="T94" policy="Duplicate"/>
    <policy field="T95" policy="Duplicate"/>
    <policy field="T96" policy="Duplicate"/>
    <policy field="T97" policy="Duplicate"/>
    <policy field="T98" policy="Duplicate"/>
    <policy field="T99" policy="Duplicate"/>
    <policy field="T100" policy="Duplicate"/>
    <policy field="T101" policy="Duplicate"/>
    <policy field="T102" policy="Duplicate"/>
    <policy field="T103" policy="Duplicate"/>
    <policy field="T104" policy="Duplicate"/>
    <policy field="T105" policy="Duplicate"/>
    <policy field="T106" policy="Duplicate"/>
    <policy field="T107" policy="Duplicate"/>
  </splitPolicies>
  <duplicatePolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="Type" policy="Duplicate"/>
    <policy field="Time" policy="Duplicate"/>
    <policy field="T0" policy="Duplicate"/>
    <policy field="T1" policy="Duplicate"/>
    <policy field="T2" policy="Duplicate"/>
    <policy field="T3" policy="Duplicate"/>
    <policy field="T4" policy="Duplicate"/>
    <policy field="T5" policy="Duplicate"/>
    <policy field="T6" policy="Duplicate"/>
    <policy field="T7" policy="Duplicate"/>
    <policy field="T8" policy="Duplicate"/>
    <policy field="T9" policy="Duplicate"/>
    <policy field="T10" policy="Duplicate"/>
    <policy field="T11" policy="Duplicate"/>
    <policy field="T12" policy="Duplicate"/>
    <policy field="T13" policy="Duplicate"/>
    <policy field="T14" policy="Duplicate"/>
    <policy field="T15" policy="Duplicate"/>
    <policy field="T16" policy="Duplicate"/>
    <policy field="T17" policy="Duplicate"/>
    <policy field="T18" policy="Duplicate"/>
    <policy field="T19" policy="Duplicate"/>
    <policy field="T20" policy="Duplicate"/>
    <policy field="T21" policy="Duplicate"/>
    <policy field="T22" policy="Duplicate"/>
    <policy field="T23" policy="Duplicate"/>
    <policy field="T24" policy="Duplicate"/>
    <policy field="T25" policy="Duplicate"/>
    <policy field="T26" policy="Duplicate"/>
    <policy field="T27" policy="Duplicate"/>
    <policy field="T28" policy="Duplicate"/>
    <policy field="T29" policy="Duplicate"/>
    <policy field="T30" policy="Duplicate"/>
    <policy field="T31" policy="Duplicate"/>
    <policy field="T32" policy="Duplicate"/>
    <policy field="T33" policy="Duplicate"/>
    <policy field="T34" policy="Duplicate"/>
    <policy field="T35" policy="Duplicate"/>
    <policy field="T36" policy="Duplicate"/>
    <policy field="T37" policy="Duplicate"/>
    <policy field="T38" policy="Duplicate"/>
    <policy field="T39" policy="Duplicate"/>
    <policy field="T40" policy="Duplicate"/>
    <policy field="T41" policy="Duplicate"/>
    <policy field="T42" policy="Duplicate"/>
    <policy field="T43" policy="Duplicate"/>
    <policy field="T44" policy="Duplicate"/>
    <policy field="T45" policy="Duplicate"/>
    <policy field="T46" policy="Duplicate"/>
    <policy field="T47" policy="Duplicate"/>
    <policy field="T48" policy="Duplicate"/>
    <policy field="T49" policy="Duplicate"/>
    <policy field="T50" policy="Duplicate"/>
    <policy field="T51" policy="Duplicate"/>
    <policy field="T52" policy="Duplicate"/>
    <policy field="T53" policy="Duplicate"/>
    <policy field="T54" policy="Duplicate"/>
    <policy field="T55" policy="Duplicate"/>
    <policy field="T56" policy="Duplicate"/>
    <policy field="T57" policy="Duplicate"/>
    <policy field="T58" policy="Duplicate"/>
    <policy field="T59" policy="Duplicate"/>
    <policy field="T60" policy="Duplicate"/>
    <policy field="T61" policy="Duplicate"/>
    <policy field="T62" policy="Duplicate"/>
    <policy field="T63" policy="Duplicate"/>
    <policy field="T64" policy="Duplicate"/>
    <policy field="T65" policy="Duplicate"/>
    <policy field="T66" policy="Duplicate"/>
    <policy field="T67" policy="Duplicate"/>
    <policy field="T68" policy="Duplicate"/>
    <policy field="T69" policy="Duplicate"/>
    <policy field="T70" policy="Duplicate"/>
    <policy field="T71" policy="Duplicate"/>
    <policy field="T72" policy="Duplicate"/>
    <policy field="T73" policy="Duplicate"/>
    <policy field="T74" policy="Duplicate"/>
    <policy field="T75" policy="Duplicate"/>
    <policy field="T76" policy="Duplicate"/>
    <policy field="T77" policy="Duplicate"/>
    <policy field="T78" policy="Duplicate"/>
    <policy field="T79" policy="Duplicate"/>
    <policy field="T80" policy="Duplicate"/>
    <policy field="T81" policy="Duplicate"/>
    <policy field="T82" policy="Duplicate"/>
    <policy field="T83" policy="Duplicate"/>
    <policy field="T84" policy="Duplicate"/>
    <policy field="T85" policy="Duplicate"/>
    <policy field="T86" policy="Duplicate"/>
    <policy field="T87" policy="Duplicate"/>
    <policy field="T88" policy="Duplicate"/>
    <policy field="T89" policy="Duplicate"/>
    <policy field="T90" policy="Duplicate"/>
    <policy field="T91" policy="Duplicate"/>
    <policy field="T92" policy="Duplicate"/>
    <policy field="T93" policy="Duplicate"/>
    <policy field="T94" policy="Duplicate"/>
    <policy field="T95" policy="Duplicate"/>
    <policy field="T96" policy="Duplicate"/>
    <policy field="T97" policy="Duplicate"/>
    <policy field="T98" policy="Duplicate"/>
    <policy field="T99" policy="Duplicate"/>
    <policy field="T100" policy="Duplicate"/>
    <policy field="T101" policy="Duplicate"/>
    <policy field="T102" policy="Duplicate"/>
    <policy field="T103" policy="Duplicate"/>
    <policy field="T104" policy="Duplicate"/>
    <policy field="T105" policy="Duplicate"/>
    <policy field="T106" policy="Duplicate"/>
    <policy field="T107" policy="Duplicate"/>
  </duplicatePolicies>
  <defaults>
    <default field="Id" applyOnUpdate="0" expression=""/>
    <default field="Type" applyOnUpdate="0" expression=""/>
    <default field="Time" applyOnUpdate="0" expression=""/>
    <default field="T0" applyOnUpdate="0" expression=""/>
    <default field="T1" applyOnUpdate="0" expression=""/>
    <default field="T2" applyOnUpdate="0" expression=""/>
    <default field="T3" applyOnUpdate="0" expression=""/>
    <default field="T4" applyOnUpdate="0" expression=""/>
    <default field="T5" applyOnUpdate="0" expression=""/>
    <default field="T6" applyOnUpdate="0" expression=""/>
    <default field="T7" applyOnUpdate="0" expression=""/>
    <default field="T8" applyOnUpdate="0" expression=""/>
    <default field="T9" applyOnUpdate="0" expression=""/>
    <default field="T10" applyOnUpdate="0" expression=""/>
    <default field="T11" applyOnUpdate="0" expression=""/>
    <default field="T12" applyOnUpdate="0" expression=""/>
    <default field="T13" applyOnUpdate="0" expression=""/>
    <default field="T14" applyOnUpdate="0" expression=""/>
    <default field="T15" applyOnUpdate="0" expression=""/>
    <default field="T16" applyOnUpdate="0" expression=""/>
    <default field="T17" applyOnUpdate="0" expression=""/>
    <default field="T18" applyOnUpdate="0" expression=""/>
    <default field="T19" applyOnUpdate="0" expression=""/>
    <default field="T20" applyOnUpdate="0" expression=""/>
    <default field="T21" applyOnUpdate="0" expression=""/>
    <default field="T22" applyOnUpdate="0" expression=""/>
    <default field="T23" applyOnUpdate="0" expression=""/>
    <default field="T24" applyOnUpdate="0" expression=""/>
    <default field="T25" applyOnUpdate="0" expression=""/>
    <default field="T26" applyOnUpdate="0" expression=""/>
    <default field="T27" applyOnUpdate="0" expression=""/>
    <default field="T28" applyOnUpdate="0" expression=""/>
    <default field="T29" applyOnUpdate="0" expression=""/>
    <default field="T30" applyOnUpdate="0" expression=""/>
    <default field="T31" applyOnUpdate="0" expression=""/>
    <default field="T32" applyOnUpdate="0" expression=""/>
    <default field="T33" applyOnUpdate="0" expression=""/>
    <default field="T34" applyOnUpdate="0" expression=""/>
    <default field="T35" applyOnUpdate="0" expression=""/>
    <default field="T36" applyOnUpdate="0" expression=""/>
    <default field="T37" applyOnUpdate="0" expression=""/>
    <default field="T38" applyOnUpdate="0" expression=""/>
    <default field="T39" applyOnUpdate="0" expression=""/>
    <default field="T40" applyOnUpdate="0" expression=""/>
    <default field="T41" applyOnUpdate="0" expression=""/>
    <default field="T42" applyOnUpdate="0" expression=""/>
    <default field="T43" applyOnUpdate="0" expression=""/>
    <default field="T44" applyOnUpdate="0" expression=""/>
    <default field="T45" applyOnUpdate="0" expression=""/>
    <default field="T46" applyOnUpdate="0" expression=""/>
    <default field="T47" applyOnUpdate="0" expression=""/>
    <default field="T48" applyOnUpdate="0" expression=""/>
    <default field="T49" applyOnUpdate="0" expression=""/>
    <default field="T50" applyOnUpdate="0" expression=""/>
    <default field="T51" applyOnUpdate="0" expression=""/>
    <default field="T52" applyOnUpdate="0" expression=""/>
    <default field="T53" applyOnUpdate="0" expression=""/>
    <default field="T54" applyOnUpdate="0" expression=""/>
    <default field="T55" applyOnUpdate="0" expression=""/>
    <default field="T56" applyOnUpdate="0" expression=""/>
    <default field="T57" applyOnUpdate="0" expression=""/>
    <default field="T58" applyOnUpdate="0" expression=""/>
    <default field="T59" applyOnUpdate="0" expression=""/>
    <default field="T60" applyOnUpdate="0" expression=""/>
    <default field="T61" applyOnUpdate="0" expression=""/>
    <default field="T62" applyOnUpdate="0" expression=""/>
    <default field="T63" applyOnUpdate="0" expression=""/>
    <default field="T64" applyOnUpdate="0" expression=""/>
    <default field="T65" applyOnUpdate="0" expression=""/>
    <default field="T66" applyOnUpdate="0" expression=""/>
    <default field="T67" applyOnUpdate="0" expression=""/>
    <default field="T68" applyOnUpdate="0" expression=""/>
    <default field="T69" applyOnUpdate="0" expression=""/>
    <default field="T70" applyOnUpdate="0" expression=""/>
    <default field="T71" applyOnUpdate="0" expression=""/>
    <default field="T72" applyOnUpdate="0" expression=""/>
    <default field="T73" applyOnUpdate="0" expression=""/>
    <default field="T74" applyOnUpdate="0" expression=""/>
    <default field="T75" applyOnUpdate="0" expression=""/>
    <default field="T76" applyOnUpdate="0" expression=""/>
    <default field="T77" applyOnUpdate="0" expression=""/>
    <default field="T78" applyOnUpdate="0" expression=""/>
    <default field="T79" applyOnUpdate="0" expression=""/>
    <default field="T80" applyOnUpdate="0" expression=""/>
    <default field="T81" applyOnUpdate="0" expression=""/>
    <default field="T82" applyOnUpdate="0" expression=""/>
    <default field="T83" applyOnUpdate="0" expression=""/>
    <default field="T84" applyOnUpdate="0" expression=""/>
    <default field="T85" applyOnUpdate="0" expression=""/>
    <default field="T86" applyOnUpdate="0" expression=""/>
    <default field="T87" applyOnUpdate="0" expression=""/>
    <default field="T88" applyOnUpdate="0" expression=""/>
    <default field="T89" applyOnUpdate="0" expression=""/>
    <default field="T90" applyOnUpdate="0" expression=""/>
    <default field="T91" applyOnUpdate="0" expression=""/>
    <default field="T92" applyOnUpdate="0" expression=""/>
    <default field="T93" applyOnUpdate="0" expression=""/>
    <default field="T94" applyOnUpdate="0" expression=""/>
    <default field="T95" applyOnUpdate="0" expression=""/>
    <default field="T96" applyOnUpdate="0" expression=""/>
    <default field="T97" applyOnUpdate="0" expression=""/>
    <default field="T98" applyOnUpdate="0" expression=""/>
    <default field="T99" applyOnUpdate="0" expression=""/>
    <default field="T100" applyOnUpdate="0" expression=""/>
    <default field="T101" applyOnUpdate="0" expression=""/>
    <default field="T102" applyOnUpdate="0" expression=""/>
    <default field="T103" applyOnUpdate="0" expression=""/>
    <default field="T104" applyOnUpdate="0" expression=""/>
    <default field="T105" applyOnUpdate="0" expression=""/>
    <default field="T106" applyOnUpdate="0" expression=""/>
    <default field="T107" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="Id" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="Type" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="Time" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T0" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T1" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T2" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T3" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T4" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T5" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T6" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T7" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T8" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T9" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T10" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T11" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T12" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T13" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T14" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T15" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T16" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T17" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T18" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T19" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T20" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T21" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T22" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T23" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T24" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T25" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T26" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T27" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T28" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T29" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T30" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T31" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T32" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T33" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T34" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T35" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T36" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T37" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T38" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T39" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T40" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T41" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T42" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T43" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T44" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T45" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T46" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T47" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T48" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T49" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T50" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T51" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T52" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T53" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T54" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T55" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T56" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T57" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T58" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T59" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T60" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T61" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T62" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T63" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T64" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T65" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T66" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T67" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T68" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T69" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T70" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T71" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T72" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T73" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T74" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T75" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T76" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T77" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T78" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T79" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T80" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T81" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T82" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T83" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T84" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T85" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T86" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T87" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T88" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T89" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T90" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T91" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T92" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T93" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T94" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T95" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T96" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T97" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T98" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T99" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T100" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T101" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T102" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T103" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T104" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T105" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T106" constraints="0"/>
    <constraint unique_strength="0" exp_strength="0" notnull_strength="0" field="T107" constraints="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="Id"/>
    <constraint desc="" exp="" field="Type"/>
    <constraint desc="" exp="" field="Time"/>
    <constraint desc="" exp="" field="T0"/>
    <constraint desc="" exp="" field="T1"/>
    <constraint desc="" exp="" field="T2"/>
    <constraint desc="" exp="" field="T3"/>
    <constraint desc="" exp="" field="T4"/>
    <constraint desc="" exp="" field="T5"/>
    <constraint desc="" exp="" field="T6"/>
    <constraint desc="" exp="" field="T7"/>
    <constraint desc="" exp="" field="T8"/>
    <constraint desc="" exp="" field="T9"/>
    <constraint desc="" exp="" field="T10"/>
    <constraint desc="" exp="" field="T11"/>
    <constraint desc="" exp="" field="T12"/>
    <constraint desc="" exp="" field="T13"/>
    <constraint desc="" exp="" field="T14"/>
    <constraint desc="" exp="" field="T15"/>
    <constraint desc="" exp="" field="T16"/>
    <constraint desc="" exp="" field="T17"/>
    <constraint desc="" exp="" field="T18"/>
    <constraint desc="" exp="" field="T19"/>
    <constraint desc="" exp="" field="T20"/>
    <constraint desc="" exp="" field="T21"/>
    <constraint desc="" exp="" field="T22"/>
    <constraint desc="" exp="" field="T23"/>
    <constraint desc="" exp="" field="T24"/>
    <constraint desc="" exp="" field="T25"/>
    <constraint desc="" exp="" field="T26"/>
    <constraint desc="" exp="" field="T27"/>
    <constraint desc="" exp="" field="T28"/>
    <constraint desc="" exp="" field="T29"/>
    <constraint desc="" exp="" field="T30"/>
    <constraint desc="" exp="" field="T31"/>
    <constraint desc="" exp="" field="T32"/>
    <constraint desc="" exp="" field="T33"/>
    <constraint desc="" exp="" field="T34"/>
    <constraint desc="" exp="" field="T35"/>
    <constraint desc="" exp="" field="T36"/>
    <constraint desc="" exp="" field="T37"/>
    <constraint desc="" exp="" field="T38"/>
    <constraint desc="" exp="" field="T39"/>
    <constraint desc="" exp="" field="T40"/>
    <constraint desc="" exp="" field="T41"/>
    <constraint desc="" exp="" field="T42"/>
    <constraint desc="" exp="" field="T43"/>
    <constraint desc="" exp="" field="T44"/>
    <constraint desc="" exp="" field="T45"/>
    <constraint desc="" exp="" field="T46"/>
    <constraint desc="" exp="" field="T47"/>
    <constraint desc="" exp="" field="T48"/>
    <constraint desc="" exp="" field="T49"/>
    <constraint desc="" exp="" field="T50"/>
    <constraint desc="" exp="" field="T51"/>
    <constraint desc="" exp="" field="T52"/>
    <constraint desc="" exp="" field="T53"/>
    <constraint desc="" exp="" field="T54"/>
    <constraint desc="" exp="" field="T55"/>
    <constraint desc="" exp="" field="T56"/>
    <constraint desc="" exp="" field="T57"/>
    <constraint desc="" exp="" field="T58"/>
    <constraint desc="" exp="" field="T59"/>
    <constraint desc="" exp="" field="T60"/>
    <constraint desc="" exp="" field="T61"/>
    <constraint desc="" exp="" field="T62"/>
    <constraint desc="" exp="" field="T63"/>
    <constraint desc="" exp="" field="T64"/>
    <constraint desc="" exp="" field="T65"/>
    <constraint desc="" exp="" field="T66"/>
    <constraint desc="" exp="" field="T67"/>
    <constraint desc="" exp="" field="T68"/>
    <constraint desc="" exp="" field="T69"/>
    <constraint desc="" exp="" field="T70"/>
    <constraint desc="" exp="" field="T71"/>
    <constraint desc="" exp="" field="T72"/>
    <constraint desc="" exp="" field="T73"/>
    <constraint desc="" exp="" field="T74"/>
    <constraint desc="" exp="" field="T75"/>
    <constraint desc="" exp="" field="T76"/>
    <constraint desc="" exp="" field="T77"/>
    <constraint desc="" exp="" field="T78"/>
    <constraint desc="" exp="" field="T79"/>
    <constraint desc="" exp="" field="T80"/>
    <constraint desc="" exp="" field="T81"/>
    <constraint desc="" exp="" field="T82"/>
    <constraint desc="" exp="" field="T83"/>
    <constraint desc="" exp="" field="T84"/>
    <constraint desc="" exp="" field="T85"/>
    <constraint desc="" exp="" field="T86"/>
    <constraint desc="" exp="" field="T87"/>
    <constraint desc="" exp="" field="T88"/>
    <constraint desc="" exp="" field="T89"/>
    <constraint desc="" exp="" field="T90"/>
    <constraint desc="" exp="" field="T91"/>
    <constraint desc="" exp="" field="T92"/>
    <constraint desc="" exp="" field="T93"/>
    <constraint desc="" exp="" field="T94"/>
    <constraint desc="" exp="" field="T95"/>
    <constraint desc="" exp="" field="T96"/>
    <constraint desc="" exp="" field="T97"/>
    <constraint desc="" exp="" field="T98"/>
    <constraint desc="" exp="" field="T99"/>
    <constraint desc="" exp="" field="T100"/>
    <constraint desc="" exp="" field="T101"/>
    <constraint desc="" exp="" field="T102"/>
    <constraint desc="" exp="" field="T103"/>
    <constraint desc="" exp="" field="T104"/>
    <constraint desc="" exp="" field="T105"/>
    <constraint desc="" exp="" field="T106"/>
    <constraint desc="" exp="" field="T107"/>
  </constraintExpressions>
  <expressionfields/>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" width="-1" type="field" name="Id"/>
      <column hidden="0" width="-1" type="field" name="Type"/>
      <column hidden="0" width="-1" type="field" name="Time"/>
      <column hidden="0" width="-1" type="field" name="T0"/>
      <column hidden="0" width="-1" type="field" name="T1"/>
      <column hidden="0" width="-1" type="field" name="T2"/>
      <column hidden="0" width="-1" type="field" name="T3"/>
      <column hidden="0" width="-1" type="field" name="T4"/>
      <column hidden="0" width="-1" type="field" name="T5"/>
      <column hidden="0" width="-1" type="field" name="T6"/>
      <column hidden="0" width="-1" type="field" name="T7"/>
      <column hidden="0" width="-1" type="field" name="T8"/>
      <column hidden="0" width="-1" type="field" name="T9"/>
      <column hidden="0" width="-1" type="field" name="T10"/>
      <column hidden="0" width="-1" type="field" name="T11"/>
      <column hidden="0" width="-1" type="field" name="T12"/>
      <column hidden="0" width="-1" type="field" name="T13"/>
      <column hidden="0" width="-1" type="field" name="T14"/>
      <column hidden="0" width="-1" type="field" name="T15"/>
      <column hidden="0" width="-1" type="field" name="T16"/>
      <column hidden="0" width="-1" type="field" name="T17"/>
      <column hidden="0" width="-1" type="field" name="T18"/>
      <column hidden="0" width="-1" type="field" name="T19"/>
      <column hidden="0" width="-1" type="field" name="T20"/>
      <column hidden="0" width="-1" type="field" name="T21"/>
      <column hidden="0" width="-1" type="field" name="T22"/>
      <column hidden="0" width="-1" type="field" name="T23"/>
      <column hidden="0" width="-1" type="field" name="T24"/>
      <column hidden="0" width="-1" type="field" name="T25"/>
      <column hidden="0" width="-1" type="field" name="T26"/>
      <column hidden="0" width="-1" type="field" name="T27"/>
      <column hidden="0" width="-1" type="field" name="T28"/>
      <column hidden="0" width="-1" type="field" name="T29"/>
      <column hidden="0" width="-1" type="field" name="T30"/>
      <column hidden="0" width="-1" type="field" name="T31"/>
      <column hidden="0" width="-1" type="field" name="T32"/>
      <column hidden="0" width="-1" type="field" name="T33"/>
      <column hidden="0" width="-1" type="field" name="T34"/>
      <column hidden="0" width="-1" type="field" name="T35"/>
      <column hidden="0" width="-1" type="field" name="T36"/>
      <column hidden="0" width="-1" type="field" name="T37"/>
      <column hidden="0" width="-1" type="field" name="T38"/>
      <column hidden="0" width="-1" type="field" name="T39"/>
      <column hidden="0" width="-1" type="field" name="T40"/>
      <column hidden="0" width="-1" type="field" name="T41"/>
      <column hidden="0" width="-1" type="field" name="T42"/>
      <column hidden="0" width="-1" type="field" name="T43"/>
      <column hidden="0" width="-1" type="field" name="T44"/>
      <column hidden="0" width="-1" type="field" name="T45"/>
      <column hidden="0" width="-1" type="field" name="T46"/>
      <column hidden="0" width="-1" type="field" name="T47"/>
      <column hidden="0" width="-1" type="field" name="T48"/>
      <column hidden="0" width="-1" type="field" name="T49"/>
      <column hidden="0" width="-1" type="field" name="T50"/>
      <column hidden="0" width="-1" type="field" name="T51"/>
      <column hidden="0" width="-1" type="field" name="T52"/>
      <column hidden="0" width="-1" type="field" name="T53"/>
      <column hidden="0" width="-1" type="field" name="T54"/>
      <column hidden="0" width="-1" type="field" name="T55"/>
      <column hidden="0" width="-1" type="field" name="T56"/>
      <column hidden="0" width="-1" type="field" name="T57"/>
      <column hidden="0" width="-1" type="field" name="T58"/>
      <column hidden="0" width="-1" type="field" name="T59"/>
      <column hidden="0" width="-1" type="field" name="T60"/>
      <column hidden="0" width="-1" type="field" name="T61"/>
      <column hidden="0" width="-1" type="field" name="T62"/>
      <column hidden="0" width="-1" type="field" name="T63"/>
      <column hidden="0" width="-1" type="field" name="T64"/>
      <column hidden="0" width="-1" type="field" name="T65"/>
      <column hidden="0" width="-1" type="field" name="T66"/>
      <column hidden="0" width="-1" type="field" name="T67"/>
      <column hidden="0" width="-1" type="field" name="T68"/>
      <column hidden="0" width="-1" type="field" name="T69"/>
      <column hidden="0" width="-1" type="field" name="T70"/>
      <column hidden="0" width="-1" type="field" name="T71"/>
      <column hidden="0" width="-1" type="field" name="T72"/>
      <column hidden="0" width="-1" type="field" name="T73"/>
      <column hidden="0" width="-1" type="field" name="T74"/>
      <column hidden="0" width="-1" type="field" name="T75"/>
      <column hidden="0" width="-1" type="field" name="T76"/>
      <column hidden="0" width="-1" type="field" name="T77"/>
      <column hidden="0" width="-1" type="field" name="T78"/>
      <column hidden="0" width="-1" type="field" name="T79"/>
      <column hidden="0" width="-1" type="field" name="T80"/>
      <column hidden="0" width="-1" type="field" name="T81"/>
      <column hidden="0" width="-1" type="field" name="T82"/>
      <column hidden="0" width="-1" type="field" name="T83"/>
      <column hidden="0" width="-1" type="field" name="T84"/>
      <column hidden="0" width="-1" type="field" name="T85"/>
      <column hidden="0" width="-1" type="field" name="T86"/>
      <column hidden="0" width="-1" type="field" name="T87"/>
      <column hidden="0" width="-1" type="field" name="T88"/>
      <column hidden="0" width="-1" type="field" name="T89"/>
      <column hidden="0" width="-1" type="field" name="T90"/>
      <column hidden="0" width="-1" type="field" name="T91"/>
      <column hidden="0" width="-1" type="field" name="T92"/>
      <column hidden="0" width="-1" type="field" name="T93"/>
      <column hidden="0" width="-1" type="field" name="T94"/>
      <column hidden="0" width="-1" type="field" name="T95"/>
      <column hidden="0" width="-1" type="field" name="T96"/>
      <column hidden="0" width="-1" type="field" name="T97"/>
      <column hidden="0" width="-1" type="field" name="T98"/>
      <column hidden="0" width="-1" type="field" name="T99"/>
      <column hidden="0" width="-1" type="field" name="T100"/>
      <column hidden="0" width="-1" type="field" name="T101"/>
      <column hidden="0" width="-1" type="field" name="T102"/>
      <column hidden="0" width="-1" type="field" name="T103"/>
      <column hidden="0" width="-1" type="field" name="T104"/>
      <column hidden="0" width="-1" type="field" name="T105"/>
      <column hidden="0" width="-1" type="field" name="T106"/>
      <column hidden="0" width="-1" type="field" name="T107"/>
      <column hidden="1" width="-1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <previewExpression>COALESCE( "Id", '&lt;NULL>' )</previewExpression>
  <mapTip enabled="1">Status: [% "T0" %]</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
