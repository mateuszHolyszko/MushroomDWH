import pandas as pd
import pytest
from src.core.schema import Schema
from src.preprocessing.imputer import Imputer

@pytest.fixture
def schema():
    return Schema()

@pytest.fixture
def sample_df():
    # DataFrame with missing codes and valid codes
    return pd.DataFrame({
        'stalk_root': ['b', '?', 'b', 'r', '?'],  # missing allowed
        'cap_shape': ['x', 'c', 'x', '?', 'b']      # missing not allowed
    })


def test_mode_imputer(schema, sample_df):
    imp = Imputer(['stalk_root'], schema, strategy='mode')
    df_filled = imp.fit_transform(sample_df)
    # Most frequent among ['b','b','r'] is 'b'
    assert all(df_filled['stalk_root'] == 'b')
    # Ensure fill_map recorded correctly
    assert imp.fill_map['stalk_root'] == 'b'


def test_constant_imputer_valid(schema, sample_df):
    imp = Imputer(['stalk_root'], schema, strategy='constant', fill_value='r')
    df_filled = imp.fit_transform(sample_df)
    # All entries replaced with 'r'
    assert all(df_filled['stalk_root'] == 'r')


def test_constant_imputer_invalid_fill(schema):
    # 'q' is not a valid code for stalk_root
    with pytest.raises(ValueError):
        Imputer(['stalk_root'], schema, strategy='constant', fill_value='q')


def test_imputer_on_missing_not_allowed(schema, sample_df):
    # Attempting to fit 'cap_shape' mode imputer should error due to missing '?'
    imp = Imputer(['cap_shape'], schema, strategy='mode')
    with pytest.raises(ValueError):
        imp.fit(sample_df)


def test_transform_without_fit(schema, sample_df):
    imp = Imputer(['stalk_root'], schema, strategy='mode')
    with pytest.raises(ValueError):
        imp.transform(sample_df)


def test_transform_missing_column(schema, sample_df):
    imp = Imputer(['nonexistent'], schema, strategy='mode')
    imp.fill_map = {}  # simulate fit
    with pytest.raises(KeyError):
        imp.transform(sample_df)
