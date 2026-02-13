# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, pyqtSlot, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import (QDockWidget, QWidget, QHBoxLayout, QLabel, QToolButton, QMessageBox, QLineEdit,
                             QListWidgetItem, QTableWidgetItem, QHeaderView, QStyle, QAbstractItemView,
                             QFrame, QGridLayout, QSizePolicy, QScrollArea)
from qgis.PyQt import uic
from qgis.core import (QgsProject, QgsVectorLayer, QgsSettings, QgsGeometry, QgsPointXY,
                       QgsRectangle, QgsFeature, QgsLayerMetadata)
from qgis.utils import iface
from qgis.gui import QgsHighlight

# In your Spoiler class, add a new signal and a slot to emit the current state:
class Spoiler(QWidget):
    toggledState = pyqtSignal(bool)  # True: expanded, False: collapsed

    def __init__(self, parent=None, title='', animationDuration=10):
        super(Spoiler, self).__init__(parent)
        self.animationDuration = animationDuration

        # Create components
        self.toggleAnimation = QParallelAnimationGroup()
        self.contentArea = QScrollArea()
        self.headerLine = QFrame()
        self.toggleButton = QToolButton()
        self.mainLayout = QGridLayout()

        # Setup toggle button
        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.RightArrow)
        self.toggleButton.setText(title)
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(False)

        # Setup header line
        self.headerLine.setFrameShape(QFrame.HLine)
        self.headerLine.setFrameShadow(QFrame.Sunken)
        self.headerLine.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # Setup content area
        self.contentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)

        # Setup animations for collapsing/expanding
        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self.contentArea, b"maximumHeight"))

        # Connect finished signal to our custom slot
        self.toggleAnimation.finished.connect(self.onAnimationFinished)

        # Build layout
        self.mainLayout.setVerticalSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        row = 0
        self.mainLayout.addWidget(self.toggleButton, row, 0, 1, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.headerLine, row, 2, 1, 1)
        row += 1
        self.mainLayout.addWidget(self.contentArea, row, 0, 1, 3)
        self.setLayout(self.mainLayout)

        # Connect the toggle button to start the animation
        self.toggleButton.clicked.connect(self.startAnimation)

    def startAnimation(self, checked):
        arrow_type = Qt.DownArrow if checked else Qt.RightArrow
        self.toggleButton.setArrowType(arrow_type)
        direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
        self.toggleAnimation.setDirection(direction)
        self.toggleAnimation.start()

    def onAnimationFinished(self):
        # Once the animation is complete, emit the current state.
        self.toggledState.emit(self.toggleButton.isChecked())

    def setContentLayout(self, contentLayout):
        self.contentArea.setLayout(contentLayout)
        collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        contentHeight = contentLayout.sizeHint().height()
        for i in range(self.toggleAnimation.animationCount()-1):
            anim = self.toggleAnimation.animationAt(i)
            anim.setDuration(self.animationDuration)
            anim.setStartValue(collapsedHeight)
            anim.setEndValue(collapsedHeight + contentHeight)
        contentAnimation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount()-1)
        contentAnimation.setDuration(self.animationDuration)
        contentAnimation.setStartValue(0)
        contentAnimation.setEndValue(contentHeight)

    def setExpanded(self, expanded):
        """Programmatically expand or collapse the spoiler."""
        if self.toggleButton.isChecked() == expanded:
            return  # Already in desired state.
        self.toggleButton.setChecked(expanded)
        self.startAnimation(expanded)

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_unified_find_properties.ui"))

class QGISRedElementsExplorerDock(QDockWidget, FORM_CLASS):
    _instance = None
    dockVisibilityChanged = pyqtSignal(bool)
    findElementsDockVisibilityChanged = pyqtSignal(bool)
    elementPropertiesDockVisibilityChanged = pyqtSignal(bool)
    dockFocusChanged = pyqtSignal(bool)

    @classmethod
    def getInstance(cls, canvas, parent=None, show_find_elements=True, show_element_properties=True):
        print("Entering getInstance")
        if cls._instance is None:
            cls._instance = cls(canvas, parent, show_find_elements, show_element_properties)
        # else:
        #     if hasattr(cls._instance, 'frameElementProperties') and cls._instance.frameElementProperties is not None:
        #         if cls._instance.frameElementProperties.isVisible() != show_element_properties:
        #             cls._instance.frameElementProperties.setVisible(show_element_properties)
        #     if hasattr(cls._instance, 'frameFindElements') and cls._instance.frameFindElements is not None:
        #         if show_find_elements and not cls._instance.frameFindElements.isVisible():
        #             cls._instance.frameFindElements.setVisible(True)
        print("Exiting getInstance")
        return cls._instance

    def __init__(self, canvas, parent=None, show_find_elements=True, show_element_properties=True):
        print("Entering __init__")
        if self._instance is not None:
            raise Exception(f"{self.__class__.__name__} is a singleton! Use getInstance() instead.")
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)
        self.setupEventFilters() 
        self.setObjectName(self.__class__.__name__)
        self.setFloating(False)
        if parent:
            parent.addDockWidget(Qt.LeftDockWidgetArea, self)

        self.canvas = canvas
        self.find_elements_visible = show_find_elements
        self.element_properties_visible = show_element_properties

        # (Other initialization code such as element types, dictionaries, etc.)
        self.element_types = [
            self.tr('Pipes'),
            self.tr('Junctions'),
            self.tr('Multiple Demands'),
            self.tr('Reservoirs'),
            self.tr('Tanks'),
            self.tr('Pumps'),
            self.tr('Valves'),
            self.tr('Sources'),
            self.tr('Service Connections'),
            self.tr('Isolation Valves'),
            self.tr('Meters')
        ]
        
        self.element_identifiers = {
            'Pipes': 'qgisred_pipes', 
            'Junctions': 'qgisred_junctions',
            'Multiple Demands': 'qgisred_demands',
            'Reservoirs': 'qgisred_reservoirs',
            'Tanks': 'qgisred_tanks',
            'Pumps': 'qgisred_pumps',
            'Valves': 'qgisred_valves',
            'Sources': 'qgisred_sources',
            'Service Connections': 'qgisred_serviceconnections',
            'Isolation Valves': 'qgisred_isolationvalves',
            'Meters': 'qgisred_meters'
        }
        
        self.singular_forms = {
            self.tr("Pipes"): self.tr("Pipe"),
            self.tr("Junctions"): self.tr("Junction"),
            self.tr("Multiple Demands"): self.tr("Multiple Demand"),
            self.tr("Reservoirs"): self.tr("Reservoir"),
            self.tr("Tanks"): self.tr("Tank"),
            self.tr("Pumps"): self.tr("Pump"),
            self.tr("Valves"): self.tr("Valve"),
            self.tr("Sources"): self.tr("Source"),
            self.tr("Service Connections"): self.tr("Service Connection"),
            self.tr("Isolation Valves"): self.tr("Isolation Valve"),
            self.tr("Meters"): self.tr("Meter")
        }
        
        self.original_ids = []
        self.adjacent_highlights = []
        self.main_highlight = None
        self.current_selected_highlight = None
        self.dictOfElementIDs = {}
        self.currentLayer = None
        self.currentFeature = None
        
        self.link_layers = ["qgisred_pipes", "qgisred_pumps", "qgisred_valves"]
        self.node_layers = ["qgisred_reservoirs", "qgisred_tanks", "qgisred_junctions", 
                            "qgisred_sources", "qgisred_demands", "qgisred_meters", "qgisred_isolationvalves"]
        self.special_layers = ["qgisred_serviceconnections"]
        self.sources_and_demands = ["qgisred_sources", "qgisred_demands"]
        
        if hasattr(self, 'listWidget'):
            self.listWidget.installEventFilter(self)
        
        if hasattr(self, 'labelFoundElement'):
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            self.labelFoundElement.setFont(font)
            self.labelFoundElement.setWordWrap(True)
            self.labelFoundElement.setText("")
        
        # Replace the original frames with spoiler widgets:
        # --- For Find Elements ---
        if hasattr(self, 'frameFindElements'):
            parentLayout = self.frameFindElements.parentWidget().layout()
            if parentLayout:
                parentLayout.removeWidget(self.frameFindElements)
            # Create a spoiler widget with the title "Find Elements"
            self.spoilerFindElements = Spoiler(title="Find Elements by Id")
            # Transfer the existing layout from the original frame to the spoiler
            self.spoilerFindElements.setContentLayout(self.frameFindElements.layout())
            # Add the spoiler widget to the same parent layout
            if parentLayout:
                parentLayout.addWidget(self.spoilerFindElements)
            # Replace the reference with the spoiler widget
            self.frameFindElements = self.spoilerFindElements

        # --- For Element Properties ---
        if hasattr(self, 'frameElementProperties'):
            parentLayout = self.frameElementProperties.parentWidget().layout()
            if parentLayout:
                parentLayout.removeWidget(self.frameElementProperties)
            self.spoilerElementProperties = Spoiler(title="Element Properties")
            self.spoilerElementProperties.setContentLayout(self.frameElementProperties.layout())
            if parentLayout:
                parentLayout.addWidget(self.spoilerElementProperties)
            self.frameElementProperties = self.spoilerElementProperties

        self.trackSpoilerEvents()

        self.setDockStyle()
        self.setupConnections()
        
        if hasattr(self, 'initializeCustomLayerProperties'):
            self.initializeCustomLayerProperties()
        
        if hasattr(self, 'initializeElementTypes'):
            self.initializeElementTypes()

        self.placeConnectedElements()

        settings = QgsSettings()
        if settings.contains("QGISRed/ElementsExplorer/geometry"):
            self.restoreGeometry(settings.value("QGISRed/ElementsExplorer/geometry"))
        if settings.contains("QGISRed/ElementsExplorer/floating"):
            self.setFloating(settings.value("QGISRed/ElementsExplorer/floating", type=bool))
        print("Exiting __init__")

    def trackSpoilerEvents(self):
        self.spoilerFindElements.toggledState.connect(self.onSpoilerFindElementsToggled)
        self.spoilerElementProperties.toggledState.connect(self.onSpoilerElementPropertiesToggled)

    def onSpoilerFindElementsToggled(self, expanded):
        if expanded:
            print("spoilerFindElements expanded")
        else:
            print("spoilerFindElements collapsed")
        # You can add any additional behavior here.

    def onSpoilerElementPropertiesToggled(self, expanded):
        if expanded:
            #self.spoilerFindElements.setExpanded(False)
            print("spoilerElementProperties expanded")
        else:
            print("spoilerElementProperties collapsed")
        # Additional handling can be placed here.

    def setupEventFilters(self):
        print("Entering setupEventFilters")
        main_widget = self.widget()
        self.installEventFilterRecursive(main_widget)
        print("Exiting setupEventFilters")

    def installEventFilterRecursive(self, widget):
        print("Entering installEventFilterRecursive")
        if widget:
            widget.installEventFilter(self)
            for child in widget.children():
                if isinstance(child, QWidget):
                    self.installEventFilterRecursive(child)
        print("Exiting installEventFilterRecursive")

    # def eventFilter(self, obj, event):
    #     if event.type() == QEvent.FocusIn:
    #         if obj != self and self.isAncestorOf(obj):
    #             self.reestablishIdentifyTool()
    #             self.onLayerTreeChanged()
    #     return super(QGISRedElementsExplorerDock, self).eventFilter(obj, event)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            # Only process focus events from non-listWidget children
            if obj != self and self.isAncestorOf(obj):
                self.reestablishIdentifyTool()
                # if obj != self.listWidget:
                #     self.initializeElementTypes()  # Update element types
        return super(QGISRedElementsExplorerDock, self).eventFilter(obj, event)

    def reestablishIdentifyTool(self):
        print("Entering reestablishIdentifyTool")
        from ..tools.qgisred_identifyFeature import QGISRedIdentifyFeature
        
        current_tool = self.canvas.mapTool()
        if not isinstance(current_tool, QGISRedIdentifyFeature):
            self.dockFocusChanged.emit(True)
        print("Exiting reestablishIdentifyTool")

    def resizeToMinimumHeight(self):
        print("Entering resizeToMinimumHeight")
        self.layout().activate()
        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())
        print("Exiting resizeToMinimumHeight")

    def setDockStyle(self):
        print("Entering setDockStyle")
        #self.initFindElementsCustomTitleBar()
        #self.initElementPropertiesCustomTitleBar()

        icon_name = 'iconFindElements.png' if 'Find' in self.__class__.__name__ else 'iconElementsProperties.png'
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', icon_name)
        self.setWindowIcon(QIcon(icon_path))
        
        if hasattr(self, 'leElementMask'):
            search_icon = QIcon(os.path.join(os.path.dirname(__file__), '..', 'images', 'iconFilter.png'))
            self.leElementMask.addAction(search_icon, QLineEdit.LeadingPosition)
        
        if hasattr(self, 'cbElementType'):
            self.cbElementType.setStyleSheet("QComboBox { background-color: white; }")
        if hasattr(self, 'cbElementId'):
            self.cbElementId.setStyleSheet("QComboBox { background-color: white; }")

        self.tempHideOtherTabs()
        print("Exiting setDockStyle")

    def tempHideOtherTabs(self):
        print("Entering tempHideOtherTabs")
        self.tabWidget.setTabVisible(1, False)
        self.tabWidget.setTabVisible(2, False)
        self.tabWidget.setTabVisible(3, False)
        self.tabWidget.setTabVisible(4, False)
        print("Exiting tempHideOtherTabs")

    def clearAll(self):
        print("Entering clearAll")
        self.clearHighlights()
        self.clearAllLayerSelections()

        if hasattr(self, 'leElementMask'):
            self.leElementMask.clear()
        if hasattr(self, 'cbElementId') and self.cbElementId.count() > 0:
            self.cbElementId.setCurrentIndex(0)
        if hasattr(self, 'labelFoundElement'):
            self.labelFoundElement.setText("")
        if hasattr(self, 'listWidget'):
            self.listWidget.clear()
        if hasattr(self, 'dataTableWidget'):
            self.dataTableWidget.clear()
            self.setDataTableWidgetColumns()
        print("Exiting clearAll")

    def clearAllLayerSelections(self):
        print("Entering clearAllLayerSelections")
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()
        print("Exiting clearAllLayerSelections")

    def clearHighlights(self):
        print("Entering clearHighlights")
        if self.main_highlight:
            self.main_highlight.hide()
            self.main_highlight = None
        for h in self.adjacent_highlights:
            h.hide()
        self.adjacent_highlights.clear()
        if self.current_selected_highlight:
            self.current_selected_highlight.hide()
            self.current_selected_highlight = None

        canvas = iface.mapCanvas()
        scene = canvas.scene()
        for item in scene.items():
            if isinstance(item, QgsHighlight):
                item.hide()
                scene.removeItem(item)
                del item
        canvas.refresh()
        print("Exiting clearHighlights")
    
    def closeEvent(self, event):
        print("Entering closeEvent")
        self.dockVisibilityChanged.emit(False)
        settings = QgsSettings()
        settings.setValue("QGISRed/ElementsExplorer/geometry", self.saveGeometry())
        settings.setValue("QGISRed/ElementsExplorer/floating", self.isFloating())

        #Disconnect signals if available
        root = QgsProject.instance().layerTreeRoot()
        inputs_group = root.findGroup("Inputs")
        if inputs_group and hasattr(self, 'onLayerTreeChanged'):
            try:
                inputs_group.addedChildren.disconnect(self.onLayerTreeChanged)
                inputs_group.removedChildren.disconnect(self.onLayerTreeChanged)
                for layer_node in inputs_group.findLayers():
                    if hasattr(self, 'disconnectLayerSignals'):
                        self.disconnectLayerSignals(layer_node.layer())
            except Exception:
                pass
        
        self.clearHighlights()
        self.clearAllLayerSelections()
        super(self.__class__, self).closeEvent(event)
        print("Exiting closeEvent")

    def getCheckedInputGroupLayers(self):
        print("Entering getCheckedInputGroupLayers")
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            print("Exiting getCheckedInputGroupLayers")
            return []
        checked_layers = inputs_group.checkedLayers()
        ordered_layers = sorted(
            checked_layers,
            key=lambda lyr: self.element_types.index(lyr.name()) if lyr.name() in self.element_types else 999
        )
        print("Exiting getCheckedInputGroupLayers")
        return ordered_layers

    def onProjectClosed(self):
        print("Entering onProjectClosed")
        self.clearHighlights()
        self.clearAllLayerSelections()
        print("Exiting onProjectClosed")
    
    def onProjectChanged(self):
        print("Entering onProjectChanged")
        self.clearAll()
        self.onLayerTreeChanged()
        print("Exiting onProjectChanged")

    def connectLayerSignals(self, layer_node):
        print("Entering connectLayerSignals")
        try:
            layer_node.nameChanged.connect(self.onLayerTreeChanged)
            if layer_node.layer():
                layer = layer_node.layer()
                layer.dataChanged.connect(self.onLayerTreeChanged)
                layer.featureAdded.connect(self.updateElementIds)
                layer.featureDeleted.connect(self.updateElementIds)
                layer.visibilityChanged.connect(self.onLayerTreeChanged)
        except Exception:
            pass
        print("Exiting connectLayerSignals")

    def disconnectLayerSignals(self, layer):
        print("Entering disconnectLayerSignals")
        try:
            if hasattr(layer, 'nameChanged'):
                try:
                    layer.nameChanged.disconnect(self.onLayerTreeChanged)
                except Exception:
                    pass
            if hasattr(layer, 'dataChanged'):
                try:
                    layer.dataChanged.disconnect(self.onLayerTreeChanged)
                except Exception:
                    pass
            if hasattr(layer, 'visibilityChanged'):
                try:
                    layer.visibilityChanged.disconnect(self.onLayerTreeChanged)
                except Exception:
                    pass
        except Exception:
            pass
        print("Exiting disconnectLayerSignals")
    
    def onLayerTreeChanged(self):
        print("Entering onLayerTreeChanged")
        current_type = self.cbElementType.currentText()
        current_id = self.extractNodeId(self.cbElementId.currentText())
        self.initializeCustomLayerProperties()
        self.initializeElementTypes()
        type_index = self.cbElementType.findText(current_type)
        if type_index >= 0:
            self.cbElementType.setCurrentIndex(type_index)
            id_index = self.cbElementId.findText(current_id)
            if id_index >= 0:
                self.cbElementId.setCurrentIndex(id_index)
        print("Exiting onLayerTreeChanged")

    def initElementsExplorerCustomTitleBar(self):
        print("Entering initElementsExplorerCustomTitleBar")
        titleBar = QWidget(self)
        layout = QHBoxLayout(titleBar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.explorerTitleLabel = QLabel("Elements Explorer", titleBar)
        self.explorerTitleLabel.setStyleSheet("font-size: 10pt;")
        layout.addWidget(self.explorerTitleLabel)
        
        layout.addStretch()
        
        self.floatButton = QToolButton(titleBar)
        float_icon = self.style().standardIcon(QStyle.SP_TitleBarNormalButton)
        self.floatButton.setIcon(float_icon)
        self.floatButton.setToolTip("Toggle Floating")
        self.floatButton.clicked.connect(self.toggleFloating)
        layout.addWidget(self.floatButton)
        
        self.closeButton = QToolButton(titleBar)
        close_icon = self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
        self.closeButton.setIcon(close_icon)
        self.closeButton.setToolTip("Close")
        self.closeButton.clicked.connect(self.close)
        layout.addWidget(self.closeButton)
        
        self.setTitleBarWidget(titleBar)
        print("Exiting initElementsExplorerCustomTitleBar")

    def initFindElementsCustomTitleBar(self):
        print("Entering initFindElementsCustomTitleBar")
        titleBar = QWidget(self)
        layout = QHBoxLayout(titleBar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = QLabel("Find Elements by Id", titleBar)
        self.titleLabel.setStyleSheet("font-weight: bold; color: darkblue; font-size: 9pt;")
        layout.addWidget(self.titleLabel)
        layout.addStretch()

        # self.epButton = QToolButton(titleBar)
        # icon_ep = QIcon(os.path.join(os.path.dirname(__file__), '..', 'images', 'iconElementsProperties.png'))
        # self.epButton.setIcon(icon_ep)
        # self.epButton.setToolTip("Element Properties")
        # self.epButton.clicked.connect(self.toggleElementPropertiesDock)
        # self.epButton.setCheckable(True)
        #layout.addWidget(self.epButton)

        self.findElementsDock.setTitleBarWidget(titleBar)

        #self.epButton.setChecked(not self.frameElementProperties.isVisible())
        print("Exiting initFindElementsCustomTitleBar")
        
    def initElementPropertiesCustomTitleBar(self):
        print("Entering initElementPropertiesCustomTitleBar")
        titleBar = QWidget(self)
        layout = QHBoxLayout(titleBar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = QLabel(self.windowTitle(), titleBar)
        self.titleLabel.setStyleSheet("font-weight: bold; color: darkblue; font-size: 9pt;")
        self.titleLabel.setText("Element Properties")
        layout.addWidget(self.titleLabel)
        layout.addStretch()

        # self.findButton = QToolButton(titleBar)
        # icon_find = QIcon(os.path.join(os.path.dirname(__file__), '..', 'images', 'iconFindElements.png'))
        # self.findButton.setIcon(icon_find)
        # self.findButton.setToolTip("Find Elements by ID")
        # self.findButton.clicked.connect(self.toggleFindElementsDock)
        # self.findButton.setCheckable(True)
        #layout.addWidget(self.findButton)
        
        self.frameElementProperties.setTitleBarWidget(titleBar)

        #self.findButton.setChecked(not self.frameFindElements.isVisible())
        print("Exiting initElementPropertiesCustomTitleBar")

    @pyqtSlot()
    def toggleFindElementsDock(self):
        print("Entering toggleFindElementsDock")
        current_visibility = self.frameFindElements.isVisible()
        self.findElementsDockVisibilityChanged.emit(current_visibility)
        print("Exiting toggleFindElementsDock")

    @pyqtSlot()
    def toggleElementPropertiesDock(self):
        print("Entering toggleElementPropertiesDock")
        current_visibility = self.frameElementProperties.isVisible()
        self.elementPropertiesDockVisibilityChanged.emit(current_visibility)
        print("Exiting toggleElementPropertiesDock")

    @pyqtSlot()
    def openElementPropertiesDock(self):
        print("Entering openElementPropertiesDock")
        if not self._instance:
            self.setComponentVisibility(False, True)
        elif not self.element_properties_visible:
            self.setComponentVisibility(self.find_elements_visible, True)
        elif self.find_elements_visible and self.element_properties_visible:
            self.setComponentVisibility(True, False)
        else:
            self.close()
        print("Exiting openElementPropertiesDock")

    @pyqtSlot()
    def openFindElementsDock(self):
        print("Entering openFindElementsDock")
        if not self._instance:
            self.setComponentVisibility(True, False)
        elif not self.find_elements_visible:
            self.setComponentVisibility(True, self.element_properties_visible)
        elif self.find_elements_visible and not self.element_properties_visible:
            self.close()
        else:
            self.setComponentVisibility(False, True)
        print("Exiting openFindElementsDock")

    def toggleFindElementsDockVisibility(self):
        print("Entering toggleFindElementsDockVisibility")
        self.find_elements_visible = not self.find_elements_visible
        if self.find_elements_visible:
            self.frameFindElements.show()
        else:
            self.frameFindElements.hide()
        
        if not self.find_elements_visible and not self.element_properties_visible:
            self.close()
        else:
            self.placeConnectedElements()
        print("Exiting toggleFindElementsDockVisibility")

    def toggleElementPropertiesVisibility(self):
        print("Entering toggleElementPropertiesVisibility")
        self.element_properties_visible = not self.element_properties_visible
        if self.element_properties_visible:
            self.frameElementProperties.show()
        else:
            self.frameElementProperties.hide()
        
        if not self.find_elements_visible and not self.element_properties_visible:
            self.close()
        else:
            self.placeConnectedElements()
        print("Exiting toggleElementPropertiesVisibility")

    def removeConnectedElementsFromLayouts(self):
        ...
    
    def placeConnectedElements(self):
        ...

    def setComponentVisibility(self, show_find_elements, show_element_properties):
        print("Entering setComponentVisibility")
        self.find_elements_visible = show_find_elements
        self.element_properties_visible = show_element_properties
        
        self.findElementsDockVisibilityChanged.emit(show_find_elements)
        self.elementPropertiesDockVisibilityChanged.emit(show_element_properties)

        # self.findButton.setChecked(show_find_elements)
        # self.epButton.setChecked(show_element_properties)
        
        # self.frameFindElements.setVisible(show_find_elements)
        # self.frameElementProperties.setVisible(show_element_properties)
        
        self.placeConnectedElements()
        self.resizeToMinimumHeight() 

        # Close the dock only if both components are hidden and the dock is not floating
        if not show_find_elements and not show_element_properties and not self.isFloating():
            self.close()
        print("Exiting setComponentVisibility")

    def openIdentifyForFindDock(self):
        print("Entering openIdentifyForFindDock")
        from ..tools.qgisred_identifyFeature import QGISRedIdentifyFeature
        self.identifyTool = QGISRedIdentifyFeature(self.canvas, useFindDock=True)
        self.canvas.setMapTool(self.identifyTool)
        print("Exiting openIdentifyForFindDock")

    #------- Common Functions -----------------
    @pyqtSlot()
    def toggleFloating(self):
        print("Entering toggleFloating")
        self.setFloating(not self.isFloating())
        print("Exiting toggleFloating")

    def setupConnections(self):
        print("Entering setupConnections")
        self.cbElementType.currentIndexChanged.connect(self.updateElementIds)
        self.leElementMask.textChanged.connect(self.filterElementIds)
        self.btFind.clicked.connect(self.onFindButtonClicked)
        self.listWidget.itemClicked.connect(self.onListItemSingleClicked)
        self.listWidget.itemDoubleClicked.connect(self.onListItemDoubleClicked)
        self.btClear.clicked.connect(self.clearAll)
        self.cbElementId.currentIndexChanged.connect(self.onElementIdChanged)           
        self.btReload.clicked.connect(self.initializeElementTypes)

        project = QgsProject.instance()
        project.layersAdded.connect(self.onLayerTreeChanged)
        project.layersRemoved.connect(self.onLayerTreeChanged)
        project.readProject.connect(self.onProjectChanged)
        project.cleared.connect(self.onProjectChanged)

        root = project.layerTreeRoot()
        inputs_group = root.findGroup("Inputs")
        if inputs_group:
            inputs_group.addedChildren.connect(self.onLayerTreeChanged)
            inputs_group.removedChildren.connect(self.onLayerTreeChanged)
            for layer_node in inputs_group.findLayers():
                self.connectLayerSignals(layer_node)
        
        # self.frameFindElements.visibilityChanged.connect(self.onDockVisibilityChanged)
        # self.frameElementProperties.visibilityChanged.connect(self.onDockVisibilityChanged)
        print("Exiting setupConnections")

    @pyqtSlot(bool)
    def onDockVisibilityChanged(self, visible):
        if self.isFloating:
            return
        
        print("Entering onDockVisibilityChanged")
        find_dock_visible = self.frameFindElements.isVisible() 
        element_properties_visible = self.frameElementProperties.isVisible()

        if not find_dock_visible and not element_properties_visible:
            self.close()
            print("Exiting onDockVisibilityChanged")
            return
        
        self.setComponentVisibility(find_dock_visible, element_properties_visible)
        self.findElementsDockVisibilityChanged.emit(find_dock_visible)
        self.elementPropertiesDockVisibilityChanged.emit(element_properties_visible)
        self.resizeToMinimumHeight() 
        print("Exiting onDockVisibilityChanged")
        
    #------- Element Properties -----------------
    def populatedataTableWidget(self):
        print("Entering populatedataTableWidget")
        if not hasattr(self, 'dataTableWidget'):
            print("Exiting populatedataTableWidget")
            return
        
        self.dataTableWidget.clearContents()
        self.dataTableWidget.setShowGrid(False)
        self.dataTableWidget.setStyleSheet("QTableWidget::item { padding: 1px; }")
        
        self.dataTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        fields = self.currentLayer.fields()
        attributes = self.currentFeature.attributes()
        num_fields = len(fields)
        self.dataTableWidget.setRowCount(num_fields)
        self.setDataTableWidgetColumns()

        header = self.dataTableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStyleSheet("QHeaderView::section { font-weight: bold; }")
        
        self.dataTableWidget.verticalHeader().setDefaultSectionSize(20)
        
        total_width = self.dataTableWidget.viewport().width() + 20 
        self.dataTableWidget.setColumnWidth(0, total_width // 2)
        self.dataTableWidget.setColumnWidth(1, total_width // 2)
        
        self.dataTableWidget.verticalHeader().setVisible(False)
        
        for row, field in enumerate(fields):
            field_item = QTableWidgetItem(field.name())
            value_item = QTableWidgetItem(str(attributes[row]))
            self.dataTableWidget.setItem(row, 0, field_item)
            self.dataTableWidget.setItem(row, 1, value_item)
        print("Exiting populatedataTableWidget")

    def setDataTableWidgetColumns(self):
        self.dataTableWidget.setColumnCount(2)
        self.dataTableWidget.setHorizontalHeaderLabels(["Property", "Value"])
        
    def setupTabs(self, visible_tabs):
        print("Entering setupTabs")
        # The code for actually handling tabs is replaced with ...
        # but we maintain the prints for clarity
        # Currently does nothing but keep the placeholder.
        print("Exiting setupTabs")

    def handleJunctions(self, layer, feature, tabs):
        print("Entering handleJunctions")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleJunctions")

    def handlePipes(self, layer, feature, tabs):
        print("Entering handlePipes")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handlePipes")

    def handlePumps(self, layer, feature, tabs):
        print("Entering handlePumps")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handlePumps")

    def handleReservoirs(self, layer, feature, tabs):
        print("Entering handleReservoirs")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleReservoirs")

    def handleTanks(self, layer, feature, tabs):
        print("Entering handleTanks")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleTanks")

    def handleValves(self, layer, feature, tabs):
        print("Entering handleValves")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleValves")
    
    def handleMeters(self, layer, feature, tabs):
        print("Entering handleMeters")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleMeters")

    def handleIsolationValves(self, layer, feature, tabs):
        print("Entering handleIsolationValves")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleIsolationValves")

    def handleServiceConnections(self, layer, feature, tabs):
        print("Entering handleServiceConnections")
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
        print("Exiting handleServiceConnections")
    
    def findOverlappingFeatures(self, target_feature, search_identifier):
        print("Entering findOverlappingFeatures")
        overlapping_features = []
        target_geom = target_feature.geometry()
        
        for layer in self.getCheckedInputGroupLayers():
            if layer.customProperty("qgisred_identifier") == search_identifier:
                for feat in layer.getFeatures():
                    if target_geom.intersects(feat.geometry()):
                        overlapping_features.append(feat)
        print("Exiting findOverlappingFeatures")
        return overlapping_features
    
    def loadFeature(self, layer, feature, feature_id_text = ""):
        print("Entering loadFeature")
        if not layer or not feature:
            print("Exiting loadFeature")
            return

        self.currentLayer = layer
        self.currentFeature = feature
        layer.selectByIds([feature.id()])
        self.populatedataTableWidget()

        #base_title = feature_id_text #f"{self.singular_forms.get(layer.name(), layer.name())} {feature.attribute('Id')}"
        # suffix_source = ""
        # suffix_demand = ""

        # id_property = layer.customProperty("qgisred_identifier")
        # if id_property in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
        #     source_features = self.findOverlappingFeatures(feature, "qgisred_sources")
        #     if source_features:
        #         suffix_source = "(Source)"
        #         for src_feat in source_features:
        #             self.appendFeatureProperties(src_feat, "Source")
        #     if id_property == "qgisred_junctions":
        #         demand_features = self.findOverlappingFeatures(feature, "qgisred_demands")
        #         if demand_features:
        #             suffix_demand = "(Mult.Dem)"
        #             for dem_feat in demand_features:
        #                 self.appendFeatureProperties(dem_feat, "Mult.Dem")

        #self.labelFoundElement.setText(f"{base_title} {suffix_source}{suffix_demand}")
        self.labelFoundElement.setText(f"{feature_id_text}")
        
        self.labelFoundElement.setStyleSheet("font-weight: bold; font-size: 12pt;")
        print("Exiting loadFeature")

    def appendFeatureProperties(self, feature, label_suffix=""):
        print("Entering appendFeatureProperties")
        if not hasattr(self, 'dataTableWidget'):
            print("Exiting appendFeatureProperties")
            return
        fields = feature.fields()
        attributes = feature.attributes()
        current_row_count = self.dataTableWidget.rowCount()
        new_row_count = current_row_count + len(fields)
        self.dataTableWidget.setRowCount(new_row_count)
        for i, field in enumerate(fields):
            field_name = f"{field.name()} ({label_suffix})"
            field_item = QTableWidgetItem(field_name)
            value_item = QTableWidgetItem(str(attributes[i]))
            self.dataTableWidget.setItem(current_row_count + i, 0, field_item)
            self.dataTableWidget.setItem(current_row_count + i, 1, value_item)
        print("Exiting appendFeatureProperties")


    #------- Find Elements -----------------
    def initializeCustomLayerProperties(self):
        print("Entering initializeCustomLayerProperties")
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            print("Exiting initializeCustomLayerProperties")
            return
        for layer_node in inputs_group.findLayers():
            layer_name = layer_node.name()
            for element_type, identifier in self.element_identifiers.items():
                if layer_name == element_type:
                    layer_obj = layer_node.layer()
                    if not layer_obj:
                        continue
                    layer_obj.setCustomProperty("qgisred_identifier", identifier)
                    layer_metadata = QgsLayerMetadata()
                    layer_metadata.setIdentifier(identifier)
                    layer_obj.setMetadata(layer_metadata)
        print("Exiting initializeCustomLayerProperties")

    def initializeElementTypes(self):
        """
        Clears the element type combobox, adds the available element types,
        and builds the cache of element IDs for each type.
        """
        print("Entering initializeElementTypes")
        self.cbElementType.clear()
        available_types = self.getAvailableElementTypes()
        self.cbElementType.addItems(available_types)
        # Build (or rebuild) the cache of element IDs for each available type.
        self.initializeElementIdsCache()
        print("Exiting initializeElementTypes")


    def initializeElementIdsCache(self):
        """
        Precompute and cache the list of IDs for each available element type.
        This method creates a dictionary mapping each element type (as shown
        in the combobox) to a sorted list of unique IDs from its associated layer.
        """
        print("Entering initializeElementIdsCache")
        # self.dictOfElementIDs = {}
        # Use the available element types from the project
        available_types = self.getAvailableElementTypes()
        for element_type in available_types:
            layer = self.getLayerForElementType(element_type)
            ids = []
            if layer:
                for feature in layer.getFeatures():
                    id_val = self.getFeatureIdValue(feature, layer, True)
                    if id_val:
                        ids.append(id_val)
                self.dictOfElementIDs[element_type] = sorted(set(ids))
            else:
                self.dictOfElementIDs[element_type] = []
        print("Exiting initializeElementIdsCache")

    def setDefaultValue(self):
        print("Entering setDefaultValue")
        self.clearAll()

        pipes_layer = self.getLayerByIdentifier("qgisred_pipes")
        if not pipes_layer:
            print("Exiting setDefaultValue")
            return

        pipes_layer_name = pipes_layer.name()
        self.cbElementType.setCurrentText(pipes_layer_name)
        self.updateElementIds()
        print("Exiting setDefaultValue")

    @pyqtSlot(int)
    def onElementIdChanged(self, index):
        print("Entering onElementIdChanged")
        self.labelFoundElement.setText("")
        self.listWidget.clear()
        self.dataTableWidget.clear()
        self.setDataTableWidgetColumns()
        print("Exiting onElementIdChanged")

    @pyqtSlot()
    def onFindButtonClicked(self):
        print("Entering onFindButtonClicked")
        if self.listWidget.currentItem():
            self.onListItemDoubleClicked(self.listWidget.currentItem())
        else:
            self.findElement()
        print("Exiting onFindButtonClicked")

    @pyqtSlot()
    def findElement(self):
        print("Entering findElement")
        self.clearHighlights()
        self.clearAllLayerSelections()
        self.listWidget.clear()

        selected_type = self.cbElementType.currentText()
        selected_id = self.extractNodeId(self.cbElementId.currentText())
        element_identifier = self.element_identifiers.get(selected_type)

        if not selected_id:
            self.labelFoundElement.setText("")
            print("Exiting findElement")
            return

        layer = self.getLayerForElementType(selected_type)
        found_feature = None
        found_feature_layer = None

        if layer:
            if layer.customProperty("qgisred_identifier") in self.sources_and_demands:
                found_feature, found_feature_layer = self.findSourceOrDemandForNodeId(selected_id)
            else:
                for feature in layer.getFeatures():
                    if self.getFeatureIdValue(feature, layer) == selected_id:
                        found_feature = feature
                        found_feature_layer = layer
                        break

        if not found_feature:
            QMessageBox.information(self, self.tr("Info"), self.tr("Feature not found"))
            print("Exiting findElement")
            return

        self.currentLayer = found_feature_layer
        self.currentFeature = found_feature

        finalTitleText = self.updateFoundElementLabel(selected_id, found_feature_layer)
        highlight = QgsHighlight(iface.mapCanvas(), found_feature.geometry(), layer)
        highlight.setColor(QColor("red"))
        highlight.setWidth(5)
        highlight.show()
        self.main_highlight = highlight
        self.adjustMapView(found_feature)

        identifier = layer.customProperty("qgisred_identifier")
        if self.isLineElement(layer):
            self.findAdjacentNodesByGeometry(found_feature)
        elif identifier == "qgisred_meters":
            self.findMeterAdjacency(found_feature, layer)
        elif identifier == "qgisred_isolationvalves":
            self.findIsolationValveAdjacency(found_feature, layer)
        elif identifier == "qgisred_serviceconnections":
            self.findServiceConnectionAdjacency(found_feature, layer)
        else:
            self.findAdjacentLinksByGeometry(found_feature, layer)
        self.sortListWidgetItems()
        self.loadFeature(layer, found_feature, finalTitleText)
        print("Exiting findElement")

    @pyqtSlot()
    def updateElementIds(self):
        """
        Updates the element ID combobox based on the currently selected element type.
        Instead of iterating over the layer's features each time, it retrieves the IDs
        from the precomputed cache.
        """
        print("Entering updateElementIds")
        self.cbElementId.clear()
        self.labelFoundElement.setText("")
        
        selected_type = self.cbElementType.currentText()
        # Retrieve the cached list of IDs for the selected element type.
        ids = self.dictOfElementIDs.get(selected_type, [])
        
        # Check if a filter mask is applied.
        mask = self.leElementMask.text().strip()
        if mask:
            filtered_ids = [id for id in ids if mask.lower() in id.lower()]
            self.cbElementId.addItems(filtered_ids)
        else:
            self.cbElementId.addItems(ids)
        print("Exiting updateElementIds")


    @pyqtSlot()
    def filterElementIds(self):
        """
        Filters the element IDs shown in the combobox based on the text entered in the mask.
        The filtering is done on the cached list of IDs for the current element type.
        """
        print("Entering filterElementIds")
        mask = self.leElementMask.text().strip()
        self.cbElementId.clear()
        selected_type = self.cbElementType.currentText()
        # Retrieve the cached list of IDs for filtering.
        ids = self.dictOfElementIDs.get(selected_type, [])
        if mask:
            filtered_ids = [id for id in ids if mask.lower() in id.lower()]
        else:
            filtered_ids = ids
        self.cbElementId.addItems(filtered_ids)
        print("Exiting filterElementIds")


    def onListItemSingleClicked(self, item):
        print("Entering onListItemSingleClicked")
        if self.current_selected_highlight:
            self.current_selected_highlight.hide()
            self.current_selected_highlight = None

        singular_type, selected_id, _ = self.extractTypeAndId(item.text())
        if not singular_type or not selected_id:
            print("Exiting onListItemSingleClicked")
            return

        element_identifier = None
        for plural, singular in self.singular_forms.items():
            if singular == singular_type:
                element_identifier = self.element_identifiers.get(plural)
                break
        if not element_identifier:
            element_identifier = self.getIdentifierFromLayerName(singular_type)

        matching_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == element_identifier
        ]
        for layer in matching_layers:
            for feature in layer.getFeatures():
                if self.getFeatureIdValue(feature, layer) == selected_id:
                    highlight = QgsHighlight(iface.mapCanvas(), feature.geometry(), layer)
                    highlight.setColor(QColor("orange"))
                    highlight.setWidth(5)
                    highlight.show()
                    self.current_selected_highlight = highlight
                    print("Exiting onListItemSingleClicked")
                    return
        print("Exiting onListItemSingleClicked")

    def onListItemDoubleClicked(self, item):
        print("Entering onListItemDoubleClicked")
        item_text = item.text()
        self.leElementMask.clear()
        singular_type, selected_id, full_id = self.extractTypeAndId(item_text)
        if not singular_type or not selected_id:
            print("Exiting onListItemDoubleClicked")
            return
        element_type = None
        for plural, singular in self.singular_forms.items():
            if singular == singular_type:
                element_type = plural
                break
        if not element_type:
            element_type = singular_type
        self.cbElementType.setCurrentText(element_type)
        index = self.cbElementId.findText(full_id)
        if index >= 0:
            self.cbElementId.setCurrentIndex(index)
        self.findElement()
        print("Exiting onListItemDoubleClicked")
    
    def adjustMapView(self, feature):
        print("Entering adjustMapView")
        canvas = iface.mapCanvas()
        current_extent = canvas.extent()
        geom = feature.geometry()
        feature_extent = geom.boundingBox()
        map_width = current_extent.width()
        map_height = current_extent.height()
        feat_width = feature_extent.width()
        feat_height = feature_extent.height()
        is_point = (feat_width == 0 and feat_height == 0)
        feat_largest_dim = max(feat_width, feat_height)
        map_largest_dim = max(map_width, map_height)
        ratio = feat_largest_dim / map_largest_dim if map_largest_dim != 0 else 1
        center = feature_extent.center()
        if not is_point:
            if ratio > 0.25:
                factor = ratio / 0.25
                new_width = map_width * factor
                new_height = map_height * factor
                new_extent = self.recenterExtent(new_width, new_height, center.x(), center.y())
            elif ratio < 0.05:
                factor = 0.05 / ratio
                new_width = map_width / factor
                new_height = map_height / factor
                new_extent = self.recenterExtent(new_width, new_height, center.x(), center.y())
            else:
                new_extent = QgsRectangle(current_extent)
        else:
            new_extent = QgsRectangle(current_extent)
        new_extent = self.applyMinimalPan(new_extent, feature_extent)
        canvas.setExtent(new_extent)
        canvas.refresh()
        print("Exiting adjustMapView")
    
    def recenterExtent(self, new_width, new_height, center_x, center_y):
        print("Entering recenterExtent")
        half_w = new_width / 2.0
        half_h = new_height / 2.0
        rect = QgsRectangle(center_x - half_w, center_y - half_h, center_x + half_w, center_y + half_h)
        print("Exiting recenterExtent")
        return rect

    def applyMinimalPan(self, current_extent, feature_extent):
        print("Entering applyMinimalPan")
        margin_x = current_extent.width() * 0.1
        margin_y = current_extent.height() * 0.1
        left_dist = feature_extent.xMinimum() - current_extent.xMinimum()
        right_dist = current_extent.xMaximum() - feature_extent.xMaximum()
        top_dist = current_extent.yMaximum() - feature_extent.yMaximum()
        bottom_dist = feature_extent.yMinimum() - current_extent.yMinimum()
        new_extent = QgsRectangle(current_extent)
        if left_dist < margin_x:
            shift = margin_x - left_dist
            new_extent.setXMinimum(new_extent.xMinimum() - shift)
            new_extent.setXMaximum(new_extent.xMaximum() - shift)
        if right_dist < margin_x:
            shift = margin_x - right_dist
            new_extent.setXMinimum(new_extent.xMinimum() + shift)
            new_extent.setXMaximum(new_extent.xMaximum() + shift)
        if top_dist < margin_y:
            shift = margin_y - top_dist
            new_extent.setYMinimum(new_extent.yMinimum() + shift)
            new_extent.setYMaximum(new_extent.yMaximum() + shift)
        if bottom_dist < margin_y:
            shift = margin_y - bottom_dist
            new_extent.setYMinimum(new_extent.yMinimum() - shift)
            new_extent.setYMaximum(new_extent.yMaximum() - shift)
        print("Exiting applyMinimalPan")
        return new_extent

    def getAvailableElementTypes(self):
        print("Entering getAvailableElementTypes")
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            print("Exiting getAvailableElementTypes")
            return []
        available_types = []
        checked_layers = inputs_group.checkedLayers()
        for element, identifier in self.element_identifiers.items():
            for layer in checked_layers:
                if layer and layer.customProperty("qgisred_identifier") == identifier:
                    available_types.append(layer.name())
                    break
        print("Exiting getAvailableElementTypes")
        return available_types

    def getLayerForElementType(self, element_type):
        print("Entering getLayerForElementType")
        project = QgsProject.instance()
        layers = project.mapLayersByName(element_type)
        layer_found = layers[0] if layers else None
        print("Exiting getLayerForElementType")
        return layer_found

    def getLayerByIdentifier(self, identifier):
        print("Entering getLayerByIdentifier")
        for layer in self.getCheckedInputGroupLayers():
            if layer.customProperty("qgisred_identifier") == identifier:
                print("Exiting getLayerByIdentifier")
                return layer
        print("Exiting getLayerByIdentifier")
        return None

    def getFeatureIdValue(self, feature, layer, special_naming=False):
        print("Entering getFeatureIdValue")
        if not layer:
            print("Exiting getFeatureIdValue")
            return "Id"
        identifier = layer.customProperty("qgisred_identifier")
        if identifier in self.sources_and_demands:
            node_feature, node_layer = self.findOverlappedNode(feature, layer, supported_only=True)
            if node_feature:
                node_id = self.extractNodeId(node_feature.attribute("Id"))
                if special_naming:
                    singular = self.singular_forms.get(node_layer.name(), node_layer.name())
                    suffix = "(Source)" if identifier == "qgisred_sources" else "(Mult.Dem)"
                    print("Exiting getFeatureIdValue")
                    return f"{singular} {node_id} {suffix}"
                print("Exiting getFeatureIdValue")
                return str(node_id)
            print("Exiting getFeatureIdValue")
            return ""
        else:
            value = feature.attribute("Id")
            id_str = str(value) if value is not None else ""
            if special_naming and identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                suffixes = []
                source_layer = self.getLayerByIdentifier("qgisred_sources")
                if source_layer:
                    for src_feat in source_layer.getFeatures():
                        if self.areOverlappedPoints(feature.geometry(), src_feat.geometry()):
                            suffixes.append("(Source)")
                            break
                if identifier == "qgisred_junctions":
                    demand_layer = self.getLayerByIdentifier("qgisred_demands")
                    if demand_layer:
                        for dmnd_feat in demand_layer.getFeatures():
                            if self.areOverlappedPoints(feature.geometry(), dmnd_feat.geometry()):
                                suffixes.append("(Mult.Dem)")
                                break
                if suffixes:
                    id_str += " " + " ".join(suffixes)
            print("Exiting getFeatureIdValue")
            return id_str

    def extractNodeId(self, text):
        print("Entering extractNodeId")
        text = text.replace(" (Source)", "").replace(" (Mult.Dem)", "")
        parts = text.strip().split()
        result = parts[-1] if len(parts) > 1 else text
        print("Exiting extractNodeId")
        return result

    def extractTypeAndId(self, text):
        print("Entering extractTypeAndId")
        original_text = text.strip()
        text_clean = original_text.replace(" (Source)", "").replace(" (Mult.Dem)", "").strip()
        sorted_singulars = sorted(self.singular_forms.values(), key=len, reverse=True)
        for singular in sorted_singulars:
            if text_clean.startswith(singular + " "):
                selected_id = text_clean[len(singular):].strip()
                full_id = original_text[len(singular):].strip() if original_text.startswith(singular + " ") else selected_id
                print("Exiting extractTypeAndId")
                return singular, selected_id, full_id
        parts = text_clean.split(" ", 1)
        if len(parts) < 2:
            print("Exiting extractTypeAndId")
            return None, None, None
        singular = parts[0]
        selected_id = parts[1].strip()
        full_id = original_text[len(singular):].strip() if original_text.startswith(singular + " ") else selected_id
        print("Exiting extractTypeAndId")
        return singular, selected_id, full_id

    def getIdentifierFromLayerName(self, layer_name):
        print("Entering getIdentifierFromLayerName")
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if layers:
            result = layers[0].customProperty("qgisred_identifier", None)
            print("Exiting getIdentifierFromLayerName")
            return result
        print("Exiting getIdentifierFromLayerName")
        return None

    def areOverlappedPoints(self, point1, point2, tolerance=1e-9):
        # This is a simple distance check; no prints inside to avoid spam for each feature
        return point1.distance(point2) < tolerance

    def updateFoundElementLabel(self, selected_id, layer=None):
        print("Entering updateFoundElementLabel")
        
        if not selected_id:
            self.labelFoundElement.setText("")
            print("Exiting updateFoundElementLabel")
            return

        if layer and layer.customProperty("qgisred_identifier") in self.sources_and_demands:
            node_layer, node_feat = self.findNodeLayer(selected_id)
        elif layer:
            node_feat = None
            for feat in layer.getFeatures():
                if self.getFeatureIdValue(feat, layer) == selected_id:
                    node_feat = feat
                    break
            node_layer = layer if node_feat else None
        else:
            node_layer, node_feat = self.findNodeLayer(selected_id)

        if node_layer and node_feat:
            suffixes = []
            node_identifier = node_layer.customProperty("qgisred_identifier", "")
            if node_identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                source_layer = self.getLayerByIdentifier("qgisred_sources")
                if source_layer:
                    for src_feat in source_layer.getFeatures():
                        if (not src_feat.geometry().isEmpty() and
                            self.areOverlappedPoints(node_feat.geometry(), src_feat.geometry())):
                            suffixes.append("(Source)")
                            break
            if node_identifier == "qgisred_junctions":
                demand_layer = self.getLayerByIdentifier("qgisred_demands")
                if demand_layer:
                    for dmnd_feat in demand_layer.getFeatures():
                        if (not dmnd_feat.geometry().isEmpty() and
                            self.areOverlappedPoints(node_feat.geometry(), dmnd_feat.geometry())):
                            suffixes.append("(Mult.Dem)")
                            break
            singular_node_type = self.singular_forms.get(node_layer.name(), node_layer.name())
            suffix_str = " ".join(suffixes)
            finalText = self.tr(f"{singular_node_type} {selected_id} {suffix_str}".strip())
            self.labelFoundElement.setText(finalText)
        else:
            element_type = self.cbElementType.currentText()
            singular_element_type = self.singular_forms.get(element_type, element_type)
            finalText = self.tr(f"{singular_element_type} {selected_id}")
            self.labelFoundElement.setText(finalText)

        return finalText
        print("Exiting updateFoundElementLabel")

    def findNodeLayer(self, node_id):
        print("Entering findNodeLayer")
        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in self.node_layers:
                if identifier in self.sources_and_demands:
                    continue
                for feature in layer.getFeatures():
                    if self.getFeatureIdValue(feature, layer) == node_id:
                        print("Exiting findNodeLayer")
                        return layer, feature
        print("Exiting findNodeLayer")
        return None, None

    def findOverlappedNode(self, point_feature, current_layer, supported_only=False):
        print("Entering findOverlappedNode")
        feature_geom = point_feature.geometry()
        if feature_geom.isEmpty():
            print("Exiting findOverlappedNode")
            return None, None
        feature_point = feature_geom.asPoint()
        feature_point_geom = QgsGeometry.fromPointXY(feature_point)
        tolerance = 1e-6
        if supported_only:
            supported_ids = ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]
            for node_layer in self.getCheckedInputGroupLayers():
                if node_layer == current_layer:
                    continue
                node_identifier = node_layer.customProperty("qgisred_identifier", "")
                if node_identifier not in supported_ids:
                    continue
                for node_feature in node_layer.getFeatures():
                    node_geom = node_feature.geometry()
                    if node_geom.isEmpty():
                        continue
                    node_point_geom = QgsGeometry.fromPointXY(node_geom.asPoint())
                    if self.areOverlappedPoints(feature_point_geom, node_point_geom):
                        print("Exiting findOverlappedNode")
                        return node_feature, node_layer
            print("Exiting findOverlappedNode")
            return None, None
        else:
            for node_layer in self.getCheckedInputGroupLayers():
                if node_layer == current_layer:
                    continue
                node_identifier = node_layer.customProperty("qgisred_identifier", "")
                if node_identifier in self.node_layers and node_identifier not in self.sources_and_demands:
                    for node_feature in node_layer.getFeatures():
                        node_geom = node_feature.geometry()
                        if node_geom.isEmpty():
                            continue
                        node_point_geom = QgsGeometry.fromPointXY(node_geom.asPoint())
                        if self.areOverlappedPoints(feature_point_geom, node_point_geom):
                            print("Exiting findOverlappedNode")
                            return node_feature, node_layer
            print("Exiting findOverlappedNode")
            return None, None

    def findSourceOrDemandForNodeId(self, node_id):
        print("Entering findSourceOrDemandForNodeId")
        node_layer, node_feat = self.findNodeLayer(node_id)
        if not node_layer or not node_feat:
            print("Exiting findSourceOrDemandForNodeId")
            return None, None 
        node_geom = node_feat.geometry()
        if node_geom.isEmpty():
            print("Exiting findSourceOrDemandForNodeId")
            return None, None 
        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in self.sources_and_demands: 
                for feat in layer.getFeatures():
                    feat_geom = feat.geometry()
                    if feat_geom.isEmpty():
                        continue
                    if self.areOverlappedPoints(node_geom, feat_geom):
                        print("Exiting findSourceOrDemandForNodeId")
                        return feat, layer
        print("Exiting findSourceOrDemandForNodeId")
        return None, None

    def isLineElement(self, layer):
        print("Entering isLineElement")
        result = layer.customProperty("qgisred_identifier") in self.link_layers
        print("Exiting isLineElement")
        return result

    def addAdjacencyItem(self, item_text, identifier):
        print("Entering addAdjacencyItem")
        new_item = QListWidgetItem(self.tr(item_text))
        new_item.setData(Qt.UserRole, identifier)
        self.listWidget.addItem(new_item)
        print("Exiting addAdjacencyItem")

    def sortListWidgetItems(self):
        print("Entering sortListWidgetItems")
        items = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            items.append((item.text(), item.data(Qt.UserRole)))
        self.listWidget.clear()

        def sort_key(entry):
            _, iden = entry
            try:
                return list(self.element_identifiers.values()).index(iden)
            except ValueError:
                return len(self.element_identifiers)
        for text, identifier in sorted(items, key=sort_key):
            new_item = QListWidgetItem(text)
            new_item.setData(Qt.UserRole, identifier)
            self.listWidget.addItem(new_item)
        print("Exiting sortListWidgetItems")

    def addServiceConnectionAdjacencies(self, current_geom, tolerance):
        print("Entering addServiceConnectionAdjacencies")
        service_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == "qgisred_serviceconnections"
        ]
        for layer in service_layers:
            for feat in layer.getFeatures():
                service_geom = feat.geometry()
                if service_geom.isEmpty():
                    continue
                if current_geom.intersects(service_geom) or current_geom.distance(service_geom) < tolerance:
                    service_id = self.getFeatureIdValue(feat, layer)
                    singular = self.singular_forms.get(layer.name(), layer.name())
                    self.addAdjacencyItem(f"{singular} {service_id}", layer.customProperty("qgisred_identifier"))
        print("Exiting addServiceConnectionAdjacencies")

    def addIsolationValveAdjacencies(self, current_geom, tolerance):
        print("Entering addIsolationValveAdjacencies")
        isolation_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == "qgisred_isolationvalves"
        ]
        for layer in isolation_layers:
            for feat in layer.getFeatures():
                iso_geom = feat.geometry()
                if iso_geom.isEmpty():
                    continue
                if current_geom.intersects(iso_geom) or current_geom.distance(iso_geom) < tolerance:
                    iso_id = self.getFeatureIdValue(feat, layer)
                    singular = self.singular_forms.get(layer.name(), layer.name())
                    self.addAdjacencyItem(f"{singular} {iso_id}", layer.customProperty("qgisred_identifier"))
        print("Exiting addIsolationValveAdjacencies")

    def findAdjacentNodesByGeometry(self, line_feature):
        print("Entering findAdjacentNodesByGeometry")
        geom = line_feature.geometry()
        if geom.isEmpty():
            print("Exiting findAdjacentNodesByGeometry")
            return
        if geom.isMultipart():
            parts = geom.asMultiPolyline()
            line_points = parts[0] if parts else []
        else:
            line_points = geom.asPolyline()
        if not line_points:
            print("Exiting findAdjacentNodesByGeometry")
            return
        line_geom = QgsGeometry.fromPolylineXY(line_points)
        tolerance = 1e-6
        found_nodes = []
        node_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") in (self.node_layers + self.special_layers)
        ]
        for node_layer in node_layers:
            if node_layer.geometryType() != 0:
                continue
            identifier = node_layer.customProperty("qgisred_identifier", "")
            if identifier in self.sources_and_demands:
                continue
            for f in node_layer.getFeatures():
                node_geom = f.geometry()
                if node_geom.isEmpty():
                    continue
                if line_geom.distance(node_geom) < tolerance:
                    node_id = self.getFeatureIdValue(f, node_layer)
                    layer_name = node_layer.name()
                    singular = self.singular_forms.get(layer_name, layer_name)
                    node_suffixes = []
                    if identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                        source_layer = self.getLayerByIdentifier("qgisred_sources")
                        if source_layer:
                            for src_feat in source_layer.getFeatures():
                                if self.areOverlappedPoints(node_geom, src_feat.geometry()):
                                    node_suffixes.append("(Source)")
                                    break
                        if identifier == "qgisred_junctions":
                            demand_layer = self.getLayerByIdentifier("qgisred_demands")
                            if demand_layer:
                                for dmnd_feat in demand_layer.getFeatures():
                                    if self.areOverlappedPoints(node_geom, dmnd_feat.geometry()):
                                        node_suffixes.append("(Mult.Dem)")
                                        break
                    suffix_str = " " + " ".join(node_suffixes) if node_suffixes else ""
                    node_info = f"{singular} {node_id}{suffix_str}"
                    found_nodes.append((node_layer, f, node_info))
        for node_layer, f, node_info in found_nodes:
            self.addAdjacencyItem(node_info, node_layer.customProperty("qgisred_identifier", ""))
        self.addServiceConnectionAdjacencies(line_geom, tolerance)
        print("Exiting findAdjacentNodesByGeometry")

    def findAdjacentLinksByGeometry(self, node_feature, layer):
        print("Entering findAdjacentLinksByGeometry")
        node_geom = node_feature.geometry()
        if node_geom.isEmpty():
            print("Exiting findAdjacentLinksByGeometry")
            return
        node_point = QgsPointXY(node_geom.asPoint())
        node_g = QgsGeometry.fromPointXY(node_point)
        tolerance = 1e-9
        found_links = []
        link_layers = [
            lyr for lyr in self.getCheckedInputGroupLayers()
            if lyr.customProperty("qgisred_identifier") in (self.link_layers + ["qgisred_meters"])
        ]
        for link_layer in link_layers:
            ident = link_layer.customProperty("qgisred_identifier", "")
            if ident in self.link_layers:
                if link_layer.geometryType() != 1:
                    continue
                for f in link_layer.getFeatures():
                    link_geom = f.geometry()
                    if link_geom.isMultipart():
                        parts = link_geom.asMultiPolyline()
                        line_points = parts[0] if parts else []
                    else:
                        line_points = link_geom.asPolyline()
                    if not line_points:
                        continue
                    if (node_g.distance(link_geom) < tolerance or
                        self.areOverlappedPoints(node_g, QgsGeometry.fromPointXY(line_points[0])) or
                        self.areOverlappedPoints(node_g, QgsGeometry.fromPointXY(line_points[-1]))):
                        link_id = self.getFeatureIdValue(f, link_layer)
                        layer_name = link_layer.name()
                        singular = self.singular_forms.get(layer_name, layer_name)
                        found_links.append((link_layer, f, f"{singular} {link_id}"))
            elif ident == "qgisred_meters":
                if link_layer.geometryType() != 0:
                    continue
                for f in link_layer.getFeatures():
                    meter_geom = f.geometry()
                    if meter_geom.isEmpty():
                        continue
                    if node_g.distance(meter_geom) < tolerance:
                        meter_id = self.getFeatureIdValue(f, link_layer)
                        layer_name = link_layer.name()
                        singular = self.singular_forms.get(layer_name, layer_name)
                        found_links.append((link_layer, f, f"{singular} {meter_id}"))
        for link_layer, f, link_info in found_links:
            self.addAdjacencyItem(link_info, link_layer.customProperty("qgisred_identifier"))
        self.addServiceConnectionAdjacencies(node_g, tolerance)
        if layer.customProperty("qgisred_identifier") == "qgisred_junctions":
            self.addIsolationValveAdjacencies(node_g, tolerance)
        print("Exiting findAdjacentLinksByGeometry")

    def findServiceConnectionAdjacency(self, feature, current_layer):
        print("Entering findServiceConnectionAdjacency")
        geom = feature.geometry()
        if geom.isEmpty():
            print("Exiting findServiceConnectionAdjacency")
            return
        if geom.isMultipart():
            parts = geom.asMultiPolyline()
            if not parts or not parts[0]:
                print("Exiting findServiceConnectionAdjacency")
                return
            line_points = parts[0]
        else:
            line_points = geom.asPolyline()
        if not line_points:
            print("Exiting findServiceConnectionAdjacency")
            return
        endpoints = [QgsPointXY(line_points[0]), QgsPointXY(line_points[-1])]
        tolerance = 1e-6
        for pt in endpoints:
            dummy_feature = QgsFeature()
            dummy_feature.setGeometry(QgsGeometry.fromPointXY(pt))
            node_feature, node_layer = self.findOverlappedNode(dummy_feature, current_layer)
            if node_feature and node_layer.customProperty("qgisred_identifier") == "qgisred_junctions":
                junction_item_text = self.getFeatureIdValue(node_feature, node_layer, True)
                singular_name = self.singular_forms.get(node_layer.name(), node_layer.name())
                junction_full_name = singular_name + ' ' + junction_item_text
                self.addAdjacencyItem(junction_full_name, node_layer.customProperty("qgisred_identifier"))
                print("Exiting findServiceConnectionAdjacency")
                return
        for pt in endpoints:
            pt_geom = QgsGeometry.fromPointXY(pt)
            for lyr in self.getCheckedInputGroupLayers():
                if lyr.customProperty("qgisred_identifier") == "qgisred_pipes":
                    for f in lyr.getFeatures():
                        pipe_geom = f.geometry()
                        if pipe_geom.isEmpty():
                            continue
                        if pt_geom.distance(pipe_geom) < tolerance:
                            pipe_id = self.getFeatureIdValue(f, lyr)
                            singular = self.singular_forms.get(lyr.name(), lyr.name())
                            full_name = f"{singular} {pipe_id}"
                            self.addAdjacencyItem(full_name, lyr.customProperty("qgisred_identifier"))
                            print("Exiting findServiceConnectionAdjacency")
                            return
        print("Exiting findServiceConnectionAdjacency")

    def findIsolationValveAdjacency(self, feature, current_layer):
        print("Entering findIsolationValveAdjacency")
        geom = feature.geometry()
        if geom.isEmpty():
            print("Exiting findIsolationValveAdjacency")
            return
        tolerance = 1e-6
        node_feature, node_layer = self.findOverlappedNode(feature, current_layer)
        if node_feature and node_layer.customProperty("qgisred_identifier") == "qgisred_junctions":
            node_item_text = self.getFeatureIdValue(node_feature, node_layer, True)
            singular_name = self.singular_forms.get(node_layer.name(), node_layer.name())
            node_full_name = singular_name + ' ' + node_item_text
            self.addAdjacencyItem(node_full_name, node_layer.customProperty("qgisred_identifier"))
            print("Exiting findIsolationValveAdjacency")
            return
        for lyr in self.getCheckedInputGroupLayers():
            if lyr.customProperty("qgisred_identifier") == "qgisred_pipes":
                for f in lyr.getFeatures():
                    pipe_geom = f.geometry()
                    if pipe_geom.isEmpty():
                        continue
                    if geom.distance(pipe_geom) < tolerance:
                        pipe_id = self.getFeatureIdValue(f, lyr)
                        singular = self.singular_forms.get(lyr.name(), lyr.name())
                        full_name = f"{singular} {pipe_id}"
                        self.addAdjacencyItem(full_name, lyr.customProperty("qgisred_identifier"))
                        print("Exiting findIsolationValveAdjacency")
                        return
        print("Exiting findIsolationValveAdjacency")

    def findMeterAdjacency(self, feature, current_layer):
        print("Entering findMeterAdjacency")
        geom = feature.geometry()
        if geom.isEmpty():
            print("Exiting findMeterAdjacency")
            return
        tolerance = 1e-6
        node_feature, node_layer = self.findOverlappedNode(feature, current_layer)
        if node_feature:
            node_id = self.getFeatureIdValue(node_feature, node_layer, True)
            singular_name = self.singular_forms.get(node_layer.name(), node_layer.name())
            node_item_text = singular_name + ' ' + node_id
            self.addAdjacencyItem(node_item_text, node_layer.customProperty("qgisred_identifier"))
            print("Exiting findMeterAdjacency")
            return
        for lyr in self.getCheckedInputGroupLayers():
            if lyr.customProperty("qgisred_identifier") != "qgisred_meters":
                for f in lyr.getFeatures():
                    link_geom = f.geometry()
                    if link_geom.isEmpty():
                        continue
                    if geom.distance(link_geom) < tolerance:
                        adj_id = self.getFeatureIdValue(f, lyr)
                        singular = self.singular_forms.get(lyr.name(), lyr.name())
                        full_name = f"{singular} {adj_id}"
                        self.addAdjacencyItem(full_name, lyr.customProperty("qgisred_identifier"))
                        print("Exiting findMeterAdjacency")
                        return
        print("Exiting findMeterAdjacency")

    def findFeature(self, layer, feature):
        print("Entering findFeature")
        element_type_text = layer.name()
        self.cbElementType.setCurrentText(element_type_text)
        
        self.updateElementIds()
        
        feature_id_text = self.getFeatureIdValue(feature, layer, special_naming=True)
        
        index = self.cbElementId.findText(feature_id_text)
        if index >= 0:
            self.cbElementId.setCurrentIndex(index)

        self.clearHighlights()
        self.clearAllLayerSelections()
        self.listWidget.clear()

        finalTitleText = self.updateFoundElementLabel(feature_id_text, layer)

        highlight = QgsHighlight(iface.mapCanvas(), feature.geometry(), layer)
        highlight.setColor(QColor("red"))
        highlight.setWidth(5)
        highlight.show()
        self.main_highlight = highlight

        self.adjustMapView(feature)
        
        identifier = layer.customProperty("qgisred_identifier")
        if self.isLineElement(layer):
            self.findAdjacentNodesByGeometry(feature)
        elif identifier == "qgisred_meters":
            self.findMeterAdjacency(feature, layer)
        elif identifier == "qgisred_isolationvalves":
            self.findIsolationValveAdjacency(feature, layer)
        elif identifier == "qgisred_serviceconnections":
            self.findServiceConnectionAdjacency(feature, layer)
        else:
            self.findAdjacentLinksByGeometry(feature, layer)
        
        self.sortListWidgetItems()

        self.loadFeature(layer, feature, finalTitleText)
        print("Exiting findFeature")
