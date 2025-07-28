-- CONSULTES DE TEST PER BROSE AMB ENCODING UTF8 FORÇAT
-- =====================================================

-- IMPORTANT: Executa SEMPRE aquestes dues linies primer:
SET CLIENT_ENCODING TO 'UTF8';
\encoding UTF8

-- 1. Comptar registres BROSE totals
SELECT COUNT(*) as total_brose_records 
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';

-- 2. Mostrar exemples amb tots els decimals
SELECT 
    client,
    element,
    actual::numeric(15,6) as actual_full_precision,
    nominal::numeric(15,6) as nominal_full_precision,
    "tol -"::numeric(15,6) as tol_minus_full,
    "tol +"::numeric(15,6) as tol_plus_full
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND actual IS NOT NULL 
  AND actual != ''
LIMIT 10;

-- 3. Estadístiques amb precisió completa
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN actual IS NOT NULL AND actual != '' THEN 1 END) as records_with_actual,
    AVG(actual::numeric(15,6)) as avg_actual_full_precision,
    STDDEV(actual::numeric(15,6)) as stddev_actual_full_precision,
    MIN(actual::numeric(15,6)) as min_actual,
    MAX(actual::numeric(15,6)) as max_actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';

-- 4. Verificar que no hi ha problemes d'encoding
SELECT 
    'Records with non-ASCII characters' as check_type,
    COUNT(*) as count
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND element ~ '[^[:ascii:]]'
UNION ALL
SELECT 
    'Records with Greek Delta (Δ)' as check_type,
    COUNT(*) as count
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND element LIKE '%Δ%'
UNION ALL  
SELECT 
    'Records with problematic patterns' as check_type,
    COUNT(*) as count
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND (element LIKE '%¿¿¿%' OR element LIKE '%???%' OR element = 'nan');

-- 5. Mostrar distribució per element BROSE
SELECT 
    element,
    COUNT(*) as record_count,
    AVG(actual::numeric(15,6)) as avg_actual,
    COUNT(CASE WHEN actual IS NOT NULL AND actual != '' THEN 1 END) as valid_actual_count
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
GROUP BY element
ORDER BY record_count DESC
LIMIT 20;

-- 6. Test final: Tots els camps amb precisió decimal
SELECT 
    id,
    client,
    projecte,
    element,
    caracteristica,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    "tol -"::numeric(15,6) as tol_minus_precision,
    "tol +"::numeric(15,6) as tol_plus_precision,
    ordre_operacio,
    data_mesura::date as mesura_date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND actual IS NOT NULL 
  AND actual != ''
  AND actual::numeric(15,6) BETWEEN -100 AND 100  -- Filtrar valors raonables
ORDER BY data_mesura DESC, id DESC
LIMIT 20;
