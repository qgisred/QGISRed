<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyDrawingTol="1" labelsEnabled="1" maxScale="0" autoRefreshMode="Disabled" minScale="0" simplifyLocal="1" symbologyReferenceScale="-1" simplifyAlgorithm="0" version="3.40.8-Bratislava" styleCategories="LayerConfiguration|Symbology|Labeling|MapTips|Rendering" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" autoRefreshTime="0" simplifyDrawingHints="0" readOnly="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <renderer-v2 symbollevels="0" enableorderby="0" referencescale="-1" type="singleSymbol" forceraster="0">
    <symbols>
      <symbol alpha="1" name="0" force_rhr="0" clip_to_extent="1" is_animated="0" type="marker" frame_rate="10">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SvgMarker" id="{519ba186-66dd-4341-936d-03a1a9a95b06}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterEnergy.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'EnergySensor', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{c29b594e-1c37-4398-a7fd-a6f989ec551e}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterOpen.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'ValveOpening', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{7a4a4f32-3cfd-4390-b887-7270152a3522}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterDiff.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'DifferentialManometer', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{005419a8-7a50-4ec1-ba23-379d5737b62a}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterStatus.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'StatusSensor', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{9df6412f-c5fa-4732-8b2f-ead9887269ee}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterTacho.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'Tachometer', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{f7265c70-79a9-41a6-aa7c-3a39c6fbf65c}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterCount.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'Countermeter', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{44176d16-88c4-482d-85fb-252cda2f6762}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,hsv:0.49783333333333335,0,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterFlow.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'Flowmeter', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{c8d8f575-704a-4fc5-b4d9-42368db70cd2}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterQuality.svg" type="QString"/>
            <Option name="offset" value="-0.40000000000000002,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'QualitySensor', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{eb03e5f6-93aa-4ef0-9e80-b360ba3430a4}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterLevel.svg" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.5" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 0, if (Type = 'LevelSensor', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer pass="0" class="SvgMarker" id="{70d71a40-912b-423e-be4a-9a51da407a63}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
            <Option name="fixedAspectRatio" value="0" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="name" value="C:/Users/fmart/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/QGISRed-BID/layerStyles/meterMan.svg" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_width" value="0.2" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="parameters"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="3" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="outlineColor" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if(IsActive is NULL, '#232323',if(IsActive !=0, '#232323','#999999'))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
                <Option name="width" type="Map">
                  <Option name="active" value="true" type="bool"/>
                  <Option name="expression" value="if (Type is NULL, 5, if (Type = 'Manometer', 5, 0))" type="QString"/>
                  <Option name="type" value="3" type="int"/>
                </Option>
              </Option>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
    <data-defined-properties>
      <Option type="Map">
        <Option name="name" value="" type="QString"/>
        <Option name="properties"/>
        <Option name="type" value="collection" type="QString"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol alpha="1" name="" force_rhr="0" clip_to_extent="1" is_animated="0" type="marker" frame_rate="10">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleMarker" id="{5c60aaec-2ceb-4cf1-8bac-a06b0a45bcbc}" enabled="1" locked="0">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="cap_style" value="square" type="QString"/>
            <Option name="color" value="255,0,0,255,rgb:1,0,0,1" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="name" value="circle" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
            <Option name="outline_style" value="solid" type="QString"/>
            <Option name="outline_width" value="0" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="2" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style tabStopDistance="80" fieldName="Id" textOpacity="1" useSubstitutions="0" forcedItalic="0" allowHtml="0" stretchFactor="100" namedStyle="Bold" fontFamily="Arial" fontSize="8" isExpression="0" multilineHeightUnit="Percentage" fontItalic="0" previewBkgrdColor="255,255,255,255,rgb:1,1,1,1" capitalization="0" fontUnderline="0" forcedBold="0" textOrientation="horizontal" fontWeight="75" fontLetterSpacing="0" textColor="237,109,215,255,hsv:0.86105555555555557,0.54044403753719383,0.92845044632639051,1" blendMode="0" legendString="Aa" multilineHeight="1" fontWordSpacing="0" tabStopDistanceMapUnitScale="3x:0,0,0,0,0,0" fontSizeUnit="Point" fontStrikeout="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontKerning="1" tabStopDistanceUnit="Point">
        <families/>
        <text-buffer bufferColor="250,250,250,255,rgb:0.98039215686274506,0.98039215686274506,0.98039215686274506,1" bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferJoinStyle="128" bufferNoFill="1" bufferOpacity="1" bufferDraw="0" bufferSize="1" bufferBlendMode="0"/>
        <text-mask maskOpacity="1" maskSize="1.5" maskSizeUnits="MM" maskEnabled="0" maskType="0" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskedSymbolLayers="" maskJoinStyle="128" maskSize2="1.5"/>
        <background shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeFillColor="255,255,255,255,rgb:1,1,1,1" shapeSVGFile="" shapeDraw="0" shapeOpacity="1" shapeBorderWidthUnit="Point" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeUnit="Point" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRotationType="0" shapeRadiiY="0" shapeBorderColor="128,128,128,255,rgb:0.50196078431372548,0.50196078431372548,0.50196078431372548,1" shapeRadiiX="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeBorderWidth="0" shapeOffsetUnit="Point" shapeType="0" shapeRotation="0" shapeOffsetY="0" shapeBlendMode="0" shapeSizeType="0" shapeJoinStyle="64" shapeRadiiUnit="Point" shapeSizeY="0">
          <symbol alpha="1" name="markerSymbol" force_rhr="0" clip_to_extent="1" is_animated="0" type="marker" frame_rate="10">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleMarker" id="" enabled="1" locked="0">
              <Option type="Map">
                <Option name="angle" value="0" type="QString"/>
                <Option name="cap_style" value="square" type="QString"/>
                <Option name="color" value="133,182,111,255,rgb:0.52156862745098043,0.71372549019607845,0.43529411764705883,1" type="QString"/>
                <Option name="horizontal_anchor_point" value="1" type="QString"/>
                <Option name="joinstyle" value="bevel" type="QString"/>
                <Option name="name" value="circle" type="QString"/>
                <Option name="offset" value="0,0" type="QString"/>
                <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="offset_unit" value="MM" type="QString"/>
                <Option name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" type="QString"/>
                <Option name="outline_style" value="solid" type="QString"/>
                <Option name="outline_width" value="0" type="QString"/>
                <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="outline_width_unit" value="MM" type="QString"/>
                <Option name="scale_method" value="diameter" type="QString"/>
                <Option name="size" value="2" type="QString"/>
                <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="size_unit" value="MM" type="QString"/>
                <Option name="vertical_anchor_point" value="1" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" value="" type="QString"/>
                  <Option name="properties"/>
                  <Option name="type" value="collection" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol alpha="1" name="fillSymbol" force_rhr="0" clip_to_extent="1" is_animated="0" type="fill" frame_rate="10">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
            <layer pass="0" class="SimpleFill" id="" enabled="1" locked="0">
              <Option type="Map">
                <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="color" value="255,255,255,255,rgb:1,1,1,1" type="QString"/>
                <Option name="joinstyle" value="bevel" type="QString"/>
                <Option name="offset" value="0,0" type="QString"/>
                <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
                <Option name="offset_unit" value="MM" type="QString"/>
                <Option name="outline_color" value="128,128,128,255,rgb:0.50196078431372548,0.50196078431372548,0.50196078431372548,1" type="QString"/>
                <Option name="outline_style" value="no" type="QString"/>
                <Option name="outline_width" value="0" type="QString"/>
                <Option name="outline_width_unit" value="Point" type="QString"/>
                <Option name="style" value="solid" type="QString"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" value="" type="QString"/>
                  <Option name="properties"/>
                  <Option name="type" value="collection" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowBlendMode="6" shadowRadius="1.5" shadowRadiusAlphaOnly="0" shadowDraw="0" shadowUnder="0" shadowColor="0,0,0,255,rgb:0,0,0,1" shadowOffsetDist="1" shadowOffsetUnit="MM" shadowOffsetGlobal="1" shadowOffsetAngle="135" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusUnit="MM" shadowOpacity="0.69999999999999996" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format rightDirectionSymbol=">" formatNumbers="0" reverseDirectionSymbol="0" addDirectionSymbol="0" multilineAlign="3" wrapChar="" leftDirectionSymbol="&lt;" useMaxLineLengthForAutoWrap="1" autoWrapLength="0" decimals="3" placeDirectionSymbol="0" plussign="0"/>
      <placement maximumDistanceUnit="MM" yOffset="0" centroidWhole="0" geometryGeneratorEnabled="0" overrunDistanceUnit="MM" overlapHandling="PreventOverlap" dist="0" rotationAngle="0" distUnits="MM" repeatDistance="0" centroidInside="0" polygonPlacementFlags="2" allowDegraded="0" priority="5" geometryGeneratorType="PointGeometry" xOffset="0" overrunDistance="0" maximumDistanceMapUnitScale="3x:0,0,0,0,0,0" placement="6" lineAnchorClipping="0" fitInPolygonOnly="0" repeatDistanceUnits="MM" preserveRotation="1" layerType="PointGeometry" lineAnchorPercent="0.5" maxCurvedCharAngleOut="-25" rotationUnit="AngleDegrees" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" geometryGenerator="" maximumDistance="0" lineAnchorType="0" offsetType="1" offsetUnits="MM" maxCurvedCharAngleIn="25" lineAnchorTextPoint="FollowPlacement" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" distMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" prioritization="PreferCloser" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR"/>
      <rendering maxNumLabels="2000" limitNumLabels="0" minFeatureSize="0" mergeLines="0" zIndex="0" upsidedownLabels="0" obstacleFactor="1" fontMaxPixelSize="10000" unplacedVisibility="0" fontLimitPixelSize="0" scaleMax="0" scaleVisibility="0" labelPerPart="0" drawLabels="1" scaleMin="0" obstacleType="1" fontMinPixelSize="3" obstacle="1"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" value="" type="QString"/>
          <Option name="properties"/>
          <Option name="type" value="collection" type="QString"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" value="pole_of_inaccessibility" type="QString"/>
          <Option name="blendMode" value="0" type="int"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
          <Option name="drawToAllParts" value="false" type="bool"/>
          <Option name="enabled" value="0" type="QString"/>
          <Option name="labelAnchorPoint" value="point_on_exterior" type="QString"/>
          <Option name="lineSymbol" value="&lt;symbol alpha=&quot;1&quot; name=&quot;symbol&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; is_animated=&quot;0&quot; type=&quot;line&quot; frame_rate=&quot;10&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; value=&quot;&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; value=&quot;collection&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer pass=&quot;0&quot; class=&quot;SimpleLine&quot; id=&quot;{afd23af8-0c5c-43c8-b191-edfa778ab827}&quot; enabled=&quot;1&quot; locked=&quot;0&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;align_dash_pattern&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;capstyle&quot; value=&quot;square&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;customdash&quot; value=&quot;5;2&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;customdash_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;customdash_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;dash_pattern_offset&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;dash_pattern_offset_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;dash_pattern_offset_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;draw_inside_polygon&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;joinstyle&quot; value=&quot;bevel&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_color&quot; value=&quot;60,60,60,255,rgb:0.23529411764705882,0.23529411764705882,0.23529411764705882,1&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_style&quot; value=&quot;solid&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_width&quot; value=&quot;0.3&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;line_width_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;offset&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;offset_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;offset_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;ring_filter&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_end&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_end_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_end_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_start&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_start_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;trim_distance_start_unit&quot; value=&quot;MM&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;tweak_dash_pattern_on_corners&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;use_custom_dash&quot; value=&quot;0&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;width_map_unit_scale&quot; value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; value=&quot;&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; value=&quot;collection&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString"/>
          <Option name="minLength" value="0" type="double"/>
          <Option name="minLengthMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="minLengthUnit" value="MM" type="QString"/>
          <Option name="offsetFromAnchor" value="0" type="double"/>
          <Option name="offsetFromAnchorMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="offsetFromAnchorUnit" value="MM" type="QString"/>
          <Option name="offsetFromLabel" value="0" type="double"/>
          <Option name="offsetFromLabelMapUnitScale" value="3x:0,0,0,0,0,0" type="QString"/>
          <Option name="offsetFromLabelUnit" value="MM" type="QString"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <previewExpression>"Descrip"</previewExpression>
  <mapTip enabled="1">[[% "Type" %]] [% "Id" %]</mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
