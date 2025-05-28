import sys
from pathlib import Path

# Ensure project root is on Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu, QInputDialog, QLineEdit
from src.gui.models.table_model import TableModel
from src.gui.views.delegates import ComboBoxDelegate
from src.gui.views.dialogs.value_prompt import ValuePromptDialog

class ContextMenuController:
    """
    Controller to provide right-click context menu on a QTableView for
    editing operations: insert/delete rows, replace values in columns.
    """
    def __init__(self, main_window):
        self.main = main_window
        tv = self.main.table_view
        tv.setContextMenuPolicy(Qt.CustomContextMenu)
        tv.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, pos):
        if not self.main.table_store.active_table_name:
            return

        tv = self.main.table_view
        sel_model = tv.selectionModel()
        indexes = sel_model.selectedIndexes()
        if not indexes:
            return
        rows = sorted({idx.row() for idx in indexes})
        cols = sorted({idx.column() for idx in indexes})

        menu = QMenu(tv)
        insert_act = menu.addAction("Insert Row")
        delete_act = menu.addAction("Delete Row(s)")
        menu.addSeparator()
        replace_act = menu.addAction("Replace Value in Column")

        action = menu.exec_(tv.viewport().mapToGlobal(pos))

        if action == insert_act:
            # Determine insertion index (before first selected row, or append)
            insert_at = rows[0] if rows else None

            # Get table and schema
            table = self.main.table_store.get_active_table()
            schema = self.main.table_store.schema

            # Build a default row: mode for non‐missing columns, '?' for allow_missing
            from src.stats.categorical_stats import categorical_stats

            row_data = {}
            for col in table.df.columns:
                coldef = schema.column_defs[col]
                if coldef.allow_missing:
                    row_data[col] = schema.missing_code
                else:
                    stats = categorical_stats(table.df[col], schema, col)
                    modes = stats.get('mode', [])
                    if not modes:
                        raise ValueError(f"No mode found for required column '{col}'")
                    row_data[col] = modes[0]

            # Append the new row
            self.main.manual_editor.add_row(
                self.main.table_store.active_table_name, 
                row_data
            )

            # Reorder so the new row appears at insert_at (or stay at end)
            df = table.df
            new_idx = len(df) - 1
            if insert_at is not None and 0 <= insert_at < new_idx:
                order = list(range(insert_at)) + [new_idx] + list(range(insert_at, new_idx))
                final_idx = insert_at
            else:
                order = list(range(len(df)))
                final_idx = new_idx

            # Apply reorder and reset index
            reordered = df.iloc[order].reset_index(drop=True)
            table._df = reordered
            self.main.table_store.warehouse.tables[self.main.table_store.active_table_name] = table

            # Refresh view through table_store
            self.main.table_store.set_active_table(self.main.table_store.active_table_name)

            # Auto‐select the newly inserted row
            self.main.table_view.selectRow(final_idx)
            self.main.status_bar.showMessage(f"Inserted row at position {final_idx}")

        elif action == delete_act:
            # Delete selected rows
            for r in reversed(rows):
                self.main.manual_editor.delete_row(
                    self.main.table_store.active_table_name, 
                    r
                )
            # Refresh through table_store
            self.main.table_store.set_active_table(self.main.table_store.active_table_name)

        elif action == replace_act and cols:
            # Single-column replace
            col_idx = cols[0]
            col_name = self.main.table_store.get_active_table().df.columns[col_idx]
            dlg = ValuePromptDialog(col_name, self.main.table_store.schema, parent=tv)
            vals = dlg.get_values()
            if vals:
                old, new = vals
                self.main.automatic_editor.replace_values(
                    self.main.table_store.active_table_name,
                    col_name, 
                    old, 
                    new
                )
            # Refresh through table_store
            self.main.table_store.set_active_table(self.main.table_store.active_table_name)

    def _refresh_view(self):
        """No longer needed - table_store observer pattern handles updates"""
        pass
