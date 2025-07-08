import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path


class KOPDataTransformer:
    def __init__(self, input_file):
        self.input_file = Path(input_file)
        self.df = pd.read_csv(self.input_file, encoding="utf-8", sep=",", dtype=str)
        self.df.columns = [self._normalize_column(col) for col in self.df.columns]
        self.base_name = self.input_file.stem.replace("dades_escandall ", "")
        self.client, self.ref_projecte = self.base_name.split(" ")
        self.output_dir = Path("dades/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_column(self, name):
        return re.sub(r"[^a-z0-9_]", "_", name.strip().lower().replace(" ", "_"))

    def _cw_to_date(self, cw_string):
        match = re.match(r"cw_(\d{1,2})_(\d{4})", cw_string.lower())
        if match:
            week, year = int(match.group(1)), int(match.group(2))
            return datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date()
        return None

    def _calcular_cavitats(self, text):
        if pd.isna(text):
            return None
        parts = re.findall(r"\d+", str(text))
        return sum(int(x) for x in parts) if parts else None

    def export_all(self):
        self.export_dades_kop()
        self.export_client()
        self.export_embalatge()
        self.export_oferta()
        self.export_ctoferta()
        self.export_matriu()

    def export_dades_kop(self):
        info = {
            "client": self.client,
            "ref_projecte": self.ref_projecte,
            "data_creacio": datetime.today().date(),
            "estat": "ACTIU"  # Placeholder, adaptar si cal
        }
        pd.DataFrame([info]).to_csv(self.output_dir / f"{self.base_name}_dades_KOP.csv", index=False)

    def export_client(self):
        df = pd.DataFrame([{"nom_client": self.client}])
        df.to_csv(self.output_dir / f"{self.base_name}_client.csv", index=False)

    def export_embalatge(self):
        cols_embalatge = [c for c in self.df.columns if any(k in c for k in ["caixa", "palet", "capa", "bossa"])]
        df_emb = self.df[cols_embalatge].copy()
        df_emb.to_csv(self.output_dir / f"{self.base_name}_embalatge.csv", index=False)

    def export_oferta(self):
        cols_oferta = [c for c in self.df.columns if any(k in c for k in ["projecte", "ref_client", "preu", "volum"])]
        df_oferta = self.df[cols_oferta].copy()
        df_oferta["client"] = self.client
        df_oferta["ref_projecte"] = self.ref_projecte
        df_oferta.to_csv(self.output_dir / f"{self.base_name}_oferta.csv", index=False)

    def export_ctoferta(self):
        cols = [c for c in self.df.columns if "component" in c or "tipus" in c or "qtat" in c or "cost" in c]
        df_ct = self.df[cols].copy()
        df_ct.to_csv(self.output_dir / f"{self.base_name}_ctoferta.csv", index=False)

    def export_matriu(self):
        cols_matriu = [c for c in self.df.columns if any(k in c for k in ["matriu", "cicle", "cavitat", "temps", "manteniment"])]
        df_matriu = self.df[cols_matriu].copy()
        if "cavitats" in df_matriu.columns:
            df_matriu["cavitats_num"] = df_matriu["cavitats"].apply(self._calcular_cavitats)
        df_matriu.to_csv(self.output_dir / f"{self.base_name}_matriu.csv", index=False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Ús: python data_transformer.py <path_fitxer_csv>")
        sys.exit(1)

    transformer = KOPDataTransformer(sys.argv[1])
    transformer.export_all()
    print("Transformació completada.")
