-- Test query to verify encoding and precision fixes
-- Execute this in your PostgreSQL client

-- First, ensure UTF-8 encoding
SET CLIENT_ENCODING TO 'UTF8';

-- Test 1: Basic BROSE query (should work without encoding errors)
SELECT 
    client,
    element,
    actual,
    nominal,
    data_hora
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_hora DESC
LIMIT 10;

-- Test 2: Check data quality improvements
SELECT 
    'Total BROSE' as metric,
    COUNT(*)::text as value
FROM mesuresqualitat WHERE client LIKE 'BROSE%'
UNION ALL
SELECT 
    'Valid actual values',
    COUNT(*)::text
FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND actual IS NOT NULL
UNION ALL
SELECT 
    'Valid nominal values', 
    COUNT(*)::text
FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND nominal IS NOT NULL;

-- Test 3: Show precision examples
SELECT 
    client,
    element,
    actual::text as actual_full_precision,
    nominal::text as nominal_full_precision,
    (actual - nominal) as difference
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
  AND nominal IS NOT NULL
  AND actual != nominal
ORDER BY ABS(actual - nominal) DESC
LIMIT 10;
