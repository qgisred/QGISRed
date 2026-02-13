<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" labelsEnabled="1" simplifyAlgorithm="0" autoRefreshTime="0" simplifyMaxScale="1" styleCategories="LayerConfiguration|Symbology|Labeling|Fields|MapTips|Rendering|CustomProperties|Notes" simplifyLocal="1" readOnly="0" simplifyDrawingTol="1" symbologyReferenceScale="-1" autoRefreshMode="Disabled" hasScaleBasedVisibilityFlag="0" version="3.40.0-Bratislava" minScale="0" simplifyDrawingHints="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <renderer-v2 referencescale="-1" enableorderby="0" type="singleSymbol" forceraster="0" symbollevels="0">
    <symbols>
      <symbol force_rhr="0" frame_rate="10" type="line" is_animated="0" name="0" alpha="1" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer locked="0" id="{422a9697-ff9a-4d4e-ad50-87e5d170a24b}" pass="0" class="SimpleLine" enabled="1">
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
            <Option type="QString" value="1.5" name="line_width"/>
            <Option type="QString" value="Pixel" name="line_width_unit"/>
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
              <Option type="Map" name="properties">
                <Option type="Map" name="customDash">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="if(IniStatus = 'CLOSED', '5;2', '5000;0')" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="outlineColor">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="if(IniStatus is NULL, '#0f1291',if(IniStatus !='CLOSED', '#0f1291','#ff0f13'))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer locked="0" id="{949b6f67-6fa2-43a2-b147-82aa27d3ce69}" pass="0" class="MarkerLine" enabled="1">
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
              <Option type="Map" name="properties">
                <Option type="Map" name="width">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,5))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol force_rhr="0" frame_rate="10" type="marker" is_animated="0" name="@0@1" alpha="1" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer locked="0" id="{b8e0a9eb-1a26-4831-93cc-a192fba7fea5}" pass="0" class="SvgMarker" enabled="1">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+DQo8c3ZnDQogICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iDQogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIg0KICAgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIg0KICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyINCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyINCiAgIHhtbG5zOnNvZGlwb2RpPSJodHRwOi8vc29kaXBvZGkuc291cmNlZm9yZ2UubmV0L0RURC9zb2RpcG9kaS0wLmR0ZCINCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIg0KICAgaWQ9InN2ZzkiDQogICBoZWlnaHQ9IjE1NG1tIg0KICAgd2lkdGg9IjE1NG1tIg0KICAgdmVyc2lvbj0iMS4wIg0KICAgc29kaXBvZGk6ZG9jbmFtZT0icGlwZXMuc3ZnIg0KICAgaW5rc2NhcGU6dmVyc2lvbj0iMC45Mi4zICgyNDA1NTQ2LCAyMDE4LTAzLTExKSI+DQogIDxzb2RpcG9kaTpuYW1lZHZpZXcNCiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIg0KICAgICBib3JkZXJjb2xvcj0iIzY2NjY2NiINCiAgICAgYm9yZGVyb3BhY2l0eT0iMSINCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCINCiAgICAgZ3JpZHRvbGVyYW5jZT0iMTAiDQogICAgIGd1aWRldG9sZXJhbmNlPSIxMCINCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiDQogICAgIGlua3NjYXBlOnBhZ2VzaGFkb3c9IjIiDQogICAgIGlua3NjYXBlOndpbmRvdy13aWR0aD0iMTkyMCINCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iMTAxNyINCiAgICAgaWQ9Im5hbWVkdmlldzgiDQogICAgIHNob3dncmlkPSJmYWxzZSINCiAgICAgaW5rc2NhcGU6em9vbT0iMC41Ig0KICAgICBpbmtzY2FwZTpjeD0iLTI0Ny42NDk3OSINCiAgICAgaW5rc2NhcGU6Y3k9IjQyMi4xMzIzNiINCiAgICAgaW5rc2NhcGU6d2luZG93LXg9IjEyNzIiDQogICAgIGlua3NjYXBlOndpbmRvdy15PSItOCINCiAgICAgaW5rc2NhcGU6d2luZG93LW1heGltaXplZD0iMSINCiAgICAgaW5rc2NhcGU6Y3VycmVudC1sYXllcj0iZzQ1MjkiIC8+DQogIDxtZXRhZGF0YQ0KICAgICBpZD0ibWV0YWRhdGExMyI+DQogICAgPHJkZjpSREY+DQogICAgICA8Y2M6V29yaw0KICAgICAgICAgcmRmOmFib3V0PSIiPg0KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4NCiAgICAgICAgPGRjOnR5cGUNCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4NCiAgICAgICAgPGRjOnRpdGxlIC8+DQogICAgICA8L2NjOldvcms+DQogICAgPC9yZGY6UkRGPg0KICA8L21ldGFkYXRhPg0KICA8ZGVmcw0KICAgICBpZD0iZGVmczMiPg0KICAgIDxwYXR0ZXJuDQogICAgICAgeT0iMCINCiAgICAgICB4PSIwIg0KICAgICAgIGhlaWdodD0iNiINCiAgICAgICB3aWR0aD0iNiINCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIg0KICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+DQogIDwvZGVmcz4NCiAgPGcNCiAgICAgaWQ9Imc0NTI0Ig0KICAgICB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtMTEuODYyODc4LDQuMTkzNDg3KSI+DQogICAgPGcNCiAgICAgICBpZD0iZzQ1MjkiDQogICAgICAgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTMuMDAwMDM1KSI+DQogICAgICA8cGF0aA0KICAgICAgICAgaWQ9InBhdGg3Ig0KICAgICAgICAgZD0ibSAyMjguNjM4MzEsMTcwLjcxNTgyIGMgLTMuNjc5OTgsMC4wOCAtNi45NTk5NSwyLjk1OTk4IC03LjAzOTk1LDcuMDM5OTUgbCAtMC42NCwxMDkuMDM5MTkgLTAuNTU5OTksMTA4Ljk1OTE5IGMgLTAuMDgsNS41MTk5NiA1LjgzOTk1LDguOTU5OTQgMTAuNTU5OTIsNi4yMzk5NiBsIDk0LjcxOTMsLTUzLjkxOTYgOTQuNzE5MywtNTMuOTk5NiBjIDIuNzk5OTgsLTEuNTk5OTkgNC4xNTk5NywtNC43OTk5NyAzLjM1OTk3LC03LjkxOTk1IC0wLjQ4LC0xLjgzOTk4IC0xLjY3OTk5LC0zLjQzOTk3IC0zLjI3OTk3LC00LjM5OTk2IGwgLTk0LjA3OTMxLC01NS4wMzk2IC05NC4wNzkzLC01NS4wMzk1OSBjIC0xLjE5OTk5LC0wLjYzOTk5IC0yLjQ3OTk4LC0wLjk1OTk5IC0zLjY3OTk3LC0wLjk1OTk5IHoiDQogICAgICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIg0KICAgICAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIg0KICAgICAgICAgc3Ryb2tlPSJwYXJhbShvdXRsaW5lKSAjRkZGIg0KICAgICAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiDQogICAgICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiDQogICAgICAgICBpbmtzY2FwZTpjb25uZWN0b3ItY3VydmF0dXJlPSIwIg0KICAgICAgICAgc29kaXBvZGk6bm9kZXR5cGVzPSJjY2NjY2NjY2NjY2MiIC8+DQogICAgICA8cGF0aA0KICAgICAgICAgZmlsbD0icGFyYW0oZmlsbCkgIzAwMCINCiAgICAgICAgIGZpbGwtb3BhY2l0eT0icGFyYW0oZmlsbC1vcGFjaXR5KSINCiAgICAgICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiINCiAgICAgICAgIHN0cm9rZS1vcGFjaXR5PSJwYXJhbShvdXRsaW5lLW9wYWNpdHkpIg0KICAgICAgICAgc3Ryb2tlLXdpZHRoPSJwYXJhbShvdXRsaW5lLXdpZHRoKSAwIg0KICAgICAgICAgZD0ibSA0MDcuNzIyMDYsMTQ4LjYxMDc2IDEuNzU3MDksLTAuNjU0MDMgMi4wODEyMywtMC4wOTM5IGggNDEuNTE1OTggbCAyLjAwMzg4LDAuMDkyOCAxLjMwODU4LDAuMzU0NzcgMC42NjI1LDAuODU0MyAwLjA4MjksMS41ODY1NyB2IDI3NC40NjY1MSBsIC0wLjEwMzYxLDAuMzcxMjIgLTAuMjY5MjUsMC4xNTI1NSAtMC41NjkzMSwwLjA1NTkgYyAtMTM4LjAzODE3LDAgLTMyLjA1ODEyLDAgLTQ4LjI0NzY0LDAgbCAtMC42MjQ4NSwtMC4wNzM2IC0wLjM2ODg2LC0wLjE3MDQzIC0wLjE2NTY0LC0wLjM2NjEzIFYgMTUwLjIxODc0IGwgMC41MTE1MSwtMC44Nzc5MiB6Ig0KICAgICAgICAgaWQ9InJlY3Q0NTE4Ig0KICAgICAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCINCiAgICAgICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0iY2NjY2NjY2NjY2NjY2NjY2NjYyIgLz4NCiAgICA8L2c+DQogIDwvZz4NCjwvc3ZnPg0K" name="name"/>
                <Option type="QString" value="-0.5,-0.5" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="Pixel" name="offset_unit"/>
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
                    <Option type="Map" name="fillColor">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(IniStatus is NULL, '#0f1291',if(IniStatus !='CLOSED', '#0f1291','#ff0f13'))" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                    <Option type="Map" name="offset">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="tostring(-inf*(if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,5))))|| ',' || tostring(-inf*(if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,5))))" name="expression"/>
                      <Option type="int" value="3" name="type"/>
                    </Option>
                    <Option type="Map" name="size">
                      <Option type="bool" value="true" name="active"/>
                      <Option type="QString" value="if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,5))" name="expression"/>
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
      <symbol force_rhr="0" frame_rate="10" type="line" is_animated="0" name="" alpha="1" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </data_defined_properties>
        <layer locked="0" id="{2ae9d3f4-94f1-42ce-9202-6cc0979b4751}" pass="0" class="SimpleLine" enabled="1">
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
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style tabStopDistanceUnit="Point" textOrientation="horizontal" multilineHeight="1" blendMode="0" fontWordSpacing="0" multilineHeightUnit="Percentage" fontItalic="0" fontStrikeout="0" fontSize="8" fontWeight="50" fontSizeUnit="Point" fontUnderline="0" legendString="Aa" fontKerning="1" previewBkgrdColor="255,255,255,255,rgb:1,1,1,1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontFamily="Arial" fontLetterSpacing="0" forcedItalic="0" namedStyle="Normal" useSubstitutions="0" textColor="31,120,180,255,rgb:0.12156862745098039,0.47058823529411764,0.70588235294117652,1" tabStopDistance="80" forcedBold="0" capitalization="0" fieldName="Id" tabStopDistanceMapUnitScale="3x:0,0,0,0,0,0" isExpression="0" allowHtml="0" textOpacity="1">
        <families/>
        <text-buffer bufferBlendMode="0" bufferSizeUnits="MM" bufferColor="250,250,250,255,rgb:0.98039215686274506,0.98039215686274506,0.98039215686274506,1" bufferSize="1" bufferNoFill="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="0" bufferJoinStyle="128" bufferOpacity="1"/>
        <text-mask maskedSymbolLayers="" maskSizeUnits="MM" maskOpacity="1" maskSize="1.5" maskType="0" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskJoinStyle="128" maskEnabled="0" maskSize2="1.5"/>
        <background shapeType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255,rgb:1,1,1,1" shapeRadiiX="0" shapeOffsetUnit="Point" shapeBorderColor="128,128,128,255,rgb:0.50196078431372548,0.50196078431372548,0.50196078431372548,1" shapeBorderWidth="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeSizeUnit="Point" shapeOffsetX="0" shapeBorderWidthUnit="Point" shapeRotation="0" shapeBlendMode="0" shapeOpacity="1" shapeSizeX="0" shapeSizeY="0" shapeRadiiY="0" shapeRotationType="0" shapeRadiiUnit="Point" shapeSVGFile="" shapeSizeType="0" shapeDraw="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0">
          <symbol force_rhr="0" frame_rate="10" type="marker" is_animated="0" name="markerSymbol" alpha="1" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer locked="0" id="" pass="0" class="SimpleMarker" enabled="1">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="square" name="cap_style"/>
                <Option type="QString" value="190,178,151,255,rgb:0.74509803921568629,0.69803921568627447,0.59215686274509804,1" name="color"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="bevel" name="joinstyle"/>
                <Option type="QString" value="circle" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="outline_color"/>
                <Option type="QString" value="solid" name="outline_style"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="2" name="size"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="size_map_unit_scale"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
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
          <symbol force_rhr="0" frame_rate="10" type="fill" is_animated="0" name="fillSymbol" alpha="1" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer locked="0" id="" pass="0" class="SimpleFill" enabled="1">
              <Option type="Map">
                <Option type="QString" value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="color"/>
                <Option type="QString" value="bevel" name="joinstyle"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="128,128,128,255,rgb:0.50196078431372548,0.50196078431372548,0.50196078431372548,1" name="outline_color"/>
                <Option type="QString" value="no" name="outline_style"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="Point" name="outline_width_unit"/>
                <Option type="QString" value="solid" name="style"/>
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
        </background>
        <shadow shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowDraw="0" shadowOffsetUnit="MM" shadowOffsetDist="1" shadowBlendMode="6" shadowOffsetAngle="135" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowRadiusUnit="MM" shadowRadius="1.5" shadowUnder="0" shadowOffsetGlobal="1" shadowOpacity="0.69999999999999996" shadowRadiusAlphaOnly="0" shadowColor="0,0,0,255,rgb:0,0,0,1"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format leftDirectionSymbol="&lt;" plussign="0" useMaxLineLengthForAutoWrap="1" wrapChar="" reverseDirectionSymbol="0" autoWrapLength="0" decimals="3" placeDirectionSymbol="0" formatNumbers="0" multilineAlign="0" rightDirectionSymbol=">" addDirectionSymbol="0"/>
      <placement overrunDistanceUnit="MM" prioritization="PreferCloser" geometryGeneratorType="PointGeometry" centroidInside="0" maximumDistance="0" layerType="LineGeometry" lineAnchorClipping="0" offsetUnits="MM" preserveRotation="1" repeatDistance="0" yOffset="0" xOffset="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" priority="5" geometryGeneratorEnabled="0" offsetType="0" placement="2" overlapHandling="PreventOverlap" dist="0" geometryGenerator="" lineAnchorType="0" quadOffset="4" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" polygonPlacementFlags="2" centroidWhole="0" allowDegraded="0" lineAnchorTextPoint="FollowPlacement" repeatDistanceUnits="MM" rotationUnit="AngleDegrees" maximumDistanceUnit="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" placementFlags="10" fitInPolygonOnly="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" distMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleOut="-25" maximumDistanceMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="25" distUnits="MM" lineAnchorPercent="0.5" overrunDistance="0" rotationAngle="0"/>
      <rendering scaleMax="0" zIndex="0" obstacle="1" minFeatureSize="0" fontLimitPixelSize="0" drawLabels="1" fontMaxPixelSize="10000" limitNumLabels="0" mergeLines="0" obstacleFactor="1" labelPerPart="0" maxNumLabels="2000" upsidedownLabels="0" fontMinPixelSize="3" scaleVisibility="0" obstacleType="1" scaleMin="0" unplacedVisibility="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option name="properties"/>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" value="pole_of_inaccessibility" name="anchorPoint"/>
          <Option type="int" value="0" name="blendMode"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
          <Option type="bool" value="false" name="drawToAllParts"/>
          <Option type="QString" value="0" name="enabled"/>
          <Option type="QString" value="point_on_exterior" name="labelAnchorPoint"/>
          <Option type="QString" value="&lt;symbol force_rhr=&quot;0&quot; frame_rate=&quot;10&quot; type=&quot;line&quot; is_animated=&quot;0&quot; name=&quot;symbol&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer locked=&quot;0&quot; id=&quot;{32581f3b-e321-45c2-a0d7-b7d209ec9547}&quot; pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;align_dash_pattern&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;square&quot; name=&quot;capstyle&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;5;2&quot; name=&quot;customdash&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;customdash_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;customdash_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;dash_pattern_offset&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;dash_pattern_offset_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;draw_inside_polygon&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;bevel&quot; name=&quot;joinstyle&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;60,60,60,255,rgb:0.23529411764705882,0.23529411764705882,0.23529411764705882,1&quot; name=&quot;line_color&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;solid&quot; name=&quot;line_style&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0.3&quot; name=&quot;line_width&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;line_width_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;offset&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;offset_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;offset_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;ring_filter&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_end&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_end_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_start&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_start_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;use_custom_dash&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;width_map_unit_scale&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol"/>
          <Option type="double" value="0" name="minLength"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale"/>
          <Option type="QString" value="MM" name="minLengthUnit"/>
          <Option type="double" value="0" name="offsetFromAnchor"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromAnchorUnit"/>
          <Option type="double" value="0" name="offsetFromLabel"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <customproperties>
    <Option type="Map">
      <Option type="int" value="0" name="embeddedWidgets/count"/>
      <Option type="QString" value="qgisred_pipes" name="qgisred_identifier"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <fieldConfiguration>
    <field configurationFlags="NoFlag" name="Id"/>
    <field configurationFlags="NoFlag" name="Length"/>
    <field configurationFlags="NoFlag" name="Diameter"/>
    <field configurationFlags="NoFlag" name="RoughCoeff"/>
    <field configurationFlags="NoFlag" name="LossCoeff"/>
    <field configurationFlags="NoFlag" name="Material"/>
    <field configurationFlags="NoFlag" name="InstalDate"/>
    <field configurationFlags="NoFlag" name="IniStatus"/>
    <field configurationFlags="NoFlag" name="BulkCoeff"/>
    <field configurationFlags="NoFlag" name="WallCoeff"/>
    <field configurationFlags="NoFlag" name="Tag"/>
    <field configurationFlags="NoFlag" name="Descrip"/>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="Id" name=""/>
    <alias index="1" field="Length" name=""/>
    <alias index="2" field="Diameter" name=""/>
    <alias index="3" field="RoughCoeff" name=""/>
    <alias index="4" field="LossCoeff" name=""/>
    <alias index="5" field="Material" name=""/>
    <alias index="6" field="InstalDate" name=""/>
    <alias index="7" field="IniStatus" name=""/>
    <alias index="8" field="BulkCoeff" name=""/>
    <alias index="9" field="WallCoeff" name=""/>
    <alias index="10" field="Tag" name=""/>
    <alias index="11" field="Descrip" name=""/>
  </aliases>
  <splitPolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="Length" policy="Duplicate"/>
    <policy field="Diameter" policy="Duplicate"/>
    <policy field="RoughCoeff" policy="Duplicate"/>
    <policy field="LossCoeff" policy="Duplicate"/>
    <policy field="Material" policy="Duplicate"/>
    <policy field="InstalDate" policy="Duplicate"/>
    <policy field="IniStatus" policy="Duplicate"/>
    <policy field="BulkCoeff" policy="Duplicate"/>
    <policy field="WallCoeff" policy="Duplicate"/>
    <policy field="Tag" policy="Duplicate"/>
    <policy field="Descrip" policy="Duplicate"/>
  </splitPolicies>
  <duplicatePolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="Length" policy="Duplicate"/>
    <policy field="Diameter" policy="Duplicate"/>
    <policy field="RoughCoeff" policy="Duplicate"/>
    <policy field="LossCoeff" policy="Duplicate"/>
    <policy field="Material" policy="Duplicate"/>
    <policy field="InstalDate" policy="Duplicate"/>
    <policy field="IniStatus" policy="Duplicate"/>
    <policy field="BulkCoeff" policy="Duplicate"/>
    <policy field="WallCoeff" policy="Duplicate"/>
    <policy field="Tag" policy="Duplicate"/>
    <policy field="Descrip" policy="Duplicate"/>
  </duplicatePolicies>
  <defaults>
    <default applyOnUpdate="0" field="Id" expression=""/>
    <default applyOnUpdate="0" field="Length" expression=""/>
    <default applyOnUpdate="0" field="Diameter" expression=""/>
    <default applyOnUpdate="0" field="RoughCoeff" expression=""/>
    <default applyOnUpdate="0" field="LossCoeff" expression=""/>
    <default applyOnUpdate="0" field="Material" expression=""/>
    <default applyOnUpdate="0" field="InstalDate" expression=""/>
    <default applyOnUpdate="0" field="IniStatus" expression=""/>
    <default applyOnUpdate="0" field="BulkCoeff" expression=""/>
    <default applyOnUpdate="0" field="WallCoeff" expression=""/>
    <default applyOnUpdate="0" field="Tag" expression=""/>
    <default applyOnUpdate="0" field="Descrip" expression=""/>
  </defaults>
  <constraints>
    <constraint field="Id" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Length" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Diameter" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="RoughCoeff" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="LossCoeff" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Material" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="InstalDate" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IniStatus" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="BulkCoeff" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="WallCoeff" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Tag" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Descrip" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="Id"/>
    <constraint desc="" exp="" field="Length"/>
    <constraint desc="" exp="" field="Diameter"/>
    <constraint desc="" exp="" field="RoughCoeff"/>
    <constraint desc="" exp="" field="LossCoeff"/>
    <constraint desc="" exp="" field="Material"/>
    <constraint desc="" exp="" field="InstalDate"/>
    <constraint desc="" exp="" field="IniStatus"/>
    <constraint desc="" exp="" field="BulkCoeff"/>
    <constraint desc="" exp="" field="WallCoeff"/>
    <constraint desc="" exp="" field="Tag"/>
    <constraint desc="" exp="" field="Descrip"/>
  </constraintExpressions>
  <expressionfields/>
  <previewExpression>"Id"</previewExpression>
  <mapTip enabled="1">Pipe [% "Id" %]</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
