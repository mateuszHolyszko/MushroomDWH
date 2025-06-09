from dataclasses import dataclass
from typing import Dict, Set, Any
import pandas as pd

@dataclass(frozen=True)
class ColumnDef:
    name: str
    codes: Set[str]
    labels: Dict[str, str]
    allow_missing: bool = False

class Schema:
    """
    Encapsulates metadata for the mushroom dataset columns, including valid codes,
    human-readable labels, and missing-value rules. Provides validation methods.
    """
    def __init__(self):
        self.missing_code = '?'
        self.column_defs: Dict[str, ColumnDef] = {
            'class': ColumnDef(
                name='class',
                codes={'e','p'},
                labels={'e':'edible','p':'poisonous'},
                allow_missing=False
            ),
            'cap_shape': ColumnDef(
                name='cap_shape',
                codes={'b','c','x','f','k','s'},
                labels={'b':'bell','c':'conical','x':'convex','f':'flat','k':'knobbed','s':'sunken'}
            ),
            'cap_surface': ColumnDef(
                name='cap_surface',
                codes={'f','g','y','s'},
                labels={'f':'fibrous','g':'grooves','y':'scaly','s':'smooth'}
            ),
            'cap_color': ColumnDef(
                name='cap_color',
                codes={'n','b','c','g','r','p','u','e','w','y'},
                labels={'n':'brown','b':'buff','c':'cinnamon','g':'gray','r':'green','p':'pink','u':'purple','e':'red','w':'white','y':'yellow'}
            ),
            'bruises': ColumnDef(
                name='bruises',
                codes={'t','f'},
                labels={'t':'bruises','f':'no'}
            ),
            'odor': ColumnDef(
                name='odor',
                codes={'a','l','c','y','f','m','n','p','s'},
                labels={'a':'almond','l':'anise','c':'creosote','y':'fishy','f':'foul','m':'musty','n':'none','p':'pungent','s':'spicy'}
            ),
            'gill_attachment': ColumnDef(
                name='gill_attachment',
                codes={'a','d','f','n'},
                labels={'a':'attached','d':'descending','f':'free','n':'notched'}
            ),
            'gill_spacing': ColumnDef(
                name='gill_spacing',
                codes={'c','w','d'},
                labels={'c':'close','w':'crowded','d':'distant'}
            ),
            'gill_size': ColumnDef(
                name='gill_size',
                codes={'b','n'},
                labels={'b':'broad','n':'narrow'}
            ),
            'gill_color': ColumnDef(
                name='gill_color',
                codes={'k','n','b','h','g','r','o','p','u','e','w','y'},
                labels={'k':'black','n':'brown','b':'buff','h':'chocolate','g':'gray','r':'green','o':'orange','p':'pink','u':'purple','e':'red','w':'white','y':'yellow'}
            ),
            'stalk_shape': ColumnDef(
                name='stalk_shape',
                codes={'e','t'},
                labels={'e':'enlarging','t':'tapering'}
            ),
            'stalk_root': ColumnDef(
                name='stalk_root',
                codes={'b','c','u','e','z','r'},
                labels={'b':'bulbous','c':'club','u':'cup','e':'equal','z':'rhizomorphs','r':'rooted'},
                allow_missing=True
            ),
            'stalk_surface_above_ring': ColumnDef(
                name='stalk_surface_above_ring',
                codes={'f','y','k','s'},
                labels={'f':'fibrous','y':'scaly','k':'silky','s':'smooth'}
            ),
            'stalk_surface_below_ring': ColumnDef(
                name='stalk_surface_below_ring',
                codes={'f','y','k','s'},
                labels={'f':'fibrous','y':'scaly','k':'silky','s':'smooth'}
            ),
            'stalk_color_above_ring': ColumnDef(
                name='stalk_color_above_ring',
                codes={'n','b','c','g','o','p','e','w','y'},
                labels={'n':'brown','b':'buff','c':'cinnamon','g':'gray','o':'orange','p':'pink','e':'red','w':'white','y':'yellow'}
            ),
            'stalk_color_below_ring': ColumnDef(
                name='stalk_color_below_ring',
                codes={'n','b','c','g','o','p','e','w','y'},
                labels={'n':'brown','b':'buff','c':'cinnamon','g':'gray','o':'orange','p':'pink','e':'red','w':'white','y':'yellow'}
            ),
            'veil_type': ColumnDef(
                name='veil_type',
                codes={'p','u'},
                labels={'p':'partial','u':'universal'}
            ),
            'veil_color': ColumnDef(
                name='veil_color',
                codes={'n','o','w','y'},
                labels={'n':'brown','o':'orange','w':'white','y':'yellow'}
            ),
            'ring_number': ColumnDef(
                name='ring_number',
                codes={'n','o','t'},
                labels={'n':'none','o':'one','t':'two'}
            ),
            'ring_type': ColumnDef(
                name='ring_type',
                codes={'c','e','f','l','n','p','s','z'},
                labels={'c':'cobwebby','e':'evanescent','f':'flaring','l':'large','n':'none','p':'pendant','s':'sheathing','z':'zone'}
            ),
            'spore_print_color': ColumnDef(
                name='spore_print_color',
                codes={'k','n','b','h','r','o','u','w','y'},
                labels={'k':'black','n':'brown','b':'buff','h':'chocolate','r':'green','o':'orange','u':'purple','w':'white','y':'yellow'}
            ),
            'population': ColumnDef(
                name='population',
                codes={'a','c','n','s','v','y'},
                labels={'a':'abundant','c':'clustered','n':'numerous','s':'scattered','v':'several','y':'solitary'}
            ),
            'habitat': ColumnDef(
                name='habitat',
                codes={'g','l','m','p','u','w','d'},
                labels={'g':'grasses','l':'leaves','m':'meadows','p':'paths','u':'urban','w':'waste','d':'woods'}
            )
        }

    def validate_row(self, row: Any, row_index: int = None) -> None:
        """
        Validate a single record (Series or dict) against column definitions.
        Only validates columns that are present in the row.
        """
        # Only validate columns that exist in the row
        for col in row.keys():
            if col not in self.column_defs:
                raise ValueError(f"Unknown column '{col}' at row {row_index}")
                
            coldef = self.column_defs[col]
            val = row[col]
            
            if pd.isna(val):
                val = self.missing_code  # Convert NaN to missing code '?'
                
            if val == self.missing_code:
                # Always allow missing code '?' for columns that aren't present in subset
                continue
                
            if val not in coldef.codes:
                raise ValueError(f"Invalid code '{val}' for column '{col}' at row {row_index}")

    def validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate an entire DataFrame, row by row.
        Only validates columns that are present in the DataFrame.
        """
        for idx, row in df.iterrows():
            self.validate_row(row, row_index=idx)
