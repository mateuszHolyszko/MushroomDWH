import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from src.gui.views.subset_panel import SubsetPanel
from src.gui.models.table_model import TableModel
from src.core.warehouse import DataWarehouse
from src.io.writer import write_mushroom_data
from src.core.data_table import DataTable
from src.extractor.subset_extractor import SubsetExtractor
from src.gui.views.delegates import ComboBoxDelegate

class SubsetController:
    """
    Controller for the SubsetPanel: handles slicing, column selection, and saving subsets.
    """
    def __init__(self, main_window):
        self.main = main_window
        self.panel: SubsetPanel = main_window.subset_panel
        self.extractor = SubsetExtractor(self.main.warehouse)
        # Keep track of current working table name
        self.working_table_name = None
        # Connect signals
        self.panel.slice_btn.clicked.connect(self.on_slice)
        self.panel.col_btn.clicked.connect(self.on_select_columns)
        self.panel.save_btn.clicked.connect(self.on_save_subset)
        self.panel.filter_col.currentTextChanged.connect(self.panel.update_filter_values)
        self.panel.filter_btn.clicked.connect(self.on_apply_filter)

    def on_slice(self):
        # Use either subset or main table
        table_name = self.working_table_name or self.main.current_table_name
        if not table_name:
            QMessageBox.warning(self.main, "No Table", "Please load a dataset first.")
            return
        
        start = self.panel.start_spin.value()
        end = self.panel.end_spin.value()
        step = self.panel.step_spin.value()
        
        # Extract subset
        subset: DataTable = self.extractor.extract_rows(table_name, start, end, step)
        self._display_subset(subset)

    def on_select_columns(self):
        # Use either subset or main table
        table_name = self.working_table_name or self.main.current_table_name
        if not table_name:
            QMessageBox.warning(self.main, "No Table", "Please load a dataset first.")
            return
        
        items = self.panel.col_list.selectedItems()
        cols = [it.text() for it in items]
        if not cols:
            QMessageBox.warning(self.main, "No Columns", "Please select at least one column.")
            return
        
        subset: DataTable = self.extractor.extract_columns(table_name, cols)
        self._display_subset(subset)

    def on_save_subset(self):
        if not hasattr(self, 'current_subset') or self.current_subset is None:
            QMessageBox.warning(self.main, "No Subset", "No subset available to save.")
            return
        if not self.working_table_name or not hasattr(self, 'current_subset'):
            QMessageBox.warning(self.main, "No Subset", "Please create a subset first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self.main,
            "Save Subset",
            "",
            "Data Files (*.data *.csv);;All Files (*)"
        )
        if not path:
            return
        # Write directly from DataTable
        write_mushroom_data(self.current_subset.df, Path(path))
        QMessageBox.information(self.main, "Saved", f"Subset saved to {path}")

    def _display_subset(self, subset: DataTable):
        # Keep track of subset
        self.current_subset = subset
        
        # Store subset in warehouse with special name
        self.working_table_name = f"{self.main.current_table_name}_subset"
        self.main.warehouse.tables[self.working_table_name] = subset
        
        # Update table view
        model = TableModel(subset, self.main.warehouse.schema)
        self.main.table_view.setModel(model)
        
        # Apply delegates
        for idx, col in enumerate(subset.df.columns):
            delegate = ComboBoxDelegate(col, self.main.warehouse.schema, 
                                    parent=self.main.table_view)
            self.main.table_view.setItemDelegateForColumn(idx, delegate)
        
        # Update subset panel controls for the new subset
        self.panel.set_table(self.working_table_name)
        
        # Update stats panel
        self.main.stats_panel.set_table(self.working_table_name)
        
        # Update status
        self.main.status_bar.showMessage(
            f"Displayed subset: {len(subset)} rows, {subset.df.shape[1]} cols"
        )

    def on_apply_filter(self):
        """Handle value-based filtering."""
        table_name = self.working_table_name or self.main.current_table_name
        if not table_name:
            QMessageBox.warning(self.main, "No Table", "Please load a dataset first.")
            return
            
        # Get selected column and values
        column = self.panel.filter_col.currentText()
        selected_items = self.panel.filter_values.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main, "No Values", 
                            "Please select at least one value to filter by.")
            return
            
        # Get codes from item data instead of display text
        values = [item.data(Qt.UserRole) for item in selected_items]
        
        # Create conditions dict for extractor
        conditions = {column: values}
        
        # Extract filtered subset
        subset = self.extractor.extract_by_value(table_name, conditions)
        
        if len(subset.df) == 0:
            QMessageBox.warning(self.main, "No Results", 
                            "No rows match the selected filter criteria.")
            return
            
        self._display_subset(subset)
