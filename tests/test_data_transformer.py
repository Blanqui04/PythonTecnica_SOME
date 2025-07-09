import sys
import os
import pytest

# Configura la ruta del projecte
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exceptions.transformation_errors import TransformationError
from src.data_processing.data_transformer import DataTransformer

# ---------- TEST 1: Excepció personalitzada ----------
def test_transformation_error_handling():
    print("Executant test de TransformationError...")
    error_message = "Fitxer mal format!"
    with pytest.raises(TransformationError) as e:
        raise TransformationError(error_message)
    assert str(e.value) == error_message


# ---------- TEST 2: Test funcional del DataTransformer ----------
@pytest.mark.parametrize("client, ref_project", [
    ("ZF", "A027Y916"),  # Exemple de test real
])
def test_transform_datasheet_basic(client, ref_project):
    datasheet_name = f"datasheet_{client}_{ref_project}"
    print(f"Executant test de transformació per {datasheet_name}...")

    try:
        transformer = DataTransformer(client, ref_project)
        result = transformer.transform_datasheet(datasheet_name)

        assert isinstance(result, dict)
        assert 'oferta' in result  # Per exemple
        print("✅ Transformació correcta")

    except TransformationError as te:
        pytest.fail(f"Transformació fallida amb TransformationError: {te}")

    except Exception as e:
        pytest.fail(f"Error inesperat: {e}")


# ---------- Execució manual ----------
if __name__ == "__main__":
    test_transformation_error_handling()
    test_transform_datasheet_basic("ZF", "A027Y916")
    print("✅ Tots els tests s'han executat correctament")

