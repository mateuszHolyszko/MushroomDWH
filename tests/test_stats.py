import pytest
import pandas as pd
from src.stats.stats_calculator import basic_stats

@pytest.fixture
def numeric_list():
    return [1, 2, 3, 4, 5]

@pytest.fixture
def mixed_list():
    return ['10', '20', '30', '40', '50']

@pytest.fixture
def nan_list():
    return ['1', 'a', None, '4', '5']


def test_basic_stats_numeric(numeric_list):
    stats = basic_stats(numeric_list)
    assert stats['min'] == 1.0
    assert stats['max'] == 5.0
    assert stats['mean'] == pytest.approx(3.0)
    assert stats['median'] == 3.0
    assert stats['std'] == pytest.approx(pd.Series(numeric_list).std())
    assert stats['var'] == pytest.approx(pd.Series(numeric_list).var())


def test_basic_stats_mixed(mixed_list):
    stats = basic_stats(mixed_list)
    assert stats['min'] == 10.0
    assert stats['max'] == 50.0
    assert stats['mean'] == pytest.approx(30.0)


def test_basic_stats_with_nans(nan_list):
    stats = basic_stats(nan_list)
    # valid numeric are [1,4,5]
    assert stats['min'] == 1.0
    assert stats['max'] == 5.0
    assert stats['mean'] == pytest.approx((1+4+5)/3)
    assert stats['median'] == 4.0


def test_basic_stats_all_invalid():
    with pytest.raises(ValueError):
        basic_stats(['a', 'b', None])  # all coerced to NaN
