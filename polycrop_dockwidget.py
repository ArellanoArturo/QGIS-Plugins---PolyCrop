import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'polycrop_dockwidget_base.ui'))

class PolyCropDockWidget(QDockWidget, FORM_CLASS):
    def __init__(self, parent=None):
        super(PolyCropDockWidget, self).__init__(parent)
        self.setupUi(self)
