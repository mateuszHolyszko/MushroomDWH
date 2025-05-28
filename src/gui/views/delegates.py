import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox
from PyQt5.QtCore import Qt
from src.core.schema import Schema

class ComboBoxDelegate(QStyledItemDelegate):
    """
    Provides a QComboBox editor for categorical columns based on a Schema ColumnDef.
    Displays human-readable labels but stores underlying codes.
    """
    def __init__(self, column_name: str, schema: Schema, parent=None):
        super().__init__(parent)
        self.column_name = column_name
        self.schema = schema
        coldef = schema.column_defs[column_name]
        # Prepare mapping
        self.code_to_label = dict(coldef.labels)
        if coldef.allow_missing:
            self.code_to_label[schema.missing_code] = 'Missing'
        # Build ordered lists
        self.codes = list(self.code_to_label.keys())
        self.labels = [self.code_to_label[code] for code in self.codes]
        # Inverse map
        self.label_to_code = {label: code for code, label in self.code_to_label.items()}

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.labels)
        combo.setEditable(False)
        return combo

    def setEditorData(self, editor: QComboBox, index):
        # index.model().data(index, Qt.EditRole) returns the code
        code = index.model().data(index, Qt.EditRole)
        label = self.code_to_label.get(code, '')
        if label in self.labels:
            editor.setCurrentText(label)

    def setModelData(self, editor: QComboBox, model, index):
        label = editor.currentText()
        code = self.label_to_code.get(label, self.schema.missing_code)
        # Store code as model data
        model.setData(index, code, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
