CLIENT_A_COLUMN_MAPPING = {
    'excel_column_name': 'database_column_name',
    'Part_Number': 'part_reference',
    'Customer': 'client_name',
    # ... more mappings
}

# config/column_mappings/__init__.py
from .client_a_mapping import CLIENT_A_COLUMN_MAPPING
from .client_b_mapping import CLIENT_B_COLUMN_MAPPING
from .default_mapping import DEFAULT_COLUMN_MAPPING

COLUMN_MAPPINGS = {
    'client_a': CLIENT_A_COLUMN_MAPPING,
    'client_b': CLIENT_B_COLUMN_MAPPING,
    'default': DEFAULT_COLUMN_MAPPING
}