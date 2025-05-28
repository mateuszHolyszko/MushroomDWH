import pandas as pd
from typing import Dict, List, Any
from src.core.schema import Schema

def categorical_stats(
    series: pd.Series,
    schema: Schema,
    col_name: str
) -> Dict[str, Any]:
    """
    Summarize a purely categorical series.

    Returns:
      - count: total non-missing entries
      - unique: number of unique codes (excluding missing)
      - mode: list of most frequent codes
      - freq: dict code→count
      - pct: dict code→relative frequency
    """
    # Map missing marker to NaN so dropna works
    s = series.replace(schema.missing_code, pd.NA).dropna()
    total = len(s)
    vc = s.value_counts()
    if vc.empty:
        return {"count": 0, "unique": 0, "mode": [], "freq": {}, "pct": {}}

    # Mode may be multiple
    max_count = vc.max()
    modes = vc[vc == max_count].index.tolist()

    freq = vc.to_dict()
    pct = (vc / total * 100).round(2).to_dict()

    return {
        "count": total,
        "unique": len(vc),
        "mode": modes,
        "freq": freq,
        "pct": pct
    }
