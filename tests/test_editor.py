import pandas as pd
import pytest
from src.core.warehouse import DataWarehouse
from src.editor.manual_editor import ManualEditor
from src.editor.automatic_editor import AutomaticEditor

@pytest.fixture
def warehouse():
    """Create a warehouse with sample mushroom data"""
    dw = DataWarehouse()
    # Create DataFrame with all required columns from schema
    df = pd.DataFrame({
        'class': ['e', 'p', 'e'],
        'cap_shape': ['b', 'x', 'x'],
        'cap_surface': ['s', 'y', 'f'],
        'cap_color': ['n', 'w', 'g'],
        'bruises': ['t', 'f', 't'],
        'odor': ['n', 'f', 'n'],
        'gill_attachment': ['f', 'f', 'f'],
        'gill_spacing': ['c', 'w', 'c'],
        'gill_size': ['n', 'b', 'b'],
        'gill_color': ['k', 'n', 'n'],
        'stalk_shape': ['e', 't', 'e'],
        'stalk_root': ['b', '?', 'r'],
        'stalk_surface_above_ring': ['s', 'k', 's'],
        'stalk_surface_below_ring': ['s', 'k', 's'],
        'stalk_color_above_ring': ['w', 'w', 'w'],
        'stalk_color_below_ring': ['w', 'w', 'w'],
        'veil_type': ['p', 'p', 'p'],
        'veil_color': ['w', 'w', 'w'],
        'ring_number': ['o', 'o', 'o'],
        'ring_type': ['p', 'p', 'p'],
        'spore_print_color': ['k', 'n', 'n'],
        'population': ['s', 'y', 'c'],
        'habitat': ['u', 'g', 'm']
    })
    dw.tables['test'] = df
    return dw

@pytest.fixture
def manual_editor(warehouse):
    return ManualEditor(warehouse)

@pytest.fixture
def auto_editor(warehouse):
    return AutomaticEditor(warehouse)

# Manual Editor Tests
def test_edit_cell(manual_editor):
    manual_editor.edit_cell('test', 0, 'odor', 'p')
    assert manual_editor.warehouse.get_table('test').df.at[0, 'odor'] == 'p'

def test_edit_cell_invalid_code(manual_editor):
    with pytest.raises(ValueError):
        manual_editor.edit_cell('test', 0, 'odor', 'x')

def test_add_row(manual_editor):
    new_row = {
        'class': 'e',
        'cap_shape': 'x',
        'cap_surface': 's',
        'cap_color': 'n',
        'bruises': 't',
        'odor': 'n',
        'gill_attachment': 'f',
        'gill_spacing': 'c',
        'gill_size': 'n',
        'gill_color': 'k',
        'stalk_shape': 'e',
        'stalk_root': 'b',
        'stalk_surface_above_ring': 's',
        'stalk_surface_below_ring': 's',
        'stalk_color_above_ring': 'w',
        'stalk_color_below_ring': 'w',
        'veil_type': 'p',
        'veil_color': 'w',
        'ring_number': 'o',
        'ring_type': 'p',
        'spore_print_color': 'k',
        'population': 's',
        'habitat': 'u'
    }
    manual_editor.add_row('test', new_row)
    table = manual_editor.warehouse.get_table('test')
    assert len(table.df) == 4
    assert table.df.iloc[-1]['class'] == 'e'

def test_add_row_invalid_data(manual_editor):
    invalid_row = {k: 'x' for k in manual_editor.warehouse.schema.column_defs.keys()}
    with pytest.raises(ValueError):
        manual_editor.add_row('test', invalid_row)

def test_delete_row(manual_editor):
    manual_editor.delete_row('test', 1)
    table = manual_editor.warehouse.get_table('test')
    assert len(table.df) == 2
    assert table.df.index.tolist() == [0, 1]

def test_get_row(manual_editor):
    row = manual_editor.get_row('test', 0)
    assert isinstance(row, dict)
    assert row['class'] == 'e'
    assert row['odor'] == 'n'

# Automatic Editor Tests
def test_replace_values(auto_editor):
    auto_editor.replace_values('test', 'odor', 'n', 'a')
    table = auto_editor.warehouse.get_table('test')
    assert all(x != 'n' for x in table.df['odor'])
    assert any(x == 'a' for x in table.df['odor'])

def test_replace_values_invalid_code(auto_editor):
    with pytest.raises(ValueError):
        auto_editor.replace_values('test', 'odor', 'n', 'x')

def test_impute_missing_mode(auto_editor):
    auto_editor.impute_missing('test', ['stalk_root'], strategy='mode')
    table = auto_editor.warehouse.get_table('test')
    assert '?' not in table.df['stalk_root'].values

def test_impute_missing_constant(auto_editor):
    auto_editor.impute_missing('test', ['stalk_root'], 
                             strategy='constant', 
                             fill_value='b')
    table = auto_editor.warehouse.get_table('test')
    # Check that no missing values remain
    assert '?' not in table.df['stalk_root'].values
    # Check that missing values were replaced with 'b'
    original_missing_indices = table.df[table.df['stalk_root'] == '?'].index
    for idx in original_missing_indices:
        assert table.df.at[idx, 'stalk_root'] == 'b'

def test_impute_missing_invalid_strategy(auto_editor):
    with pytest.raises(ValueError):
        auto_editor.impute_missing('test', ['stalk_root'], strategy='invalid')

def test_apply_function(auto_editor):
    func = lambda x: 'v' if x == 'y' else x
    auto_editor.apply_function('test', 'population', func)
    table = auto_editor.warehouse.get_table('test')
    assert 'y' not in table.df['population'].values
    assert 'v' in table.df['population'].values

def test_apply_function_invalid_result(auto_editor):
    func = lambda x: 'x'
    with pytest.raises(ValueError):
        auto_editor.apply_function('test', 'population', func)

def test_apply_function_specific_rows(auto_editor):
    func = lambda x: 'v' if x == 's' else x
    auto_editor.apply_function('test', 'population', func, rows=[0])
    table = auto_editor.warehouse.get_table('test')
    assert table.df.at[0, 'population'] == 'v'
    assert table.df.at[1, 'population'] == 'y'