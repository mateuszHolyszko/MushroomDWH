import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QPushButton, QDialogButtonBox, QLabel
)
from src.core.schema import Schema

class ValuePromptDialog(QDialog):
    """
    Dialog to prompt the user for old and new categorical codes for a specific column.
    """
    def __init__(self, column_name: str, schema: Schema, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Replace Values in '{column_name}'")
        self.column_name = column_name
        self.schema = schema
        self.result = None  # tuple(old_code, new_code)

        # Layouts
        main_layout = QVBoxLayout(self)
        form = QFormLayout()

        # Prepare list of codes and labels
        coldef = self.schema.column_defs[column_name]
        codes = list(coldef.codes)
        labels = [coldef.labels[c] for c in codes]
        if coldef.allow_missing:
            codes.insert(0, schema.missing_code)
            labels.insert(0, 'Missing')

        # Old value combo
        self.old_cb = QComboBox(self)
        self.old_cb.addItems(labels)
        form.addRow("Old Value:", self.old_cb)

        # New value combo
        self.new_cb = QComboBox(self)
        self.new_cb.addItems(labels)
        form.addRow("New Value:", self.new_cb)

        main_layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def accept(self):
        # Map selected labels back to codes
        coldef = self.schema.column_defs[self.column_name]
        labels_to_codes = {coldef.labels[c]: c for c in coldef.codes}
        if coldef.allow_missing:
            labels_to_codes['Missing'] = self.schema.missing_code

        old_label = self.old_cb.currentText()
        new_label = self.new_cb.currentText()
        old_code = labels_to_codes.get(old_label)
        new_code = labels_to_codes.get(new_label)

        self.result = (old_code, new_code)
        super().accept()

    def get_values(self):
        """
        Show the dialog and return (old_code, new_code) if accepted, else None.
        """
        if self.exec_() == QDialog.Accepted:
            return self.result
        return None
