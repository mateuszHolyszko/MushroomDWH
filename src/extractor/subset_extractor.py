from typing import List, Dict, Optional, Union
import pandas as pd
import numpy as np
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable

class SubsetExtractor:
    """
    Extracts subsets of data from warehouse tables based on various criteria.
    """
    def __init__(self, warehouse: DataWarehouse):
        self.warehouse = warehouse

    def extract_rows(self, table_name: str, 
                    start: Optional[int] = None, 
                    end: Optional[int] = None, 
                    step: Optional[int] = None) -> DataTable:
        """
        Extract rows using slice-like indexing.
        """
        table = self.warehouse.get_table(table_name)
        indices = range(len(table))[slice(start, end, step)]
        return table.select_rows(indices)

    def extract_columns(self, table_name: str, columns: List[str]) -> DataTable:
        """
        Extract specific columns.
        """
        table = self.warehouse.get_table(table_name)
        return table.select_columns(columns)

    def extract_by_value(self, table_name: str, 
                        conditions: Dict[str, Union[str, List[str]]]) -> DataTable:
        """
        Extract rows matching specified column values.
        """
        table = self.warehouse.get_table(table_name)
        df = table.df
        
        # Build mask for each condition
        mask = pd.Series([True] * len(df), index=df.index)
        for col, values in conditions.items():
            if isinstance(values, str):
                values = [values]
            col_mask = df[col].isin(values)
            mask = mask & col_mask
            
        return DataTable(df[mask])

    def extract_sample(self, table_name: str, n: int, 
                      random_state: Optional[int] = None) -> DataTable:
        """
        Extract random sample of n rows.
        """
        table = self.warehouse.get_table(table_name)
        df = table.df
        sampled_indices = df.index.to_series().sample(
            n=min(n, len(df)), 
            random_state=random_state
        ).tolist()
        return table.select_rows(sampled_indices)

    def extract_class_balanced(self, table_name: str, n_per_class: int,
                             class_column: str = 'class',
                             random_state: Optional[int] = None) -> DataTable:
        """
        Extract balanced sample with n_per_class rows for each class value.
        """
        table = self.warehouse.get_table(table_name)
        df = table.df
        
        # Sample indices from each class separately
        sampled_indices = []
        for class_val in df[class_column].unique():
            class_indices = df[df[class_column] == class_val].index.tolist()
            n_sample = min(n_per_class, len(class_indices))
            if n_sample > 0:
                rng = np.random.RandomState(random_state)
                selected = rng.choice(class_indices, size=n_sample, replace=False)
                sampled_indices.extend(selected)
                
        return table.select_rows(sampled_indices)