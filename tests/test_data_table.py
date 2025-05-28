import pandas as pd
import pytest
from src.core.data_table import DataTable

@pytest.fixture
def sample_df():
    # Create a sample DataFrame with both numeric and categorical data
    data = {
        'numeric': [1, 2, 3, 4, 5],
        'categorical': ['a', 'b', 'a', 'c', 'b'],
        'mixed_numeric': ['10', '20', '30', '40', '50']
    }
    return pd.DataFrame(data)

@pytest.fixture
def data_table(sample_df):
    return DataTable(sample_df)


def test_len_and_repr(data_table):
    assert len(data_table) == 5
    rep = repr(data_table)
    assert 'rows=5' in rep and 'columns=[' in rep


def test_select_rows(data_table, sample_df):
    # Select a subset of rows
    subset = data_table.select_rows([0, 2, 4])
    assert isinstance(subset, DataTable)
    assert len(subset) == 3
    expected = sample_df.iloc[[0, 2, 4]].reset_index(drop=True)
    pd.testing.assert_frame_equal(subset.df.reset_index(drop=True), expected)


def test_select_columns(data_table, sample_df):
    # Select specific columns
    subset = data_table.select_columns(['numeric', 'categorical'])
    assert isinstance(subset, DataTable)
    assert subset.df.shape == (5, 2)
    assert list(subset.df.columns) == ['numeric', 'categorical']


def test_basic_stats_numeric(data_table):
    # Test stats on numeric column
    stats = data_table.basic_stats('numeric')
    assert stats['min'] == 1
    assert stats['max'] == 5
    assert stats['median'] == 3
    assert set(stats['mode']) == {1, 2, 3, 4, 5}
    assert pytest.approx(stats['std']) == pd.Series([1,2,3,4,5]).std()
    assert pytest.approx(stats['var']) == pd.Series([1,2,3,4,5]).var()


def test_basic_stats_mixed_numeric(data_table):
    # Test stats on column of numeric strings
    stats = data_table.basic_stats('mixed_numeric')
    assert stats['min'] == 10
    assert stats['max'] == 50
    assert stats['median'] == 30
    assert set(stats['mode']) == {10, 20, 30, 40, 50}



def test_basic_stats_nonexistent_column(data_table):
    # Requesting stats on a missing column should raise KeyError
    with pytest.raises(KeyError):
        data_table.basic_stats('nonexistent')


def test_edit_value_and_persistence(data_table):
    # Edit a single value and ensure it persists
    data_table.edit_value(0, 'categorical', 'z')
    assert data_table.df.at[0, 'categorical'] == 'z'


def test_df_property_returns_copy(data_table):
    # Modifications to returned df shouldn't affect internal state
    df_copy = data_table.df
    df_copy.at[0, 'numeric'] = 999
    assert data_table.df.at[0, 'numeric'] != 999
