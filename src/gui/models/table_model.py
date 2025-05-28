import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from src.core.data_table import DataTable
from src.core.schema import Schema

class TableModel(QAbstractTableModel):
    """
    Qt table model wrapping a DataTable for use in QTableView,
    translating codes via Schema and supporting dropdown delegates.
    """
    def __init__(self, data_table: DataTable, schema: Schema):
        super().__init__()
        self._data_table = data_table
        self._df = data_table.df
        self._schema = schema

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        col_name = self._df.columns[index.column()]
        value = self._df.iat[index.row(), index.column()]
        if role == Qt.DisplayRole:
            if pd.isna(value) or value == self._schema.missing_code:
                return ''
            labels = self._schema.column_defs[col_name].labels
            return labels.get(value, str(value))
        if role == Qt.EditRole:
            # Return underlying code for delegate
            if pd.isna(value) or value == self._schema.missing_code:
                return self._schema.missing_code
            return value
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._df.columns[section]
        else:
            return str(section)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            row = index.row()
            col_name = self._df.columns[index.column()]
            code = value
            self._data_table.edit_value(row, col_name, code)
            self._df = self._data_table.df
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False
