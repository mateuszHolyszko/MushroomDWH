import pandas as pd
from typing import List, Union
from src.stats.categorical_stats import categorical_stats

class DataTable:
    """
    In-memory representation of a tabular dataset, wrapping a pandas DataFrame
    and providing common data-warehouse operations like subsetting, basic stats,
    and manual edits.
    """
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the DataTable with an existing DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the dataset, with proper column names and types.
        """
        # Store a copy to avoid modifying the original DataFrame
        self._df = df.copy()

    @property
    def df(self) -> pd.DataFrame:
        """Return a copy of the underlying DataFrame."""
        return self._df.copy()

    def select_rows(self, rows: Union[List[int], range]) -> 'DataTable':
        """
        Return a new DataTable containing only the specified rows.

        Parameters
        ----------
        rows : list of int or range
            Row indices (0-based) to include in the subset.
        """
        subset_df = self._df.iloc[rows]
        return DataTable(subset_df)

    def select_columns(self, columns: List[str]) -> 'DataTable':
        """
        Return a new DataTable containing only the specified columns.

        Parameters
        ----------
        columns : list of str
            Column names to include in the subset.
        """
        subset_df = self._df.loc[:, columns]
        return DataTable(subset_df)

    def basic_stats(self, column: str) -> dict:
        series = self._df[column]
        # All values are nominal, so use categorical_stats
        return categorical_stats(series, self.schema, column)

    def edit_value(self, row_idx: int, column: str, new_value) -> None:
        """
        Manually edit a single cell in the DataTable.

        Parameters
        ----------
        row_idx : int
            0-based index of the row to edit.
        column : str
            Name of the column to edit.
        new_value : any
            New value to set in the specified cell.
        """
        self._df.at[row_idx, column] = new_value

    def __len__(self) -> int:
        """Return the number of rows in the table."""
        return len(self._df)

    def __repr__(self) -> str:
        return f"<DataTable rows={len(self)}, columns={list(self._df.columns)}>"
