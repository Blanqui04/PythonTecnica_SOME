import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.data_processing.data_transformer import DataTransformer
from src.exceptions import TransformationError

def test_transform_datasheet(client, ref_project):
    datasheet_name = f"datasheet_{client}_{ref_project}"
    print(f"Provant DataTransformer amb client={client}, ref_project={ref_project}, datasheet={datasheet_name}")
    try:
        transformer = DataTransformer(client, ref_project)
        result = transformer.transform_datasheet(datasheet_name)
        print("✅ Transformació correcta:")
        for key, val in result.items():
            print(f"- {key}: {val}")
    except TransformationError as te:
        print(f"❌ Error en la transformació: {te}")
    except Exception as e:
        print(f"❌ Error inesperat: {e}")

if __name__ == "__main__":
    test_transform_datasheet('ADIENT', '5704341')

