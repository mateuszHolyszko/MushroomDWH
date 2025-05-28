# tests/test_warehouse.py
import pandas as pd
import pytest
from pathlib import Path
from src.core.warehouse import DataWarehouse
from src.core.data_table import DataTable


def test_load_and_list(tmp_path):
    # Create a small .data file and load it
    sample = "e,x,s,n,t,p,f,c,n,k,e,e,s,s,w,w,p,w,o,p,k,s,u\n"
    data_file = tmp_path / "test.data"
    data_file.write_text(sample)

    dw = DataWarehouse()
    dw.load_table('m', data_file)
    assert 'm' in dw.list_tables()
    table = dw.get_table('m')
    assert isinstance(table, DataTable)
    assert len(table) == 1


def test_subset_and_stats(tmp_path):
    df = pd.DataFrame({'a':['1','2','3'], 'b':['x','y','z']})
    dw = DataWarehouse()
    dw.tables['t'] = DataTable(df)

    sub = dw.subset_rows('t', [0,2])
    assert len(sub) == 2
    sub2 = dw.subset_columns('t', ['a'])
    assert list(sub2.df.columns) == ['a']

    stats = dw.compute_stats('t', 'a')
    assert stats['min'] == 1
    assert stats['max'] == 3


def test_edit_and_save(tmp_path):
    df = pd.DataFrame({'a':['1','2'], 'b':['x','y']})
    dw = DataWarehouse()
    dw.tables['t'] = DataTable(df)

    dw.edit_cell('t', 0, 'b', 'z')
    assert dw.get_table('t').df.at[0,'b'] == 'z'

    out_file = tmp_path / 'out.data'
    dw.save_table('t', out_file)
    lines = out_file.read_text().strip().splitlines()
    content = [cell for line in lines for cell in line.split(',')]
    assert content == ['1','z','2','y']


def test_load_invalid_code(tmp_path):
    # Introduce invalid code 'z' in cap_shape
    bad = "e,z,s,n,t,p,f,c,n,k,e,e,s,s,w,w,p,w,o,p,k,s,u\n"
    bad_file = tmp_path / "bad.data"
    bad_file.write_text(bad)

    dw = DataWarehouse()
    with pytest.raises(ValueError):
        dw.load_table('bad', bad_file)