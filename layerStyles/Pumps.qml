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
        <layer locked="0" id="{10588269-2d16-47d1-a023-5f2575d435bf}" pass="0" class="SimpleLine" enabled="1">
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
                  <Option type="QString" value="if(IniStatus is NULL, '#85b66f',if(IniStatus !='CLOSED', '#85b66f','#ff0f13'))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer locked="0" id="{b356d598-d92a-48f8-8c9c-5b608e49dac1}" pass="0" class="MarkerLine" enabled="1">
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
            <layer locked="0" id="{12e65fdd-dd06-4c9e-9f45-6e7e8440ca08}" pass="0" class="SvgMarker" enabled="1">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="0,0,0,255,rgb:0,0,0,1" name="color"/>
                <Option type="QString" value="0" name="fixedAspectRatio"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+DQo8c3ZnDQogICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iDQogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIg0KICAgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIg0KICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyINCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyINCiAgIGlkPSJzdmc5Ig0KICAgaGVpZ2h0PSIxNTRtbSINCiAgIHdpZHRoPSIxNTRtbSINCiAgIHZlcnNpb249IjEuMCI+DQogIDxtZXRhZGF0YQ0KICAgICBpZD0ibWV0YWRhdGExMyI+DQogICAgPHJkZjpSREY+DQogICAgICA8Y2M6V29yaw0KICAgICAgICAgcmRmOmFib3V0PSIiPg0KICAgICAgICA8ZGM6Zm9ybWF0PmltYWdlL3N2Zyt4bWw8L2RjOmZvcm1hdD4NCiAgICAgICAgPGRjOnR5cGUNCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4NCiAgICAgICAgPGRjOnRpdGxlPjwvZGM6dGl0bGU+DQogICAgICA8L2NjOldvcms+DQogICAgPC9yZGY6UkRGPg0KICA8L21ldGFkYXRhPg0KICA8ZGVmcw0KICAgICBpZD0iZGVmczMiPg0KICAgIDxwYXR0ZXJuDQogICAgICAgeT0iMCINCiAgICAgICB4PSIwIg0KICAgICAgIGhlaWdodD0iNiINCiAgICAgICB3aWR0aD0iNiINCiAgICAgICBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIg0KICAgICAgIGlkPSJFTUZoYmFzZXBhdHRlcm4iIC8+DQogIDwvZGVmcz4NCiAgPHBhdGgNCiAgICAgaWQ9InBhdGg1Ig0KICAgICBkPSIgIE0gMjg5LjY3Nzg1LDE1NS4wMzg4NSAgIEMgMjE1LjI3ODQxLDE1NS4wMzg4NSAxNTQuNjM4ODUsMjE1LjU5ODQgMTU0LjYzODg1LDI4OS45OTc4NSAgIEMgMTU0LjYzODg1LDM2NC4zOTczIDIxNS4yNzg0MSw0MjUuMDM2ODUgMjg5LjY3Nzg1LDQyNS4wMzY4NSAgIEMgMzY0LjA3NzMsNDI1LjAzNjg1IDQyNC42MzY4NSwzNjQuMzk3MyA0MjQuNjM2ODUsMjg5Ljk5Nzg1ICAgQyA0MjQuNjM2ODUsMjE1LjU5ODQgMzY0LjA3NzMsMTU1LjAzODg1IDI4OS42Nzc4NSwxNTUuMDM4ODUgICB6ICINCiAgICAgc3R5bGU9ImZpbGw6I2ZmZmZmZjtmaWxsLXJ1bGU6bm9uemVybztmaWxsLW9wYWNpdHk6MTtzdHJva2U6bm9uZSIgLz4NCiAgPHBhdGgNCiAgICAgaWQ9InBhdGg3Ig0KICAgICBkPSIgIE0gMjg5Ljk5Nzg1LDEyMy45OTkwOCAgIEMgMTk4LjU1ODUzLDEyMy45OTkwOCAxMjMuOTk5MDgsMTk4LjU1ODUzIDEyMy45OTkwOCwyODkuOTk3ODUgICBDIDEyMy45OTkwOCwzODEuNDM3MTcgMTk4LjU1ODUzLDQ1NS45OTY2MiAyODkuOTk3ODUsNDU1Ljk5NjYyICAgQyAzODEuNDM3MTcsNDU1Ljk5NjYyIDQ1NS45OTY2MiwzODEuNDM3MTcgNDU1Ljk5NjYyLDI4OS45OTc4NSAgIEMgNDU1Ljk5NjYyLDE5OC41NTg1MyAzODEuNDM3MTcsMTIzLjk5OTA4IDI4OS45OTc4NSwxMjMuOTk5MDggICB6ICBNIDI4OS45OTc4NSwxNTUuOTk4ODQgICBDIDM2NC4yMzczLDE1NS45OTg4NCA0MjMuOTk2ODYsMjE1Ljc1ODQgNDIzLjk5Njg2LDI4OS45OTc4NSAgIEMgNDIzLjk5Njg2LDM2NC4yMzczIDM2NC4yMzczLDQyMy45OTY4NiAyODkuOTk3ODUsNDIzLjk5Njg2ICAgQyAyMTUuNzU4NCw0MjMuOTk2ODYgMTU1Ljk5ODg0LDM2NC4yMzczIDE1NS45OTg4NCwyODkuOTk3ODUgICBDIDE1NS45OTg4NCwyMTUuNzU4NCAyMTUuNzU4NCwxNTUuOTk4ODQgMjg5Ljk5Nzg1LDE1NS45OTg4NCAgIHogIE0gMjI4LjYzODMxLDE3Mi45NTg3MiAgIEMgMjI0Ljk1ODMzLDE3My4wMzg3MiAyMjEuNjc4MzYsMTc1LjkxODcgMjIxLjU5ODM2LDE3OS45OTg2NyAgIEwgMjIwLjk1ODM2LDI4OS4wMzc4NiAgIEwgMjIwLjM5ODM3LDM5Ny45OTcwNSAgIEMgMjIwLjMxODM3LDQwMy41MTcwMSAyMjYuMjM4MzIsNDA2Ljk1Njk5IDIzMC45NTgyOSw0MDQuMjM3MDEgICBMIDMyNS42Nzc1OSwzNTAuMzE3NDEgICBMIDQyMC4zOTY4OSwyOTYuMzE3ODEgICBDIDQyMy4xOTY4NywyOTQuNzE3ODIgNDI0LjU1Njg2LDI5MS41MTc4NCA0MjMuNzU2ODYsMjg4LjM5Nzg2ICAgQyA0MjMuMjc2ODYsMjg2LjU1Nzg4IDQyMi4wNzY4NywyODQuOTU3ODkgNDIwLjQ3Njg5LDI4My45OTc5ICAgTCAzMjYuMzk3NTgsMjI4Ljk1ODMgICBMIDIzMi4zMTgyOCwxNzMuOTE4NzEgICBDIDIzMS4xMTgyOSwxNzMuMjc4NzIgMjI5LjgzODMsMTcyLjk1ODcyIDIyOC42MzgzMSwxNzIuOTU4NzIgICB6ICINCiAgICAgZmlsbD0icGFyYW0oZmlsbCkgIzAwMCINCiAgICAgZmlsbC1vcGFjaXR5PSJwYXJhbShmaWxsLW9wYWNpdHkpIg0KICAgICBzdHJva2U9InBhcmFtKG91dGxpbmUpICNGRkYiDQogICAgIHN0cm9rZS1vcGFjaXR5PSJwYXJhbShvdXRsaW5lLW9wYWNpdHkpIg0KICAgICBzdHJva2Utd2lkdGg9InBhcmFtKG91dGxpbmUtd2lkdGgpIDAiDQogICAgIGlua3NjYXBlOmNvbm5lY3Rvci1jdXJ2YXR1cmU9IjAiIC8+DQo8L3N2Zz4NCg==" name="name"/>
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
                      <Option type="QString" value="if(IniStatus is NULL, '#85b66f',if(IniStatus !='CLOSED', '#85b66f','#ff0f13'))" name="expression"/>
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
        <layer locked="0" id="{ab327f09-9545-4040-9e3c-dfe449a83bc2}" pass="0" class="SimpleLine" enabled="1">
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
      <text-style tabStopDistanceUnit="Point" textOrientation="horizontal" multilineHeight="1" blendMode="0" fontWordSpacing="0" multilineHeightUnit="Percentage" fontItalic="0" fontStrikeout="0" fontSize="8" fontWeight="50" fontSizeUnit="Point" fontUnderline="0" legendString="Aa" fontKerning="1" previewBkgrdColor="255,255,255,255,rgb:1,1,1,1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontFamily="Arial" fontLetterSpacing="0" forcedItalic="0" namedStyle="Normal" useSubstitutions="0" textColor="255,0,3,255,hsv:0.99833333333333329,1,1,1" tabStopDistance="80" forcedBold="0" capitalization="0" fieldName="Id" tabStopDistanceMapUnitScale="3x:0,0,0,0,0,0" isExpression="0" allowHtml="0" textOpacity="1">
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
                <Option type="QString" value="125,139,143,255,rgb:0.49019607843137253,0.54509803921568623,0.5607843137254902,1" name="color"/>
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
          <Option type="QString" value="&lt;symbol force_rhr=&quot;0&quot; frame_rate=&quot;10&quot; type=&quot;line&quot; is_animated=&quot;0&quot; name=&quot;symbol&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer locked=&quot;0&quot; id=&quot;{b676603d-f9bf-44f3-a25c-d6e1f565731c}&quot; pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;align_dash_pattern&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;square&quot; name=&quot;capstyle&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;5;2&quot; name=&quot;customdash&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;customdash_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;customdash_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;dash_pattern_offset&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;dash_pattern_offset_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;draw_inside_polygon&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;bevel&quot; name=&quot;joinstyle&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;60,60,60,255,rgb:0.23529411764705882,0.23529411764705882,0.23529411764705882,1&quot; name=&quot;line_color&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;solid&quot; name=&quot;line_style&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0.3&quot; name=&quot;line_width&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;line_width_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;offset&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;offset_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;offset_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;ring_filter&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_end&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_end_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_start&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_start_unit&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;use_custom_dash&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;width_map_unit_scale&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol"/>
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
      <Option type="List" name="dualview/previewExpressions">
        <Option type="QString" value="&quot;Id&quot;"/>
      </Option>
      <Option type="int" value="0" name="embeddedWidgets/count"/>
      <Option type="QString" value="qgisred_pumps" name="qgisred_identifier"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <fieldConfiguration>
    <field configurationFlags="NoFlag" name="Id"/>
    <field configurationFlags="NoFlag" name="IdHFCurve"/>
    <field configurationFlags="NoFlag" name="Power"/>
    <field configurationFlags="NoFlag" name="Speed"/>
    <field configurationFlags="NoFlag" name="IdSpeedPat"/>
    <field configurationFlags="NoFlag" name="IniStatus"/>
    <field configurationFlags="NoFlag" name="IdEffiCur"/>
    <field configurationFlags="NoFlag" name="EnergyPric"/>
    <field configurationFlags="NoFlag" name="IdPricePat"/>
    <field configurationFlags="NoFlag" name="Tag"/>
    <field configurationFlags="NoFlag" name="Descrip"/>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="Id" name=""/>
    <alias index="1" field="IdHFCurve" name=""/>
    <alias index="2" field="Power" name=""/>
    <alias index="3" field="Speed" name=""/>
    <alias index="4" field="IdSpeedPat" name=""/>
    <alias index="5" field="IniStatus" name=""/>
    <alias index="6" field="IdEffiCur" name=""/>
    <alias index="7" field="EnergyPric" name=""/>
    <alias index="8" field="IdPricePat" name=""/>
    <alias index="9" field="Tag" name=""/>
    <alias index="10" field="Descrip" name=""/>
  </aliases>
  <splitPolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="IdHFCurve" policy="Duplicate"/>
    <policy field="Power" policy="Duplicate"/>
    <policy field="Speed" policy="Duplicate"/>
    <policy field="IdSpeedPat" policy="Duplicate"/>
    <policy field="IniStatus" policy="Duplicate"/>
    <policy field="IdEffiCur" policy="Duplicate"/>
    <policy field="EnergyPric" policy="Duplicate"/>
    <policy field="IdPricePat" policy="Duplicate"/>
    <policy field="Tag" policy="Duplicate"/>
    <policy field="Descrip" policy="Duplicate"/>
  </splitPolicies>
  <duplicatePolicies>
    <policy field="Id" policy="Duplicate"/>
    <policy field="IdHFCurve" policy="Duplicate"/>
    <policy field="Power" policy="Duplicate"/>
    <policy field="Speed" policy="Duplicate"/>
    <policy field="IdSpeedPat" policy="Duplicate"/>
    <policy field="IniStatus" policy="Duplicate"/>
    <policy field="IdEffiCur" policy="Duplicate"/>
    <policy field="EnergyPric" policy="Duplicate"/>
    <policy field="IdPricePat" policy="Duplicate"/>
    <policy field="Tag" policy="Duplicate"/>
    <policy field="Descrip" policy="Duplicate"/>
  </duplicatePolicies>
  <defaults>
    <default applyOnUpdate="0" field="Id" expression=""/>
    <default applyOnUpdate="0" field="IdHFCurve" expression=""/>
    <default applyOnUpdate="0" field="Power" expression=""/>
    <default applyOnUpdate="0" field="Speed" expression=""/>
    <default applyOnUpdate="0" field="IdSpeedPat" expression=""/>
    <default applyOnUpdate="0" field="IniStatus" expression=""/>
    <default applyOnUpdate="0" field="IdEffiCur" expression=""/>
    <default applyOnUpdate="0" field="EnergyPric" expression=""/>
    <default applyOnUpdate="0" field="IdPricePat" expression=""/>
    <default applyOnUpdate="0" field="Tag" expression=""/>
    <default applyOnUpdate="0" field="Descrip" expression=""/>
  </defaults>
  <constraints>
    <constraint field="Id" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IdHFCurve" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Power" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Speed" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IdSpeedPat" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IniStatus" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IdEffiCur" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="EnergyPric" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="IdPricePat" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Tag" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
    <constraint field="Descrip" constraints="0" exp_strength="0" unique_strength="0" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="Id"/>
    <constraint desc="" exp="" field="IdHFCurve"/>
    <constraint desc="" exp="" field="Power"/>
    <constraint desc="" exp="" field="Speed"/>
    <constraint desc="" exp="" field="IdSpeedPat"/>
    <constraint desc="" exp="" field="IniStatus"/>
    <constraint desc="" exp="" field="IdEffiCur"/>
    <constraint desc="" exp="" field="EnergyPric"/>
    <constraint desc="" exp="" field="IdPricePat"/>
    <constraint desc="" exp="" field="Tag"/>
    <constraint desc="" exp="" field="Descrip"/>
  </constraintExpressions>
  <expressionfields/>
  <previewExpression>"Id"</previewExpression>
  <mapTip enabled="1">Pump [% "Id" %]</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
