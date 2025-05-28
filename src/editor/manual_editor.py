from typing import Dict, Any
import pandas as pd
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable

class ManualEditor:
    def __init__(self, warehouse: DataWarehouse):
        self.warehouse = warehouse

    def _get_table(self, table_name: str) -> DataTable:
        """Get table and ensure it's a DataTable instance"""
        table = self.warehouse.get_table(table_name)
        if isinstance(table, pd.DataFrame):
            table = DataTable(table)
            self.warehouse.tables[table_name] = table
        return table
        
    def edit_cell(self, table_name: str, row_idx: int, column: str, new_value: str) -> None:
        """Edit a single cell value."""
        table = self._get_table(table_name)
        # Validate new value against schema
        if new_value != self.warehouse.schema.missing_code:
            coldef = self.warehouse.schema.column_defs[column]
            if new_value not in coldef.codes:
                raise ValueError(f"Invalid code '{new_value}' for column '{column}'")
        table.edit_value(row_idx, column, new_value)

    def add_row(self, table_name: str, row_data: Dict[str, str]) -> None:
        """Add a new row to the table."""
        table = self._get_table(table_name)
        
        # Create a complete row dict with missing values for non-present columns
        complete_row = {}
        for col in self.warehouse.schema.column_defs:
            if col in row_data:
                complete_row[col] = row_data[col]
            else:
                coldef = self.warehouse.schema.column_defs[col]
                if coldef.allow_missing:
                    complete_row[col] = self.warehouse.schema.missing_code
                else:
                    # For required columns not in subset, use mode or raise error
                    from src.stats.categorical_stats import categorical_stats
                    full_table = self.warehouse.get_table(table_name.split('_')[0])  # Get original table
                    stats = categorical_stats(full_table.df[col], self.warehouse.schema, col)
                    modes = stats.get('mode', [])
                    if not modes:
                        raise ValueError(f"No mode found for required column '{col}'")
                    complete_row[col] = modes[0]

        # Validate the complete row
        self.warehouse.schema.validate_row(complete_row)
        
        # Add only the subset columns
        new_idx = len(table)
        for col in table.df.columns:
            table.edit_value(new_idx, col, complete_row[col])

    def delete_row(self, table_name: str, row_idx: int) -> None:
        """Delete a row from the table by index."""
        table = self._get_table(table_name)
        # Create new table without the deleted row and reset index
        remaining_rows = [i for i in range(len(table)) if i != row_idx]
        new_table = table.select_rows(remaining_rows)
        # Reset index to maintain consecutive numbering
        new_table._df = new_table._df.reset_index(drop=True)
        self.warehouse.tables[table_name] = new_table

    def get_row(self, table_name: str, row_idx: int) -> Dict[str, Any]:
        """Get a row as a dictionary for viewing/editing."""
        table = self._get_table(table_name)
        return table.df.iloc[row_idx].to_dict()