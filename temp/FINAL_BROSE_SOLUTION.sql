-- SOLUCIÓ FINAL DEFINITIVA PER BROSE
-- ====================================

-- SEMPRE executa primer:
SET CLIENT_ENCODING TO 'UTF8';

-- ✅ CONSULTA QUE FUNCIONA I MOSTRA TOTS ELS DECIMALS:
SELECT 
    actual::numeric(15,6) as actual_full_decimals,
    nominal::numeric(15,6) as nominal_full_decimals
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
LIMIT 5;

-- ✅ CONSULTA COMPLETA AMB CONTEXT:
SELECT 
    client,
    element,
    caracteristica,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    "tol -"::numeric(15,6) as tolerance_minus,
    "tol +"::numeric(15,6) as tolerance_plus,
    data_mesura::date as measurement_date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_mesura DESC
LIMIT 10;

-- ✅ ESTADÍSTIQUES AMB PRECISIÓ COMPLETA:
SELECT 
    'BROSE Statistics' as description,
    COUNT(*) as total_records,
    COUNT(actual) as valid_actual_values,
    AVG(actual::numeric(15,6)) as average_with_full_precision,
    STDDEV(actual::numeric(15,6)) as stddev_with_full_precision,
    MIN(actual::numeric(15,6)) as minimum_value,
    MAX(actual::numeric(15,6)) as maximum_value
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';

-- NOTA: Aquestes consultes mostren TOTS els decimals (fins a 6 posicions)
-- El problema era que el teu client estava configurat amb WIN1252 en lloc d'UTF8