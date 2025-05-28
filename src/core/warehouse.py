# src/core/warehouse.py
from pathlib import Path
from typing import List, Dict, Union
from src.io.reader import read_mushroom_data
from src.io.writer import write_mushroom_data
from src.core.data_table import DataTable
from src.core.schema import Schema

class DataWarehouse:
    """
    Orchestrator for loading, accessing, editing, and persisting multiple DataTable instances,
    with schema validation.
    """
    def __init__(self):
        self.schema = Schema()
        self.tables: Dict[str, DataTable] = {}

    def load_table(self, name: str, file_path: Union[str, Path]) -> None:
        """
        Loads a .data file into a DataTable stored under the given name,
        validating against the schema.
        """
        df = read_mushroom_data(file_path)
        # Validate data against schema
        self.schema.validate_dataframe(df)
        self.tables[name] = DataTable(df)

    def get_table(self, name: str) -> DataTable:
        """Retrieve the DataTable by name."""
        if name not in self.tables:
            raise KeyError(f"Table '{name}' not found in warehouse.")
        return self.tables[name]

    def list_tables(self) -> List[str]:
        """List all loaded table names."""
        return list(self.tables.keys())

    def save_table(self, name: str, file_path: Union[str, Path]) -> None:
        """
        Persist the specified table to disk using writer.
        """
        table = self.get_table(name)
        write_mushroom_data(table.df, Path(file_path))

    # Convenience methods forwarding to DataTable:
    def subset_rows(self, name: str, rows: Union[List[int], range]) -> DataTable:
        return self.get_table(name).select_rows(rows)

    def subset_columns(self, name: str, columns: List[str]) -> DataTable:
        return self.get_table(name).select_columns(columns)

    def compute_stats(self, name: str, column: str) -> dict:
        return self.get_table(name).basic_stats(column)

    def edit_cell(self, name: str, row_idx: int, column: str, new_value) -> None:
        # Optionally validate single value on edit
        if isinstance(new_value, str) and new_value != self.schema.missing_code:
            coldef = self.schema.column_defs.get(column)
            if coldef and new_value not in coldef.codes:
                raise ValueError(f"Invalid code '{new_value}' for column '{column}'")
        self.get_table(name).edit_value(row_idx, column, new_value)