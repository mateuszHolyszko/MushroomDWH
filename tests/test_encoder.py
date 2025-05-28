import pandas as pd
import numpy as np
import pytest
from src.core.schema import Schema
from src.preprocessing.encoder import LabelEncoder, OneHotEncoder

@pytest.fixture
def schema():
    return Schema()

@pytest.fixture
def sample_series():
     # Use stalk_root codes including missing and invalid 'q'
     return pd.Series(['b', 'c', '?', 'r', 'q'])
(['b', 'c', '?', 'r', 'z'])  # 'z' is invalid

@pytest.fixture
def sample_df():
    # DataFrame with two categorical columns
    return pd.DataFrame({
        'gill_size': ['b', 'n', 'b', 'n'],  # no missing
        'stalk_root': ['b', 'c', '?', 'r']    # missing allowed
    })


def test_label_encoder_valid(schema):
    le = LabelEncoder('gill_size', schema)
    arr = le.transform(['b', 'n', 'b'])
    # Check that mapping produces ints 0..len(codes)-1
    codes = sorted(schema.column_defs['gill_size'].codes)
    expected = [codes.index(v) for v in ['b', 'n', 'b']]
    assert np.array_equal(arr, expected)


def test_label_encoder_missing_not_allowed(schema):
    le = LabelEncoder('gill_size', schema)
    with pytest.raises(ValueError):
        le.transform(['b', '?'])


def test_label_encoder_missing_allowed(schema):
    le = LabelEncoder('stalk_root', schema)
    arr = le.transform(['?', 'b', 'r'])
    # Missing '?' should map to 0
    assert arr[0] == 0
    # Other codes shift by 1
    assert arr[1] == le.code_to_int['b']


def test_label_encoder_invalid_code(schema, sample_series):
    le = LabelEncoder('stalk_root', schema)
    
    # 'q' is not a valid code, expect ValueError
    with pytest.raises(ValueError):
        le.transform(sample_series)


def test_onehot_encoder_default(sample_df, schema):
    ohe = OneHotEncoder(['gill_size'], schema, drop_first=False)
    df_ohe = ohe.transform(sample_df)
    # Expect 2 cols: gill_size_b, gill_size_n plus original stalk_root
    assert 'gill_size_b' in df_ohe.columns
    assert 'gill_size_n' in df_ohe.columns
    assert 'stalk_root' in df_ohe.columns
    # Check one-hot correctness
    row0 = df_ohe.iloc[0][['gill_size_b', 'gill_size_n']].tolist()
    assert row0 == [1, 0]


def test_onehot_encoder_drop_first(sample_df, schema):
     ohe = OneHotEncoder(['stalk_root'], schema, drop_first=True)
     df_ohe = ohe.transform(sample_df)
     # Original stalk_root gone
     assert 'stalk_root' not in df_ohe.columns
     # Check dummy columns count equals number of codes
     codes = list(schema.column_defs['stalk_root'].codes)
     dummy_cols = [col for col in df_ohe.columns if col.startswith('stalk_root_')]
     assert len(dummy_cols) == len(codes)

