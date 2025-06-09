import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QFormLayout, QLabel, QSizePolicy, QGroupBox
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.stats.categorical_stats import categorical_stats
from src.stats.correlation import categorical_correlation
from src.core.table_store import TableStore

class StatsPanel(QWidget):
    def __init__(self, table_store: TableStore, parent=None):
        super().__init__(parent)
        self.table_store = table_store
        self.init_ui()
        # Subscribe to table changes
        self.table_store.add_observer(self.set_table)

    def init_ui(self):
        """Initialize the UI components."""
        # Main layout is now vertical
        main_layout = QVBoxLayout(self)

        # Upper section: stats and histogram (horizontal)
        upper_section = QHBoxLayout()

        # Left side: controls + form
        left = QVBoxLayout()
        self.column_picker = QComboBox()
        self.compute_btn = QPushButton("Compute Statistics")
        self.compute_btn.setEnabled(False)
        self.form = QFormLayout()

        left.addWidget(self.column_picker)
        left.addWidget(self.compute_btn)
        left.addLayout(self.form)
        left.addStretch()

        # Right side: histogram canvas
        self.fig = Figure(figsize=(4,3))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add left and right to upper section
        upper_section.addLayout(left, 1)
        upper_section.addWidget(self.canvas, 2)

        # Add upper section to main layout
        main_layout.addLayout(upper_section)

        # Connect signals
        self.compute_btn.clicked.connect(self.on_compute)

        # Lower section: correlation
        self.corr_group = QGroupBox("Correlation Analysis")
        corr_layout = QVBoxLayout()
        
        # Column selection
        col_select = QHBoxLayout()
        self.col1_combo = QComboBox()
        self.col2_combo = QComboBox()
        col_select.addWidget(QLabel("Column 1:"))
        col_select.addWidget(self.col1_combo)
        col_select.addWidget(QLabel("Column 2:"))
        col_select.addWidget(self.col2_combo)
        
        # Compute button
        self.compute_corr_btn = QPushButton("Compute Correlation")
        self.compute_corr_btn.clicked.connect(self.on_compute_correlation)
        col_select.addWidget(self.compute_corr_btn)
        
        corr_layout.addLayout(col_select)
        
        # Results
        self.corr_result = QLabel()
        self.corr_result.setAlignment(Qt.AlignCenter)
        corr_layout.addWidget(self.corr_result)
        
        self.corr_group.setLayout(corr_layout)
        
        # Add correlation group to main layout
        main_layout.addWidget(self.corr_group)

    def set_table(self, table_name: str):
        """Update panel when active table changes."""
        self.clear_display()
        
        if not table_name:
            return

        try:
            table = self.table_store.get_active_table()
            self.column_picker.addItems(table.df.columns)
            self.compute_btn.setEnabled(True)
            
            # Update correlation combos
            self.col1_combo.clear()
            self.col2_combo.clear()
            if table_name:
                cols = list(self.table_store.get_active_table().df.columns)
                self.col1_combo.addItems(cols)
                self.col2_combo.addItems(cols)

        except (KeyError, ValueError) as e:
            self.compute_btn.setEnabled(False)
            print(f"Error setting table: {e}")

    def clear_display(self):
        """Clear all display elements."""
        self.column_picker.clear()
        self.compute_btn.setEnabled(False)
        
        while self.form.rowCount() > 0:
            self.form.removeRow(0)
            
        self.fig.clear()
        self.canvas.draw()

    def on_compute(self):
        """Compute and display statistics for selected column."""
        if not self.table_store.active_table_name:
            return

        col = self.column_picker.currentText()
        if not col:
            return

        # Clear previous results
        while self.form.rowCount() > 0:
            self.form.removeRow(0)

        try:
            # Get data from table store
            table = self.table_store.get_active_table()
            series = table.df[col]
            stats = categorical_stats(series, self.table_store.schema, col)
            coldef = self.table_store.schema.column_defs[col]

            # Display basic statistics
            self._display_basic_stats(stats, coldef)
            
            # Display frequencies
            self._display_frequencies(stats, coldef)
            
            # Display histogram
            self._display_histogram(stats, coldef, col)

        except Exception as e:
            print(f"Error computing statistics: {e}")

    def _display_basic_stats(self, stats, coldef):
        """Display basic statistics."""
        self.form.addRow("Count:", QLabel(str(stats["count"])))
        self.form.addRow("Unique:", QLabel(str(stats["unique"])))
        mode_labels = [coldef.labels.get(c, str(c)) for c in stats["mode"]]
        self.form.addRow("Mode:", QLabel(", ".join(mode_labels)))

    def _display_frequencies(self, stats, coldef):
        """Display frequency statistics."""
        for code, cnt in stats["freq"].items():
            label = coldef.labels.get(code, str(code))
            pct = stats["pct"][code]
            self.form.addRow(f"{label} (n):", QLabel(str(cnt)))
            self.form.addRow(f"{label} (%):", QLabel(f"{pct:.2f}%"))

    def _display_histogram(self, stats, coldef, col):
        """Display histogram."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        codes = list(stats["freq"].keys())
        counts = [stats["freq"][c] for c in codes]
        labels = [coldef.labels.get(c, str(c)) for c in codes]
        
        ax.bar(labels, counts)
        ax.set_title(f"Distribution of {col}")
        ax.set_ylabel("Count")
        ax.set_xticklabels(labels, rotation=45, ha="right")
        
        self.fig.tight_layout()
        self.canvas.draw()

    def on_compute_correlation(self):
        """Handle correlation computation."""
        if not self.table_store.active_table_name:
            return
            
        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        
        if col1 == col2:
            self.corr_result.setText("Please select different columns")
            return
            
        table = self.table_store.get_active_table()
        corr, p_value = categorical_correlation(
            table.df[col1],
            table.df[col2],
            self.table_store.schema
        )
        
        # Display result with interpretation
        strength = "weak" if corr < 0.3 else "moderate" if corr < 0.6 else "strong"
        self.corr_result.setText(
            f"Cramér's V: {corr:.3f}\n"
            f"({strength} association)\n"
            f"p-value: {p_value:.3e}"
        )