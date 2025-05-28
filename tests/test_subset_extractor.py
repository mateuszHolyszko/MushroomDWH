import pytest
import pandas as pd
from src.extractor.subset_extractor import SubsetExtractor
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable

@pytest.fixture
def warehouse():
    """Create warehouse with test data"""
    dw = DataWarehouse()
    df = pd.DataFrame({
        'class': ['e', 'p', 'e', 'p', 'e', 'p'],
        'odor': ['n', 'f', 'n', 'f', 'n', 'f'],
        'population': ['s', 'y', 'c', 'y', 's', 'c']
    })
    dw.tables['test'] = DataTable(df)
    return dw

@pytest.fixture
def extractor(warehouse):
    return SubsetExtractor(warehouse)

def test_extract_rows(extractor):
    # Get first 3 rows
    subset = extractor.extract_rows('test', end=3)
    assert len(subset.df) == 3
    
    # Get every other row
    subset = extractor.extract_rows('test', step=2)
    assert len(subset.df) == 3
    assert list(subset.df['class']) == ['e', 'e', 'e']

def test_extract_columns(extractor):
    subset = extractor.extract_columns('test', ['class', 'odor'])
    assert list(subset.df.columns) == ['class', 'odor']
    assert len(subset.df) == 6

def test_extract_by_value(extractor):
    # Single value condition
    subset = extractor.extract_by_value('test', {'class': 'e'})
    assert len(subset.df) == 3
    assert all(subset.df['class'] == 'e')
    
    # Multiple values condition
    subset = extractor.extract_by_value('test', {'population': ['s', 'c']})
    assert len(subset.df) == 4
    assert all(subset.df['population'].isin(['s', 'c']))
    
    # Multiple column conditions
    subset = extractor.extract_by_value('test', {
        'class': 'e',
        'odor': 'n'
    })
    assert len(subset.df) == 3
    assert all(subset.df['class'] == 'e')
    assert all(subset.df['odor'] == 'n')

def test_extract_sample(extractor):
    n = 3
    subset = extractor.extract_sample('test', n, random_state=42)
    assert len(subset.df) == n
    
    # Test reproducibility with random_state
    subset2 = extractor.extract_sample('test', n, random_state=42)
    pd.testing.assert_frame_equal(subset.df, subset2.df)

def test_extract_class_balanced(extractor):
    subset = extractor.extract_class_balanced('test', n_per_class=2)
    assert len(subset.df) == 4  # 2 per class
    
    class_counts = subset.df['class'].value_counts()
    assert class_counts['e'] == 2
    assert class_counts['p'] == 2

def test_extract_more_than_available(extractor):
    # Requesting more rows than available should return all rows
    subset = extractor.extract_sample('test', 1000)
    assert len(subset.df) == 6
    
    # Same for class balanced
    subset = extractor.extract_class_balanced('test', n_per_class=1000)
    assert len(subset.df) == 6