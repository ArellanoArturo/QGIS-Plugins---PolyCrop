# -*- coding: utf-8 -*-
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsMarkerSymbol,
    QgsSvgMarkerSymbolLayer,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant, QObject, QEvent, Qt
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QComboBox, QDoubleSpinBox, QSpinBox, QToolTip
import os
import json

class TooltipEventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            text = obj.toolTip()
            if text:
                QToolTip.showText(event.globalPos(), text, obj, obj.rect(), 5000)
                return True
        elif event.type() == QEvent.MouseMove:
            QToolTip.hideText()
        return super().eventFilter(obj, event)

from .polycrop_dockwidget import PolyCropDockWidget

class PolyCrop:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.resources_dir = os.path.join(self.plugin_dir, 'resources')
        self.dockwidget = None
        self.action = None
        self.svg_icons = []
        self._load_svg_icons()

    def _load_svg_icons(self):
        if os.path.exists(self.resources_dir):
            for f in os.listdir(self.resources_dir):
                if f.endswith('.svg'):
                    self.svg_icons.append(f)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.svg')
        self.action = QAction(QIcon(icon_path), "PolyCrop", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&PolyCrop", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&PolyCrop", self.action)
        if self.dockwidget:
            self.iface.removeDockWidget(self.dockwidget)

    def run(self):
        if not self.dockwidget:
            self.dockwidget = PolyCropDockWidget()
            from qgis.core import QgsMapLayerProxyModel
            from qgis.PyQt.QtWidgets import QAbstractItemView, QAbstractButton
            self.dockwidget.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)
            self.dockwidget.mTargetLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
            
            # Tooltips for native dock buttons
            for btn in self.dockwidget.findChildren(QAbstractButton):
                if btn.objectName() == "qt_dockwidget_closebutton":
                    btn.setToolTip("Cerrar panel de PolyCrop")
                elif btn.objectName() == "qt_dockwidget_floatbutton":
                    btn.setToolTip("Desacoplar panel (ventana flotante)")
                    
            # Install tooltip event filter
            self.tooltip_filter = TooltipEventFilter(self.dockwidget)
            self.dockwidget.installEventFilter(self.tooltip_filter)
            for child in self.dockwidget.findChildren(QObject):
                if hasattr(child, 'toolTip') and child.toolTip():
                    child.installEventFilter(self.tooltip_filter)
            
            self.dockwidget.radUpdateExisting.toggled.connect(self._on_update_mode_toggled)
            self.dockwidget.mTargetLayerComboBox.layerChanged.connect(self.load_pattern_from_layer)
            
            self.dockwidget.btnAdd.clicked.connect(self.add_crop)
            self.dockwidget.btnDuplicate.clicked.connect(self.duplicate_crop)
            self.dockwidget.btnRemove.clicked.connect(self.remove_crop)
            self.dockwidget.btnClear.clicked.connect(self.clear_pattern)
            self.dockwidget.btnGenerate.clicked.connect(self.generate)
            
            # Fix for Drag and Drop with cell widgets
            self.dockwidget.tableWidget.setDragDropMode(QAbstractItemView.NoDragDrop)
            self.dockwidget.tableWidget.verticalHeader().setSectionsMovable(True)
            
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            
            # Add initial crop
            self.add_crop()
            
        self.dockwidget.show()

    def add_crop(self):
        table = self.dockwidget.tableWidget
        row = table.rowCount()
        table.insertRow(row)
        
        # Combo for icons
        combo_icon = QComboBox()
        for icon in self.svg_icons:
            icon_path = os.path.join(self.resources_dir, icon)
            combo_icon.addItem(QIcon(icon_path), icon, icon_path)
        table.setCellWidget(row, 0, combo_icon)
        
        # Name
        table.setItem(row, 1, QTableWidgetItem(f"Cultivo {row+1}"))
        
        # Spacing
        spin_spacing = QDoubleSpinBox()
        spin_spacing.setRange(0.1, 100.0)
        spin_spacing.setSingleStep(0.1)
        spin_spacing.setValue(1.0)
        table.setCellWidget(row, 2, spin_spacing)
        
        # Quantity
        spin_qty = QSpinBox()
        spin_qty.setRange(1, 1000)
        spin_qty.setValue(1)
        table.setCellWidget(row, 3, spin_qty)

    def remove_crop(self):
        table = self.dockwidget.tableWidget
        selected_rows = set(index.row() for index in table.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            table.removeRow(row)

    def _on_update_mode_toggled(self, checked):
        self.dockwidget.mTargetLayerComboBox.setEnabled(checked)
        self.dockwidget.txtLayerName.setEnabled(not checked)
        if checked:
            self.load_pattern_from_layer(self.dockwidget.mTargetLayerComboBox.currentLayer())

    def load_pattern_from_layer(self, layer):
        if not layer or not self.dockwidget.radUpdateExisting.isChecked():
            return
            
        pattern_json = layer.customProperty("PolyCrop_Pattern")
        if not pattern_json:
            return
            
        try:
            ui_pattern = json.loads(pattern_json)
        except Exception:
            return
            
        # Clear table and summary
        table = self.dockwidget.tableWidget
        table.setRowCount(0)
        self.dockwidget.txtSummary.clear()
        
        # Load source line layer if available
        source_layer_id = layer.customProperty("PolyCrop_SourceLineLayer")
        if source_layer_id:
            from qgis.core import QgsProject
            proj_layer = QgsProject.instance().mapLayer(source_layer_id)
            if proj_layer:
                self.dockwidget.mMapLayerComboBox.setLayer(proj_layer)
        
        # Populate table
        for item in ui_pattern:
            row = table.rowCount()
            table.insertRow(row)
            
            # Icon
            combo_icon = QComboBox()
            for icon in self.svg_icons:
                icon_path = os.path.join(self.resources_dir, icon)
                combo_icon.addItem(QIcon(icon_path), icon, icon_path)
                if icon_path == item.get('icon_path'):
                    combo_icon.setCurrentIndex(combo_icon.count() - 1)
            table.setCellWidget(row, 0, combo_icon)
            
            # Name
            table.setItem(row, 1, QTableWidgetItem(item.get('name', '')))
            
            # Spacing
            spin_spacing = QDoubleSpinBox()
            spin_spacing.setRange(0.1, 100.0)
            spin_spacing.setSingleStep(0.1)
            spin_spacing.setValue(item.get('spacing', 1.0))
            table.setCellWidget(row, 2, spin_spacing)
            
            # Quantity
            spin_qty = QSpinBox()
            spin_qty.setRange(1, 1000)
            spin_qty.setValue(item.get('qty', 1))
            table.setCellWidget(row, 3, spin_qty)

    def duplicate_crop(self):
        table = self.dockwidget.tableWidget
        selected_indexes = table.selectedIndexes()
        if not selected_indexes:
            return
            
        selected_row = selected_indexes[0].row()
        
        # Read values from selected row
        source_combo = table.cellWidget(selected_row, 0)
        source_icon_path = source_combo.currentData()
        source_name = table.item(selected_row, 1).text()
        source_spacing = table.cellWidget(selected_row, 2).value()
        source_qty = table.cellWidget(selected_row, 3).value()
        
        # Insert new row below
        new_row = selected_row + 1
        table.insertRow(new_row)
        
        # Combo for icons
        combo_icon = QComboBox()
        for icon in self.svg_icons:
            icon_path = os.path.join(self.resources_dir, icon)
            combo_icon.addItem(QIcon(icon_path), icon, icon_path)
            if icon_path == source_icon_path:
                combo_icon.setCurrentIndex(combo_icon.count() - 1)
        table.setCellWidget(new_row, 0, combo_icon)
        
        # Name
        table.setItem(new_row, 1, QTableWidgetItem(source_name))
        
        # Spacing
        spin_spacing = QDoubleSpinBox()
        spin_spacing.setRange(0.1, 100.0)
        spin_spacing.setSingleStep(0.1)
        spin_spacing.setValue(source_spacing)
        table.setCellWidget(new_row, 2, spin_spacing)
        
        # Quantity
        spin_qty = QSpinBox()
        spin_qty.setRange(1, 1000)
        spin_qty.setValue(source_qty)
        table.setCellWidget(new_row, 3, spin_qty)

    def clear_pattern(self):
        self.dockwidget.tableWidget.setRowCount(0)

    def generate(self):
        layer = self.dockwidget.mMapLayerComboBox.currentLayer()
        if not layer or layer.geometryType() != QgsWkbTypes.LineGeometry:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "Por favor seleccione una capa de líneas válida.")
            return

        table = self.dockwidget.tableWidget
        if table.rowCount() == 0:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "El patrón debe tener al menos un cultivo.")
            return

        # Read pattern
        pattern = []
        ui_pattern = []
        for visual_row in range(table.rowCount()):
            logical_row = table.verticalHeader().logicalIndex(visual_row)
            combo = table.cellWidget(logical_row, 0)
            icon_path = combo.currentData()
            name = table.item(logical_row, 1).text()
            spacing = table.cellWidget(logical_row, 2).value()
            qty = table.cellWidget(logical_row, 3).value()
            
            ui_pattern.append({
                'name': name,
                'spacing': spacing,
                'icon_path': icon_path,
                'qty': qty
            })
            
            # Expand quantity into the pattern
            for _ in range(qty):
                pattern.append({
                    'name': name,
                    'spacing': spacing,
                    'icon_path': icon_path
                })
                
        if not pattern:
            return

        reverse_dir = self.dockwidget.chkReverse.isChecked()
        restart_pattern = self.dockwidget.chkRestart.isChecked()
        update_existing = self.dockwidget.radUpdateExisting.isChecked()

        if update_existing:
            vl = self.dockwidget.mTargetLayerComboBox.currentLayer()
            if not vl or vl.geometryType() != QgsWkbTypes.PointGeometry:
                QMessageBox.warning(self.iface.mainWindow(), "Error", "Por favor seleccione una capa de puntos válida para actualizar.")
                return
            pr = vl.dataProvider()
        else:
            # Create output layer
            layer_name = self.dockwidget.txtLayerName.text().strip()
            if not layer_name:
                layer_name = "Policultivo_Generado"
                
            crs = layer.crs().authid()
            vl = QgsVectorLayer(f"Point?crs={crs}", layer_name, "memory")
            pr = vl.dataProvider()
            pr.addAttributes([
                QgsField("ID_Linea", QVariant.Int),
                QgsField("Cultivo", QVariant.String),
                QgsField("Orden", QVariant.Int),
                QgsField("Espacio_usado", QVariant.Double)
            ])
            vl.updateFields()

        features_to_add = []
        pattern_index = 0
        counts = {}
        
        # Decide which features to process
        selected_features = layer.selectedFeatures()
        if selected_features:
            features_to_process = selected_features
        else:
            features_to_process = list(layer.getFeatures())
            
        line_ids = [f.id() for f in features_to_process]
        
        # Selective Deletion logic
        if update_existing and line_ids:
            from qgis.core import QgsFeatureRequest
            expr = f"ID_Linea IN ({','.join(map(str, line_ids))})"
            request = QgsFeatureRequest().setFilterExpression(expr)
            ids_to_delete = [f.id() for f in vl.getFeatures(request)]
            if ids_to_delete:
                pr.deleteFeatures(ids_to_delete)
        
        for feature in features_to_process:
            geom = feature.geometry()
            if not geom or geom.isEmpty():
                continue
                
            if reverse_dir:
                geom = self._reverse_line(geom)
                
            length = geom.length()
            current_dist = 0.0
            
            if restart_pattern:
                pattern_index = 0
                
            # First point of the line
            item = pattern[pattern_index]
            pt = geom.interpolate(current_dist)
            if not pt.isEmpty():
                f = QgsFeature()
                f.setGeometry(pt)
                f.setAttributes([feature.id(), item['name'], pattern_index, 0.0])
                features_to_add.append(f)
                counts[item['name']] = counts.get(item['name'], 0) + 1
            
            # Subsequent points
            while True:
                prev_item = pattern[pattern_index]
                
                # Move to next item in sequence
                pattern_index = (pattern_index + 1) % len(pattern)
                curr_item = pattern[pattern_index]
                
                # Calculate max spacing
                step = max(prev_item['spacing'], curr_item['spacing'])
                current_dist += step
                
                if current_dist > length:
                    break
                    
                pt = geom.interpolate(current_dist)
                if not pt.isEmpty():
                    f = QgsFeature()
                    f.setGeometry(pt)
                    f.setAttributes([feature.id(), curr_item['name'], pattern_index, step])
                    features_to_add.append(f)
                    counts[curr_item['name']] = counts.get(curr_item['name'], 0) + 1

        if features_to_add:
            pr.addFeatures(features_to_add)
            vl.updateExtents()
            
            # Apply styling
            self._apply_styling(vl, pattern)
            
            # Save pattern metadata
            vl.setCustomProperty("PolyCrop_Pattern", json.dumps(ui_pattern))
            vl.setCustomProperty("PolyCrop_SourceLineLayer", layer.id())
            
            if not update_existing:
                QgsProject.instance().addMapLayer(vl)
            else:
                vl.triggerRepaint()
            
            # Show summary
            summary = "<b>Proceso terminado.</b><br/>"
            total = 0
            for name, count in counts.items():
                summary += f"&bull; {name}: {count}<br/>"
                total += count
            summary += f"<br/><b>Total individuos: {total}</b>"
            self.dockwidget.txtSummary.setHtml(summary)
        else:
            self.dockwidget.txtSummary.setHtml("<font color='red'>No se generaron puntos (posiblemente las líneas son muy cortas).</font>")

    def _reverse_line(self, geom):
        # QGIS 3 geometries
        if geom.isMultipart():
            # For simplicity, we just deal with single lines or we have to reverse each part.
            # Here is a basic reversal for single parts:
            parts = geom.asMultiPolyline()
            new_parts = [part[::-1] for part in parts]
            return QgsGeometry.fromMultiPolylineXY(new_parts)
        else:
            line = geom.asPolyline()
            return QgsGeometry.fromPolylineXY(line[::-1])

    def _apply_styling(self, layer, pattern):
        categories = []
        # Unique crops in pattern
        unique_crops = {}
        for item in pattern:
            if item['name'] not in unique_crops:
                unique_crops[item['name']] = item['icon_path']
                
        for name, icon_path in unique_crops.items():
            svg_layer = QgsSvgMarkerSymbolLayer(icon_path)
            svg_layer.setSize(4.0) # 4mm size
            symbol = QgsMarkerSymbol()
            symbol.changeSymbolLayer(0, svg_layer)
            
            category = QgsRendererCategory(name, symbol, name)
            categories.append(category)
            
        renderer = QgsCategorizedSymbolRenderer("Cultivo", categories)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
