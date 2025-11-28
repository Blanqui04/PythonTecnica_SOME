import pandas as pd
import numpy as np
import os

# Create test data directory
os.makedirs('data/temp/stress_test', exist_ok=True)

# Generate large dimensional analysis dataset (1000 elements, 5 measurements each)
np.random.seed(42)
n_elements = 1000
n_measurements = 5

print("Generating stress test data...")

data = []
for i in range(n_elements):
    element_id = f'ELEMENT_{i:04d}'
    nominal = np.random.uniform(10, 100)
    lower_tol = nominal - np.random.uniform(0.1, 2.0)
    upper_tol = nominal + np.random.uniform(0.1, 2.0)

    # Generate measurements with some variation
    measurements = []
    for j in range(n_measurements):
        measurement = nominal + np.random.normal(0, 0.5)  # Normal distribution around nominal
        measurements.append(round(measurement, 3))

    row = {
        'element_id': element_id,
        'description': f'Test Element {i}',
        'nominal': round(nominal, 3),
        'lower_tolerance': round(lower_tol, 3),
        'upper_tolerance': round(upper_tol, 3),
        'batch': f'BATCH_{i//100:02d}',
        'cavity': str(np.random.randint(1, 5)),
        'class': f'CLASS_{np.random.randint(1, 4)}',
        'datum_element_id': f'DATUM_{np.random.randint(1, 10)}',
        'evaluation_type': 'Normal',
        'measuring_instrument': '3D Scanbox',
        'unit': 'mm'
    }

    # Add measurements
    for j in range(n_measurements):
        row[f'measurement_{j+1}'] = measurements[j]

    data.append(row)

df = pd.DataFrame(data)
df.to_excel('data/temp/stress_test/large_dimensional_test.xlsx', index=False)

file_size_mb = os.path.getsize('data/temp/stress_test/large_dimensional_test.xlsx') / (1024*1024)
print(f'✅ Created stress test data: {len(df)} elements, {len(df.columns)} columns')
print(f'📊 File size: {file_size_mb:.1f} MB')
print(f'📁 File location: data/temp/stress_test/large_dimensional_test.xlsx')