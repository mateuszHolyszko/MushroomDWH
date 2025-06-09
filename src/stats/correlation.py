import numpy as np
from scipy.stats import chi2_contingency
import pandas as pd
from src.core.schema import Schema

def categorical_correlation(series1: pd.Series, 
                          series2: pd.Series,
                          schema: Schema) -> tuple[float, float]:
    """
    Calculate correlation between two categorical variables using Cramér's V.
    
    Parameters
    ----------
    series1, series2 : pd.Series
        The categorical columns to compare
    schema : Schema
        Schema containing valid codes/labels
        
    Returns
    -------
    float
        Correlation coefficient (0 to 1)
    float
        p-value from chi-square test
    """
    # Create contingency table
    contingency = pd.crosstab(series1, series2)
    
    # Calculate chi-square statistic and p-value
    chi2, p_value, dof, expected = chi2_contingency(contingency)
    
    # Calculate Cramér's V
    n = len(series1)
    min_dim = min(len(np.unique(series1)), len(np.unique(series2))) - 1
    if min_dim == 0:
        return 0.0, p_value
    
    cramers_v = np.sqrt(chi2 / (n * min_dim))
    
    return cramers_v, p_value