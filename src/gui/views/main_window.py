import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog,
    QTableView, QTabWidget, QWidget, QVBoxLayout,
    QAction, QMessageBox, QLabel, QMenu
)
from src.core.warehouse import DataWarehouse
from src.gui.models.table_model import TableModel
from src.gui.views.delegates import ComboBoxDelegate
from src.editor.automatic_editor import AutomaticEditor
from src.editor.manual_editor import ManualEditor
from src.gui.views.subset_panel import SubsetPanel


class MainWindow(QMainWindow):
    def __init__(self, table_store):
        super().__init__()
        self.setWindowTitle("Mushroom Data Warehouse")
        self.resize(1000, 700)

        # Use table_store instead of direct warehouse
        self.table_store = table_store
        self.table_store.add_observer(self._on_table_changed)
        
        # These editors should use table_store's warehouse
        self.manual_editor = ManualEditor(self.table_store.warehouse)
        self.automatic_editor = AutomaticEditor(self.table_store.warehouse)

        self._init_ui()

        # Initialize controllers with self
        from src.gui.controllers.context_menu_ctrl import ContextMenuController
        self.context_ctrl = ContextMenuController(self)
        from src.gui.controllers.subset_ctrl import SubsetController
        self.subset_ctrl = SubsetController(self)
        from src.gui.controllers.class_ctrl import ClassController
        self.class_ctrl = ClassController(self)


    def _init_ui(self):
        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open Data File...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        save_action = QAction("Save Data File...", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tabbed interface
        self.tabs = QTabWidget()

        # 1) Table tab
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        self.table_view = QTableView()
        # Enable custom context menu on table
        table_layout.addWidget(self.table_view)
        table_tab.setLayout(table_layout)
        self.tabs.addTab(table_tab, "Table")

        # 2) Statistics tab
        from src.gui.views.stats_panel import StatsPanel
        self.stats_panel = StatsPanel(self.table_store)
        self.tabs.addTab(self.stats_panel, "Statistics")

        # 3) Subset tab
        self.subset_panel = SubsetPanel(self.table_store)
        self.tabs.addTab(self.subset_panel, "Subset")

        # 4) Classify tab (
        from src.gui.views.class_panel import ClassPanel
        self.class_panel = ClassPanel(self.table_store)
        self.tabs.addTab(self.class_panel, "Classify")

        # Set up status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.setCentralWidget(self.tabs)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Mushroom Data File", "",
            "Data Files (*.data *.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            # Load into table_store
            table_name = 'mushrooms'
            self.table_store.warehouse.load_table(table_name, path)
            self.table_store.set_active_table(table_name)
            
            # Model and delegates will be handled by _on_table_changed
            self.status_bar.showMessage(f"Loaded {len(self.table_store.get_active_table().df)} rows from {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", str(e))

    def save_file(self):
        if not self.table_store.active_table_name:
            QMessageBox.warning(self, "No Table", "No data loaded to save.")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Mushroom Data File", "",
            "Data Files (*.data *.csv);;All Files (*)"
        )
        if not path:
            return
            
        try:
            self.table_store.warehouse.save_table(self.table_store.active_table_name, path)
            QMessageBox.information(self, "Saved", f"Data saved to {path}")
            self.status_bar.showMessage(f"Data saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", str(e))

    def on_table_context_menu(self, pos):
        """
        Show context menu for table operations: insert/delete rows, edit values, etc.
        """
        # Determine selected rows and columns
        sel = self.table_view.selectionModel().selectedIndexes()
        rows = sorted({idx.row() for idx in sel})
        cols = sorted({idx.column() for idx in sel})

        menu = QMenu(self.table_view)
        # Insert row at selection start or end
        insert_action = menu.addAction("Insert Row")
        delete_action = menu.addAction("Delete Row(s)")
        menu.addSeparator()
        replace_action = menu.addAction("Replace Value in Column")

        action = menu.exec_(self.table_view.viewport().mapToGlobal(pos))

        if not self.table_store.active_table_name:
            return

        if action == insert_action:
            row = rows[0] if rows else len(self.table_store.get_active_table().df)
            self.manual_editor.add_row(self.table_store.active_table_name, {})
        elif action == delete_action and rows:
            for r in reversed(rows):
                self.manual_editor.delete_row(self.table_store.active_table_name, r)
        elif action == replace_action and cols:
            col = self.table_store.get_active_table().df.columns[cols[0]]
            self.automatic_editor.replace_values(self.table_store.active_table_name, col, 'old', 'new')

        # No need to manually refresh - table_store observer will handle it
        # TableStore will notify observers which triggers _on_table_changed
        # Force a refresh by re-setting the active table
        self.table_store.set_active_table(self.table_store.active_table_name)

    def _on_table_changed(self, table_name: str):
        """Handle updates from the table store."""
        if not table_name:
            return
            
        table = self.table_store.get_active_table()
        
        # Update table view
        model = TableModel(table, self.table_store.schema)
        self.table_view.setModel(model)
        
        # Apply delegates
        for idx, col_name in enumerate(table.df.columns):
            delegate = ComboBoxDelegate(col_name, self.table_store.schema, 
                                      parent=self.table_view)
            self.table_view.setItemDelegateForColumn(idx, delegate)
            
        # Update all panels
        self.stats_panel.set_table(table_name)
        self.subset_panel.set_table(table_name)
        self.class_panel.set_table(table_name)
        
        # Update status
        self.status_bar.showMessage(f"Active table: {table_name}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
