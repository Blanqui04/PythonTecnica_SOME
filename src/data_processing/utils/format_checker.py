import pandas as pd
import os

def load_data_file(filepath):
    ext = os.path.splitext(filepath)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(filepath)
    elif ext == ".json":
        return pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
