import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QGroupBox, QFormLayout
)
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable

class SubsetPanel(QWidget):
    """
    UI panel for extracting subsets from a loaded table.
    Supports row slicing, column selection, and value-based filters.
    """
    def __init__(self, warehouse: DataWarehouse, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.current_table = None
        self.init_ui()

    def init_ui(self):
        main = QVBoxLayout(self)
        # Controls for row slicing
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Rows: start"))
        self.start_spin = QSpinBox(); self.start_spin.setMinimum(0)
        row_layout.addWidget(self.start_spin)
        row_layout.addWidget(QLabel("end"))
        self.end_spin = QSpinBox(); self.end_spin.setMinimum(0)
        row_layout.addWidget(self.end_spin)
        row_layout.addWidget(QLabel("step"))
        self.step_spin = QSpinBox(); self.step_spin.setMinimum(1); self.step_spin.setValue(1)
        row_layout.addWidget(self.step_spin)
        self.slice_btn = QPushButton("Slice Rows")
        self.slice_btn.setEnabled(False)
        row_layout.addWidget(self.slice_btn)
        main.addLayout(row_layout)

        # Controls for column selection
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Columns:"))
        self.col_list = QListWidget(); 
        self.col_list.setSelectionMode(QListWidget.MultiSelection)
        col_layout.addWidget(self.col_list)
        self.col_btn = QPushButton("Select Columns")
        self.col_btn.setEnabled(False)
        col_layout.addWidget(self.col_btn)
        main.addLayout(col_layout)

        # Value-based filter controls
        filter_group = QGroupBox("Value-based Filter")
        filter_layout = QFormLayout()
        
        # Column selector
        self.filter_col = QComboBox()
        filter_layout.addRow("Column:", self.filter_col)
        
        # Value selector (supports multiple selection)
        self.filter_values = QListWidget()
        self.filter_values.setSelectionMode(QListWidget.MultiSelection)
        filter_layout.addRow("Values:", self.filter_values)
        
        # Apply filter button
        self.filter_btn = QPushButton("Apply Filter")
        self.filter_btn.setEnabled(False)
        filter_layout.addRow(self.filter_btn)
        
        filter_group.setLayout(filter_layout)
        main.addWidget(filter_group)

        # Save subset
        self.save_btn = QPushButton("Save Subset As...")
        self.save_btn.setEnabled(False)
        main.addWidget(self.save_btn)

    def set_table(self, table_name: str):
        """Populate controls when a new table is loaded."""
        self.current_table = table_name
        if table_name is None:
            # Clear all controls
            self.col_list.clear()
            self.start_spin.setValue(0)
            self.end_spin.setValue(0)
            self.step_spin.setValue(1)
            self.filter_col.clear()
            self.filter_values.clear()
            self.slice_btn.setEnabled(False)
            self.col_btn.setEnabled(False)
            self.filter_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            return
        
        table = self.warehouse.get_table(table_name)
        n = len(table)
        
        # Update row controls
        self.start_spin.setMaximum(n-1)
        self.start_spin.setValue(0)
        self.end_spin.setMaximum(n)
        self.end_spin.setValue(n)
        self.step_spin.setValue(1)
        
        # Update column lists
        self.col_list.clear()
        self.filter_col.clear()
        for col in table.df.columns:
            self.col_list.addItem(QListWidgetItem(col))
            self.filter_col.addItem(col)
        
        # Enable buttons
        self.slice_btn.setEnabled(True)
        self.col_btn.setEnabled(True)
        self.filter_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def update_filter_values(self):
        """Update available values for the selected filter column."""
        if not self.current_table or self.filter_col.currentText() == '':
            self.filter_values.clear()
            return
            
        table = self.warehouse.get_table(self.current_table)
        col = self.filter_col.currentText()
        coldef = self.warehouse.schema.column_defs[col]
        
        # Get unique values and map to labels
        unique_codes = sorted(table.df[col].unique())
        labeled_values = []
        for code in unique_codes:
            if code == self.warehouse.schema.missing_code:
                if coldef.allow_missing:
                    labeled_values.append(('Missing', code))
            else:
                label = coldef.labels.get(code, code)
                labeled_values.append((label, code))
        
        # Update list widget with labels
        self.filter_values.clear()
        for label, code in labeled_values:
            item = QListWidgetItem(label)
            # Store the code as item data
            item.setData(Qt.UserRole, code)
            self.filter_values.addItem(item)
