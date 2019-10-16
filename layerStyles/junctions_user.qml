<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" readOnly="0" simplifyAlgorithm="0" labelsEnabled="0" simplifyLocal="1" version="3.8.0-Zanzibar" simplifyDrawingTol="1" maxScale="0" styleCategories="AllStyleCategories" simplifyDrawingHints="0" minScale="0" simplifyMaxScale="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" forceraster="0" type="singleSymbol" enableorderby="0">
    <symbols>
      <symbol force_rhr="0" clip_to_extent="1" name="0" type="marker" alpha="1">
        <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="21,21,21,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.5"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="Pixel"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="1.2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option value="true" name="active" type="bool"/>
                  <Option value="if( abs(&quot;BaseDem&quot;)&lt;1E-9, color_rgb(21,21,21),color_rgb(200,25,25))" name="expression" type="QString"/>
                  <Option value="3" name="type" type="int"/>
                </Option>
                <Option name="size" type="Map">
                  <Option value="true" name="active" type="bool"/>
                  <Option value="if( abs(&quot;BaseDem&quot;)&lt;1E-9, 1.2,2)" name="expression" type="QString"/>
                  <Option value="3" name="type" type="int"/>
                </Option>
              </Option>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory diagramOrientation="Up" penWidth="0" enabled="0" opacity="1" rotationOffset="270" scaleDependency="Area" maxScaleDenominator="0" backgroundColor="#ffffff" penColor="#000000" sizeType="MM" minimumSize="0" penAlpha="255" height="15" backgroundAlpha="255" labelPlacementMethod="XHeight" lineSizeType="MM" barWidth="5" minScaleDenominator="0" width="15" sizeScale="3x:0,0,0,0,0,0" scaleBasedVisibility="0" lineSizeScale="3x:0,0,0,0,0,0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="2" obstacle="0" placement="0" priority="0" dist="0" zIndex="0" showAll="1">
    <properties>
      <Option type="Map">
        <Option value="" name="name" type="QString"/>
        <Option name="properties"/>
        <Option value="collection" name="type" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="Id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Elevation">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BaseDem">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="IdPattDem">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="EmittCoef">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="IniQuality">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Tag">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Descrip">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="Id" index="0" name=""/>
    <alias field="Elevation" index="1" name=""/>
    <alias field="BaseDem" index="2" name=""/>
    <alias field="IdPattDem" index="3" name=""/>
    <alias field="EmittCoef" index="4" name=""/>
    <alias field="IniQuality" index="5" name=""/>
    <alias field="Tag" index="6" name=""/>
    <alias field="Descrip" index="7" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="Id" expression=""/>
    <default applyOnUpdate="0" field="Elevation" expression=""/>
    <default applyOnUpdate="0" field="BaseDem" expression=""/>
    <default applyOnUpdate="0" field="IdPattDem" expression=""/>
    <default applyOnUpdate="0" field="EmittCoef" expression=""/>
    <default applyOnUpdate="0" field="IniQuality" expression=""/>
    <default applyOnUpdate="0" field="Tag" expression=""/>
    <default applyOnUpdate="0" field="Descrip" expression=""/>
  </defaults>
  <constraints>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="Id"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="Elevation"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="BaseDem"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="IdPattDem"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="EmittCoef"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="IniQuality"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="Tag"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="Descrip"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="Id" exp=""/>
    <constraint desc="" field="Elevation" exp=""/>
    <constraint desc="" field="BaseDem" exp=""/>
    <constraint desc="" field="IdPattDem" exp=""/>
    <constraint desc="" field="EmittCoef" exp=""/>
    <constraint desc="" field="IniQuality" exp=""/>
    <constraint desc="" field="Tag" exp=""/>
    <constraint desc="" field="Descrip" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column hidden="0" width="-1" name="Id" type="field"/>
      <column hidden="0" width="-1" name="Elevation" type="field"/>
      <column hidden="0" width="-1" name="BaseDem" type="field"/>
      <column hidden="0" width="-1" name="IdPattDem" type="field"/>
      <column hidden="0" width="-1" name="EmittCoef" type="field"/>
      <column hidden="0" width="-1" name="IniQuality" type="field"/>
      <column hidden="0" width="-1" name="Tag" type="field"/>
      <column hidden="0" width="-1" name="Descrip" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- codificación: utf-8 -*-
"""
Los formularios de QGIS pueden tener una función de Python que
es llamada cuando se abre el formulario.

Use esta función para añadir lógica extra a sus formularios.

Introduzca el nombre de la función en el campo
"Python Init function".
Sigue un ejemplo:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="BaseDem" editable="1"/>
    <field name="Descrip" editable="1"/>
    <field name="Elevation" editable="1"/>
    <field name="EmittCoef" editable="1"/>
    <field name="Id" editable="1"/>
    <field name="IdPattDem" editable="1"/>
    <field name="IniQuality" editable="1"/>
    <field name="Tag" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="BaseDem" labelOnTop="0"/>
    <field name="Descrip" labelOnTop="0"/>
    <field name="Elevation" labelOnTop="0"/>
    <field name="EmittCoef" labelOnTop="0"/>
    <field name="Id" labelOnTop="0"/>
    <field name="IdPattDem" labelOnTop="0"/>
    <field name="IniQuality" labelOnTop="0"/>
    <field name="Tag" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>COALESCE( "Descrip", '&lt;NULL>' )</previewExpression>
  <mapTip>[Junction]&lt;br>
Id: [% "Id" %]</mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
