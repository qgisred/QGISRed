# Third-party imports
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (QDialog, QMessageBox, QWidget, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QComboBox, QLineEdit, QPushButton,
                             QCheckBox, QHBoxLayout, QAbstractItemView, QDialogButtonBox, 
                             QDoubleSpinBox, QLabel, QVBoxLayout)

class RangeEditDialog(QDialog):
    """A simple dialog for editing a numeric range (lower and upper bounds)."""
    def __init__(self, lowerValue, upperValue, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit Range"))
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(self.tr("Lower Value:")))
        self.lowerSpinBox = QDoubleSpinBox()
        self.lowerSpinBox.setRange(-1e12, 1e12)
        self.lowerSpinBox.setDecimals(4)
        self.lowerSpinBox.setValue(lowerValue)
        layout.addWidget(self.lowerSpinBox)

        layout.addWidget(QLabel(self.tr("Upper Value:")))
        self.upperSpinBox = QDoubleSpinBox()
        self.upperSpinBox.setRange(-1e12, 1e12)
        self.upperSpinBox.setDecimals(4)
        self.upperSpinBox.setValue(upperValue)
        layout.addWidget(self.upperSpinBox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def getValues(self):
        """Returns the current values of the spin boxes."""
        return self.lowerSpinBox.value(), self.upperSpinBox.value()