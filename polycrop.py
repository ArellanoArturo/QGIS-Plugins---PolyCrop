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
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QComboBox, QDoubleSpinBox, QSpinBox
import os

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
            self.dockwidget.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)
            self.dockwidget.btnAdd.clicked.connect(self.add_crop)
            self.dockwidget.btnRemove.clicked.connect(self.remove_crop)
            self.dockwidget.btnGenerate.clicked.connect(self.generate)
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
        for row in range(table.rowCount()):
            combo = table.cellWidget(row, 0)
            icon_path = combo.currentData()
            name = table.item(row, 1).text()
            spacing = table.cellWidget(row, 2).value()
            qty = table.cellWidget(row, 3).value()
            
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

        # Create output layer
        crs = layer.crs().authid()
        vl = QgsVectorLayer(f"Point?crs={crs}", "Policultivo_Generado", "memory")
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
        
        for feature in layer.getFeatures():
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
                    # If we exceeded the line length, we don't place this crop here.
                    # We need to decide if the next line starts with THIS crop or the NEXT.
                    # Usually, if we didn't place it, we should start with it on the next line (if not restarting).
                    # So we don't increment anything further, just break.
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
            
            QgsProject.instance().addMapLayer(vl)
            
            # Show summary
            summary = "Proceso terminado.\n\n"
            total = 0
            for name, count in counts.items():
                summary += f"- {name}: {count}\n"
                total += count
            summary += f"\nTotal individuos: {total}"
            QMessageBox.information(self.iface.mainWindow(), "Resumen PolyCrop", summary)
        else:
            QMessageBox.information(self.iface.mainWindow(), "Sin Resultados", "No se generaron puntos (posiblemente las líneas son muy cortas).")

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
