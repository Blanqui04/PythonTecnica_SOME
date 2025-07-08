import os
import pandas as pd
from .utils.fragmenter import fragment_dataframe
from .utils.file_writer import write_fragments
from .utils.format_checker import load_data_file

class DataTransformer:
    def __init__(self, input_path, output_path):
        self.input_path = input_path  # arxiu .csv o .json
        self.output_path = output_path  # carpeta on desar els fragments

    def transform(self):
        # Carrega l'arxiu en DataFrame
        df = load_data_file(self.input_path)

        # Fragmenta en subconjunts lògics
        fragments = fragment_dataframe(df)

        # Escriu cada fragment a fitxers
        write_fragments(fragments, self.output_path)
