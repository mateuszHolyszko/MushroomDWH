from typing import List, Union
import pandas as pd
import numpy as np
from src.core.schema import Schema, ColumnDef

class LabelEncoder:
    """
    Maps categorical codes of a single column to integer labels based on Schema.
    """
    def __init__(self, column: str, schema: Schema):
        self.column = column
        self.schema = schema
        coldef: ColumnDef = self.schema.column_defs[column]
        # Use sorted order for deterministic mapping
        codes = sorted(coldef.codes)
        # Reserve index 0 for missing if allowed
        if coldef.allow_missing:
            codes = [self.schema.missing_code] + codes
        # Build code→int mapping
        self.code_to_int = {code: idx for idx, code in enumerate(codes)}
        self.int_to_code = {idx: code for code, idx in self.code_to_int.items()}

    def transform(self, series: Union[pd.Series, List[str]]) -> np.ndarray:
        """
        Transform a series of codes into integer labels.

        Missing, unknown, or NaN values map to 0 if allowed, else raise.
        """
        s = pd.Series(series, dtype=object)
        result = []
        for val in s:
            if pd.isna(val) or val == self.schema.missing_code:
                if self.schema.column_defs[self.column].allow_missing:
                    result.append(self.code_to_int[self.schema.missing_code])
                else:
                    raise ValueError(f"Missing not allowed for column '{self.column}'")
            else:
                if val not in self.schema.column_defs[self.column].codes:
                    raise ValueError(f"Invalid code '{val}' for column '{self.column}'")
                result.append(self.code_to_int[val])
        return np.array(result, dtype=int)

class OneHotEncoder:
    """
    Produces one-hot encoded DataFrame for specified columns based on Schema.
    """
    def __init__(self, columns: List[str], schema: Schema, drop_first: bool = False):
        self.columns = columns
        self.schema = schema
        self.drop_first = drop_first

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform specified categorical columns into one-hot columns.

        Returns a new DataFrame with original columns dropped and new dummy columns added.
        """
        out = df.copy()
        for col in self.columns:
            coldef = self.schema.column_defs[col]
            # Determine levels: sorted codes, include missing at front if allowed
            levels = sorted(coldef.codes)
            if coldef.allow_missing:
                levels = [self.schema.missing_code] + levels
            # Create dummy DataFrame for this column
            dummies = pd.get_dummies(out[col], prefix=col)
            # Ensure all levels present
            expected_cols = [f"{col}_{lvl}" for lvl in levels]
            for exp in expected_cols:
                if exp not in dummies.columns:
                    dummies[exp] = 0
            # Optionally drop first level to avoid collinearity
            drop_cols = []
            if self.drop_first and levels:
                # drop the first expected_cols entry
                drop_cols = [expected_cols[0]]
            keep_cols = [c for c in expected_cols if c not in drop_cols]
            # Reorder columns
            dummies = dummies[keep_cols]
            out = pd.concat([out.drop(columns=[col]), dummies], axis=1)
        return out
