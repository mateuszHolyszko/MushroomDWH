from pathlib import Path
import pandas as pd

def write_mushroom_data(
    df: pd.DataFrame,
    file_path: Path
) -> None:
    """
    Writes a DataFrame to a .data or .csv file without headers or index.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to write.
    file_path : Path
        Destination file path.
    """
    df.to_csv(
        file_path,
        index=False,
        header=False
    )