import pandas as pd
from typing import List, Dict, Optional
from src.core.schema import Schema

class Imputer:
    """
    Handles missing values in categorical columns according to a specified strategy.

    Supported strategies:
      - 'mode': replace all values with the most frequent valid code in each column
      - 'constant': replace all values with a provided constant code for each column
    """
    def __init__(
        self,
        columns: List[str],
        schema: Schema,
        strategy: str = 'mode',
        fill_value: Optional[str] = None
    ):
        self.columns = columns
        self.schema = schema
        self.strategy = strategy
        self.fill_value = fill_value
        # After fit, mapping from column to fill code
        self.fill_map: Dict[str, str] = {}

        if self.strategy not in ('mode', 'constant'):
            raise ValueError(f"Unsupported strategy '{self.strategy}'. Use 'mode' or 'constant'.")
        if self.strategy == 'constant':
            if self.fill_value is None:
                raise ValueError("`fill_value` must be provided for constant strategy.")
            # Validate provided fill_value against each column
            for col in self.columns:
                coldef = self.schema.column_defs[col]
                if self.fill_value != self.schema.missing_code and self.fill_value not in coldef.codes:
                    raise ValueError(f"Invalid fill_value '{self.fill_value}' for column '{col}'")

    def fit(self, df: pd.DataFrame) -> 'Imputer':
        """
        Learn fill values for each column based on the strategy.
        For 'mode', compute most frequent valid code.
        For 'constant', use the provided fill_value for all.
        """
        for col in self.columns:
            coldef = self.schema.column_defs[col]
            series = df[col].astype(object)
            # Identify missing markers
            mask_missing = series.isna() | (series == self.schema.missing_code)
            if self.strategy == 'mode':
                # Missing not allowed when computing mode
                if mask_missing.any() and not coldef.allow_missing:
                    raise ValueError(f"Missing code '{self.schema.missing_code}' not allowed for column '{col}' during mode imputation fit.")
                # Count only valid non-missing
                counts = series[~mask_missing].value_counts()
                if counts.empty:
                    raise ValueError(f"Cannot compute mode for column '{col}' with no valid values.")
                self.fill_map[col] = counts.idxmax()
            else:  # constant
                self.fill_map[col] = self.fill_value
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Replace all values in specified columns based on learned fill_map.
        Returns a new DataFrame.
        """
        out = df.copy()
        for col in self.columns:
            if col not in out.columns:
                raise KeyError(f"Column '{col}' not in DataFrame.")
            if col not in self.fill_map:
                raise ValueError(f"Imputer not fitted for column '{col}'.")
            fill_code = self.fill_map[col]
            out[col] = fill_code
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convenience method: fit then transform.
        """
        return self.fit(df).transform(df)
