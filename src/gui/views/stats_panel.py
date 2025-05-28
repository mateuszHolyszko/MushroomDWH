# src/gui/views/stats_panel.py
import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QFormLayout, QLabel, QSizePolicy
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.stats.categorical_stats import categorical_stats
from src.core.schema import Schema

class StatsPanel(QWidget):
    def __init__(self, warehouse, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.table_name = None

        # Main layout: horizontal split
        main_layout = QHBoxLayout(self)

        # Left side: controls + form
        left = QVBoxLayout()
        self.column_picker = QComboBox()
        self.compute_btn = QPushButton("Compute Statistics")
        self.form = QFormLayout()

        left.addWidget(self.column_picker)
        left.addWidget(self.compute_btn)
        left.addLayout(self.form)
        left.addStretch()

        # Right side: histogram canvas
        self.fig = Figure(figsize=(4,3))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addLayout(left, 1)
        main_layout.addWidget(self.canvas, 2)

        # Signals
        self.compute_btn.clicked.connect(self.on_compute)

    def set_table(self, table_name):
        """Populate the column picker when a new table is loaded."""
        self.table_name = table_name
        cols = list(self.warehouse.get_table(table_name).df.columns)
        self.column_picker.clear()
        self.column_picker.addItems(cols)
        # Clear form and chart
        while self.form.rowCount() > 0:
            self.form.removeRow(0)
        self.fig.clear()
        self.canvas.draw()

    def on_compute(self):
        if not self.table_name:
            return

        col = self.column_picker.currentText()
        # Clear previous form entries
        while self.form.rowCount() > 0:
            self.form.removeRow(0)

        # Compute categorical stats
        table = self.warehouse.get_table(self.table_name)
        series = table.df[col]
        stats = categorical_stats(series, self.warehouse.schema, col)
        coldef = self.warehouse.schema.column_defs[col]

        # 1) Count, Unique, Mode
        self.form.addRow("Count:", QLabel(str(stats["count"])))
        self.form.addRow("Unique:", QLabel(str(stats["unique"])))
        mode_labels = [coldef.labels.get(c, str(c)) for c in stats["mode"]]
        self.form.addRow("Mode:", QLabel(", ".join(mode_labels)))

        # 2) Frequencies and percents
        for code, cnt in stats["freq"].items():
            label = coldef.labels.get(code, str(code))
            pct = stats["pct"][code]
            self.form.addRow(f"{label} (n):", QLabel(str(cnt)))
            self.form.addRow(f"{label} (%):", QLabel(f"{pct:.2f}%"))

        # 3) Histogram
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
