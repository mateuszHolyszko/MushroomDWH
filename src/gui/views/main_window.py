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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mushroom Data Warehouse")
        self.resize(1000, 700)

        # Backend data warehouse
        self.warehouse = DataWarehouse()
        self.current_table_name = None
        self.working_table_name = None
        self.manual_editor = ManualEditor(self.warehouse)
        self.automatic_editor = AutomaticEditor(self.warehouse)

        self._init_ui()

        # hook up right‑click context menu for the table:
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
        self.stats_panel = StatsPanel(self.warehouse)
        self.tabs.addTab(self.stats_panel, "Statistics")

        # 3) Subset tab
        self.subset_panel = SubsetPanel(self.warehouse)
        self.tabs.addTab(self.subset_panel, "Subset")

        # 4) Edit tab (placeholder)
        edit_tab = QWidget()
        edit_layout = QVBoxLayout()
        edit_layout.addWidget(QLabel("Edit panel (placeholder)"))
        edit_tab.setLayout(edit_layout)
        self.tabs.addTab(edit_tab, "Edit")

        # 5) Classify tab (placeholder)
        from src.gui.views.class_panel import ClassPanel
        self.class_panel = ClassPanel(self.warehouse)
        self.tabs.addTab(self.class_panel, "Classify")

        # Set up status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.setCentralWidget(self.tabs)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Mushroom Data File",
            "",
            "Data Files (*.data *.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            # Load into warehouse
            self.current_table_name = 'mushrooms'
            self.warehouse.load_table(self.current_table_name, path)
            table = self.warehouse.get_table(self.current_table_name)
            # Create and set model
            model = TableModel(table, self.warehouse.schema)
            self.table_view.setModel(model)
            # Apply delegates per column
            for col_idx, col_name in enumerate(table.df.columns):
                delegate = ComboBoxDelegate(col_name, self.warehouse.schema, parent=self.table_view)
                self.table_view.setItemDelegateForColumn(col_idx, delegate)
            # Notify stats panel of new table
            self.stats_panel.set_table(self.current_table_name)
            self.subset_panel.set_table(self.current_table_name)
            self.class_panel.set_table(self.current_table_name)
            # Update status bar
            self.status_bar.showMessage(f"Loaded {self.current_table_name} from {path}")
            self.status_bar.showMessage(f"Loaded {len(table.df)} rows from {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", str(e))

    def save_file(self):
        if not self.current_table_name:
            QMessageBox.warning(self, "No Table", "No data loaded to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Mushroom Data File",
            "",
            "Data Files (*.data *.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            self.warehouse.save_table(self.current_table_name, path)
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
        # Use working table if available, otherwise use main table
        table_name = self.working_table_name or self.current_table_name

        if action == insert_action:
            row = rows[0] if rows else len(self.warehouse.get_table(table_name).df)
            self.manual_editor.add_row(table_name, {})  # prompt in real impl
        elif action == delete_action and rows:
            for r in reversed(rows):
                self.manual_editor.delete_row(table_name, r)
        elif action == replace_action and cols:
            col = self.warehouse.get_table(table_name).df.columns[cols[0]]
            # In a real app, prompt for old/new values here
            self.automatic_editor.replace_values(table_name, col, 'old', 'new')

        # Refresh view
        table = self.warehouse.get_table(table_name)
        model = TableModel(table, self.warehouse.schema)
        self.table_view.setModel(model)
        # Reapply delegates
        for idx, col_name in enumerate(table.df.columns):
            delegate = ComboBoxDelegate(col_name, self.warehouse.schema, parent=self.table_view)
            self.table_view.setItemDelegateForColumn(idx, delegate)
        # Update panels with correct table name
        self.stats_panel.set_table(table_name)
        self.subset_panel.set_table(table_name)
        self.status_bar.showMessage("Table updated")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
