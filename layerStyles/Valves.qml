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
        <layer locked="0" id="{d57e4065-d202-464d-928d-6a3459c32297}" pass="0" class="SimpleLine" enabled="1">
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
                  <Option type="QString" value="if(IniStatus is NULL, '#85b66f',if(IniStatus is 'CLOSED', '#ff0f13', if(IniStatus !='ACTIVE', '#85b66f','#ff9900')))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer locked="0" id="{2168a092-f2c4-4bee-a00f-99e5ceaae9f4}" pass="0" class="MarkerLine" enabled="1">
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
          <symbol force_rhr="0" frame_rate="10" type="marker" is_animated="0" name="@0@1" alpha="1" clip_to_extent="1">
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
            <layer locked="0" id="{8822a772-efa6-4354-b7d5-8c51f60ece01}" pass="0" class="SvgMarker" enabled="1">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+DQo8c3ZnDQogICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iDQogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIg0KICAgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIg0KICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyINCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyINCiAgIHhtbG5zOnNvZGlwb2RpPSJodHRwOi8vc29kaXBvZGkuc291cmNlZm9yZ2UubmV0L0RURC9zb2RpcG9kaS0wLmR0ZCINCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIg0KICAgaWQ9InN2ZzkiDQogICBoZWlnaHQ9IjE1NG1tIg0KICAgd2lkdGg9IjE1NG1tIg0KICAgdmVyc2lvbj0iMS4wIg0KICAgc29kaXBvZGk6ZG9jbmFtZT0idmFsdmVzLnN2ZyINCiAgIGlua3NjYXBlOnZlcnNpb249IjAuOTIuMyAoMjQwNTU0NiwgMjAxOC0wMy0xMSkiPg0KICA8c29kaXBvZGk6bmFtZWR2aWV3DQogICAgIHBhZ2Vjb2xvcj0iI2ZmZmZmZiINCiAgICAgYm9yZGVyY29sb3I9IiM2NjY2NjYiDQogICAgIGJvcmRlcm9wYWNpdHk9IjEiDQogICAgIG9iamVjdHRvbGVyYW5jZT0iMTAiDQogICAgIGdyaWR0b2xlcmFuY2U9IjEwIg0KICAgICBndWlkZXRvbGVyYW5jZT0iMTAiDQogICAgIGlua3NjYXBlOnBhZ2VvcGFjaXR5PSIwIg0KICAgICBpbmtzY2FwZTpwYWdlc2hhZG93PSIyIg0KICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjEyODAiDQogICAgIGlua3NjYXBlOndpbmRvdy1oZWlnaHQ9Ijk2MSINCiAgICAgaWQ9Im5hbWVkdmlldzgiDQogICAgIHNob3dncmlkPSJmYWxzZSINCiAgICAgaW5rc2NhcGU6em9vbT0iMC40MDU0NjUzNyINCiAgICAgaW5rc2NhcGU6Y3g9IjI5MS4wMjM2MiINCiAgICAgaW5rc2NhcGU6Y3k9IjI5MS4wMjM2MiINCiAgICAgaW5rc2NhcGU6d2luZG93LXg9Ii04Ig0KICAgICBpbmtzY2FwZTp3aW5kb3cteT0iLTgiDQogICAgIGlua3NjYXBlOndpbmRvdy1tYXhpbWl6ZWQ9IjEiDQogICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9InN2ZzkiIC8+DQogIDxtZXRhZGF0YQ0KICAgICBpZD0ibWV0YWRhdGExMyI+DQogICAgPHJkZjpSREY+DQogICAgICA8Y2M6V29yaw0KICAgICAgICAgcmRmOmFib3V0PSIiPg0KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4NCiAgICAgICAgPGRjOnR5cGUNCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4NCiAgICAgICAgPGRjOnRpdGxlIC8+DQogICAgICA8L2NjOldvcms+DQogICAgPC9yZGY6UkRGPg0KICA8L21ldGFkYXRhPg0KICA8ZGVmcw0KICAgICBpZD0iZGVmczMiPg0KICAgIDxwYXR0ZXJuDQogICAgICAgeT0iMCINCiAgICAgICB4PSIwIg0KICAgICAgIGhlaWdodD0iNiINCiAgICAgICB3aWR0aD0iNiINCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIg0KICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+DQogIDwvZGVmcz4NCiAgPHBhdGgNCiAgICAgaWQ9InBhdGg1Ig0KICAgICBkPSJtIDExNS42MzI0NiwxNzYuNDAwMzEgYyAtNi4wMjYxMywwLjA3NDQgLTExLjQ1NzA5LDQuOTEwMTggLTExLjUzMTQ5LDExLjYwNTg4IGwgLTAuNTk1MTcsMTAxLjMyODM2IC0wLjU5NTE4LDEwMS40MDI3NSBjIDAsOC45Mjc2MSA5LjY3MTU4LDE0LjU4MTc2IDE3LjQwODgzLDEwLjExNzk2IGwgODguMDg1NzQsLTUwLjE0MzQgODIuMjA4NCwtNDYuODY5OTUgODEuMzE1NjMsNDguMzU3ODkgODcuMTE4NTcsNTEuNzgwMTIgYyA3LjY2Mjg2LDQuNjEyNiAxNy40MDg4NCwtMC44OTI3NiAxNy41NTc2MywtOS44MjAzNyBsIDEuMjY0NzQsLTEwMS4zMjgzNSAxLjI2NDc1LC0xMDEuNDAyNzUgYyAwLjE0ODc5LC04LjkyNzYxIC05LjQ0ODM4LC0xNC42NTYxNiAtMTcuMjYwMDQsLTEwLjI2Njc1IGwgLTg4LjQ1NzcyLDQ5LjU0ODIyIC04Mi41ODAzOCw0Ni4zNDkxNyAtODEuNzYyMDEsLTQ3LjgzNzExIC04Ny40OTA1NiwtNTEuMTg0OTUgYyAtMS45MzQzMSwtMS4xMTU5NSAtMy45NDMwMywtMS42MzY3MiAtNS45NTE3NCwtMS42MzY3MiB6IG0gMzQwLjA2NzQ4LDM0Ljg5MjA3IC0xLjA0MTU1LDgxLjI0MTIzIC0xLjA0MTU2LDgxLjE2NjgzIC02OS44NTg1NCwtNDEuNDM4OTggLTY5Ljc4NDEzLC00MS41MTMzOCA3MC44MjU3LC0zOS43Mjc4NSB6Ig0KICAgICBmaWxsPSJwYXJhbShmaWxsKSAjMDAwIg0KICAgICBmaWxsLW9wYWNpdHk9InBhcmFtKGZpbGwtb3BhY2l0eSkiDQogICAgIHN0cm9rZT0icGFyYW0ob3V0bGluZSkgI0ZGRiINCiAgICAgc3Ryb2tlLW9wYWNpdHk9InBhcmFtKG91dGxpbmUtb3BhY2l0eSkiDQogICAgIHN0cm9rZS13aWR0aD0icGFyYW0ob3V0bGluZS13aWR0aCkgMCINCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4NCiAgPHBhdGgNCiAgICAgaWQ9InBhdGg3Ig0KICAgICBkPSJtIDMxMS41MTkwNywyOTEuNzE1MjUgNzIuMDE2MDQsNDIuNzc4MTIgNzIuMDE2MDQsNDIuODUyNTEgMS4xMTU5NSwtODMuODQ1MTIgLTAuOTY3MTYsLTgyLjIwODM4IGMgLTI0LjM4MTE2LDEzLjY1NzM2IC00Ni43NDY1NywyNS43NjQ5NSAtNzEuMTIzMjgsMzkuNDMwMjYgeiINCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLW9wYWNpdHk6MTtmaWxsLXJ1bGU6bm9uemVybztzdHJva2U6bm9uZTtzdHJva2Utd2lkdGg6MC45Mjk5NjYwOSINCiAgICAgaW5rc2NhcGU6Y29ubmVjdG9yLWN1cnZhdHVyZT0iMCIgLz4NCjwvc3ZnPg0K" name="name"/>
                <Option type="QString" value="-0.5,-0.5" name="offset"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
                <Option type="QString" value="Pixel" name="offset_unit"/>
                <Option type="QString" value="255,255,255,255,rgb:1,1,1,1" name="outline_color"/>
                <Option type="QString" value="0" name="outline_width"/>
                <Option type="QString" value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option name="parameters"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="4" name="size"/>
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
                      <Option type="QString" value="if(IniStatus is NULL, '#85b66f',if(IniStatus is 'CLOSED', '#ff0f13', if(IniStatus !='ACTIVE', '#85b66f','#ff9900')))" name="expression"/>
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
        <layer locked="0" id="{e4dc2e9a-2e17-4cce-8315-47b58ab43686}" pass="0" class="SimpleLine" enabled="1">
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
      <text-style tabStopDistanceUnit="Point" textOrientation="horizontal" multilineHeight="1" blendMode="0" fontWordSpacing="0" multilineHeightUnit="Percentage" fontItalic="0" fontStrikeout="0" fontSize="8" fontWeight="50" fontSizeUnit="Point" fontUnderline="0" legendString="Aa" fontKerning="1" previewBkgrdColor="255,255,255,255,rgb:1,1,1,1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontFamily="Arial" fontLetterSpacing="0" forcedItalic="0" namedStyle="Normal" useSubstitutions="0" textColor="51,160,44,255,rgb:0.20000000000000001,0.62745098039215685,0.17254901960784313,1" tabStopDistance="80" forcedBold="0" capitalization="0" fieldName="concat(&quot;Type&quot;,' ',&quot;Id&quot;)" tabStopDistanceMapUnitScale="3x:0,0,0,0,0,0" isExpression="1" allowHtml="0" textOpacity="1">
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
                <Option type="QString" value="145,82,45,255,rgb:0.56862745098039214,0.32156862745098042,0.17647058823529413,1" name="color"/>
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
          <Option type="QString" value="&lt;symbol force_rhr=&quot;0&quot; frame_rate=&quot;10&quot; type=&quot;line&quot; is_animated=&quot;0&quot; name=&quot;symbol&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer locked=&quot;0&quot; id=&quot;{c4537359-1dfc-490c-855b-77360f5efafa}&quot; pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;align_dash_pattern&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;square&quot; name=&quot;capstyle&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;5;2&quot; name=&quot;customdash&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;customdash_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;customdash_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;dash_pattern_offset&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;dash_pattern_offset_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;draw_inside_polygon&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;bevel&quot; name=&quot;joinstyle&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;60,60,60,255,rgb:0.23529411764705882,0.23529411764705882,0.23529411764705882,1&quot; name=&quot;line_color&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;solid&quot; name=&quot;line_style&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0.3&quot; name=&quot;line_width&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;line_width_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;offset&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;offset_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;offset_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;ring_filter&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_end&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_end_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_start&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_start_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;use_custom_dash&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;width_map_unit_scale&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol"/>
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
      <Option type="QString" value="qgisred_valves" name="qgisred_identifier"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <fieldConfiguration>
    <field configurationFlags="NoFlag" name="Id"/>
    <field configurationFlags="NoFlag" name="Diameter"/>
    <field configurationFlags="NoFlag" name="Type"/>
    <field configurationFlags="NoFlag" name="Setting"/>
    <field configurationFlags="NoFlag" name="IdHeadLoss"/>
    <field configurationFlags="NoFlag" name="LossCoeff"/>
    <field configurationFlags="NoFlag" name="IniStatus"/>
    <field configurationFlags="NoFlag" name="Tag"/>
    <field configurationFlags="NoFlag" name="Descrip"/>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="Id" name=""/>
    <alias index="1" field="Diameter" name=""/>
    <alias index="2" field="Type" name=""/>
    <alias index="3" field="Setting" name=""/>
    <alias index="4" field="IdHeadLoss" name=""/>
    <alias index="5" field="LossCoeff" name=""/>
    <alias index="6" field="IniStatus" name=""/>
    <alias index="7" field="Tag" name=""/>
    <alias index="8" field="Descrip" name=""/>
  </aliases>
  <splitPolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="Diameter" policy="Duplicate"/>
    <policy field="Type" policy="Duplicate"/>
    <policy field="Setting" policy="Duplicate"/>
    <policy field="IdHeadLoss" policy="Duplicate"/>
    <policy field="LossCoeff" policy="Duplicate"/>
    <policy field="IniStatus" policy="Duplicate"/>
    <policy field="Tag" policy="Duplicate"/>
    <policy field="Descrip" policy="Duplicate"/>
  </splitPolicies>
  <duplicatePolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="Diameter" policy="Duplicate"/>
    <policy field="Type" policy="Duplicate"/>
    <policy field="Setting" policy="Duplicate"/>
    <policy field="IdHeadLoss" policy="Duplicate"/>
    <policy field="LossCoeff" policy="Duplicate"/>
    <policy field="IniStatus" policy="Duplicate"/>
    <policy field="Tag" policy="Duplicate"/>
    <policy field="Descrip" policy="Duplicate"/>
  </duplicatePolicies>
  <defaults>
    <default applyOnUpdate="0" field="Id" expression=""/>
    <default applyOnUpdate="0" field="Diameter" expression=""/>
    <default applyOnUpdate="0" field="Type" expression=""/>
    <default applyOnUpdate="0" field="Setting" expression=""/>
    <default applyOnUpdate="0" field="IdHeadLoss" expression=""/>
    <default applyOnUpdate="0" field="LossCoeff" expression=""/>
    <default applyOnUpdate="0" field="IniStatus" expression=""/>
    <default applyOnUpdate="0" field="Tag" expression=""/>
    <default applyOnUpdate="0" field="Descrip" expression=""/>
  </defaults>
  <constraints>
    <constraint field="Id" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Diameter" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Type" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Setting" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IdHeadLoss" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="LossCoeff" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IniStatus" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Tag" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Descrip" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="Id"/>
    <constraint desc="" exp="" field="Diameter"/>
    <constraint desc="" exp="" field="Type"/>
    <constraint desc="" exp="" field="Setting"/>
    <constraint desc="" exp="" field="IdHeadLoss"/>
    <constraint desc="" exp="" field="LossCoeff"/>
    <constraint desc="" exp="" field="IniStatus"/>
    <constraint desc="" exp="" field="Tag"/>
    <constraint desc="" exp="" field="Descrip"/>
  </constraintExpressions>
  <expressionfields/>
  <previewExpression>"Id"</previewExpression>
  <mapTip enabled="1">[% "Type" %] [% "Id" %]</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
