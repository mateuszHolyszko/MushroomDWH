import pandas as pd
from pathlib import Path
from typing import Union

# Column names corresponding to the 23 attributes (including class)
COLUMN_NAMES = [
    'class',                  # edible=e, poisonous=p
    'cap_shape',             # bell=b, conical=c, convex=x, flat=f, knobbed=k, sunken=s
    'cap_surface',           # fibrous=f, grooves=g, scaly=y, smooth=s
    'cap_color',             # brown=n, buff=b, cinnamon=c, gray=g, green=r, pink=p, purple=u, red=e, white=w, yellow=y
    'bruises',               # bruises=t, no=f
    'odor',                  # almond=a, anise=l, creosote=c, fishy=y, foul=f, musty=m, none=n, pungent=p, spicy=s
    'gill_attachment',       # attached=a, descending=d, free=f, notched=n
    'gill_spacing',          # close=c, crowded=w, distant=d
    'gill_size',             # broad=b, narrow=n
    'gill_color',            # black=k, brown=n, buff=b, chocolate=h, gray=g, green=r, orange=o, pink=p, purple=u, red=e, white=w, yellow=y
    'stalk_shape',           # enlarging=e, tapering=t
    'stalk_root',            # bulbous=b, club=c, cup=u, equal=e, rhizomorphs=z, rooted=r, missing=?
    'stalk_surface_above_ring',  # fibrous=f, scaly=y, silky=k, smooth=s
    'stalk_surface_below_ring',  # fibrous=f, scaly=y, silky=k, smooth=s
    'stalk_color_above_ring',    # brown=n, buff=b, cinnamon=c, gray=g, orange=o, pink=p, red=e, white=w, yellow=y
    'stalk_color_below_ring',    # brown=n, buff=b, cinnamon=c, gray=g, orange=o, pink=p, red=e, white=w, yellow=y
    'veil_type',             # partial=p, universal=u
    'veil_color',            # brown=n, orange=o, white=w, yellow=y
    'ring_number',           # none=n, one=o, two=t
    'ring_type',             # cobwebby=c, evanescent=e, flaring=f, large=l, none=n, pendant=p, sheathing=s, zone=z
    'spore_print_color',     # black=k, brown=n, buff=b, chocolate=h, green=r, orange=o, purple=u, white=w, yellow=y
    'population',            # abundant=a, clustered=c, numerous=n, scattered=s, several=v, solitary=y
    'habitat'                # grasses=g, leaves=l, meadows=m, paths=p, urban=u, waste=w, woods=d
]


def read_mushroom_data(
    file_path: Union[str, Path],
    na_values: list = ['?']
) -> pd.DataFrame:
    """
    Reads the Agaricus-Lepiota mushroom dataset from a .data file into a pandas DataFrame.

    Parameters
    ----------
    file_path : str or Path
        Path to the .data file containing mushroom records, comma-delimited.
    na_values : list, optional
        List of strings to interpret as missing values (default is ['?']).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns defined in COLUMN_NAMES, and missing values as NaN.
    """
    # Ensure file exists
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Mushroom data file not found: {file_path}")

    # Read CSV without header, assign custom names, treat '?' as NaN
    df = pd.read_csv(
        path,
        header=None,
        names=COLUMN_NAMES,
        na_values=na_values,
        dtype=str  # keep all values as strings for categorical processing
    )

    return df


if __name__ == '__main__':
    # Quick smoke test
    df = read_mushroom_data('data/agaricus-lepiota.data')
    print(f"Loaded {len(df)} records with columns: {list(df.columns)}")
