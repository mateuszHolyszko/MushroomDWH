import pandas as pd
from typing import Union, List, Dict

def basic_stats(
    data: Union[pd.Series, List[Union[int, float, str]]]
) -> Dict[str, float]:
    """
    Compute basic statistics (min, max, mean, median, std, variance) for a numeric or numeric-string series.

    Raises
    ------
    ValueError
        If the input contains no valid numeric values.

    Parameters
    ----------
    data : pd.Series or list
        Sequence of numeric values or strings representing numbers.

    Returns
    -------
    dict
        Dictionary with keys: 'min', 'max', 'mean', 'median', 'std', 'var'.
    """
    # Convert to pandas Series and coerce to numeric
    s = pd.Series(data)
    s = pd.to_numeric(s, errors='coerce')

    # Drop NaNs (non-numeric values)
    valid = s.dropna()
    if valid.empty:
        raise ValueError("No valid numeric values to compute statistics.")

    return {
        'min': float(valid.min()),
        'max': float(valid.max()),
        'mean': float(valid.mean()),
        'median': float(valid.median()),
        'std': float(valid.std()),
        'var': float(valid.var())
    }
