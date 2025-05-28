from typing import List, Optional, Callable, Union
import pandas as pd
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable
from src.preprocessing.imputer import Imputer

class AutomaticEditor:
    def __init__(self, warehouse: DataWarehouse):
        self.warehouse = warehouse

    def _get_table(self, table_name: str) -> DataTable:
        """Get table and ensure it's a DataTable instance"""
        table = self.warehouse.get_table(table_name)
        if isinstance(table, pd.DataFrame):
            table = DataTable(table)
            self.warehouse.tables[table_name] = table
        return table

    def replace_values(self, table_name: str, column: str, old_value: str, new_value: str) -> None:
        table = self._get_table(table_name)
        # Validate new value
        coldef = self.warehouse.schema.column_defs[column]
        if new_value != self.warehouse.schema.missing_code and new_value not in coldef.codes:
            raise ValueError(f"Invalid code '{new_value}' for column '{column}'")
        
        # Find rows to update using the DataFrame copy
        df = table.df
        rows_to_update = df.index[df[column] == old_value].tolist()
        
        # Update each row individually using DataTable's edit_value
        for row_idx in rows_to_update:
            table.edit_value(row_idx, column, new_value)

    def impute_missing(self, table_name: str, columns: List[str], 
                      strategy: str = 'mode', fill_value: Optional[str] = None) -> None:
        table = self._get_table(table_name)
    
        # Validate strategy and fill_value
        if strategy not in ['mode', 'constant']:
            raise ValueError(f"Invalid strategy: {strategy}")
        if strategy == 'constant' and fill_value is None:
            raise ValueError("fill_value must be provided for constant strategy")
        
        # For constant strategy, validate the fill_value against schema
        if strategy == 'constant':
            for col in columns:
                coldef = self.warehouse.schema.column_defs[col]
                if fill_value not in coldef.codes:
                    raise ValueError(f"Invalid fill_value '{fill_value}' for column '{col}'")
        
        imputer = Imputer(columns, self.warehouse.schema, strategy, fill_value)
        filled_df = imputer.fit_transform(table.df)
    
        # Apply changes through DataTable methods
        for col in columns:
            missing_mask = table.df[col] == self.warehouse.schema.missing_code
            missing_indices = table.df[missing_mask].index
            for idx in missing_indices:
                new_value = filled_df.at[idx, col]
                table.edit_value(idx, col, new_value)

    def apply_function(self, table_name: str, column: str, 
                      func: Callable[[str], str], rows: Optional[List[int]] = None) -> None:
        table = self._get_table(table_name)
        df = table.df
        rows_to_process = rows if rows is not None else range(len(table))
        
        for idx in rows_to_process:
            new_value = func(df.at[idx, column])
            # Validate new value
            if new_value != self.warehouse.schema.missing_code:
                coldef = self.warehouse.schema.column_defs[column]
                if new_value not in coldef.codes:
                    raise ValueError(f"Invalid code '{new_value}' for column '{column}' at row {idx}")
            # Apply change through DataTable method
            table.edit_value(idx, column, new_value)