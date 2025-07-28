-- FINAL TEST QUERIES - These should now work perfectly without any encoding errors!

-- Always set encoding first
SET CLIENT_ENCODING TO 'UTF8';

-- Test 1: Basic BROSE query (should work without errors now)
SELECT 
    client,
    element,
    actual,
    nominal,
    tolerancia_negativa,
    tolerancia_positiva,
    data_hora
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_hora DESC
LIMIT 10;

-- Test 2: Full precision decimal display
SELECT 
    client,
    element,
    actual::text as actual_full_precision,
    nominal::text as nominal_full_precision,
    (actual - nominal) as difference_calculated
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
  AND nominal IS NOT NULL
ORDER BY ABS(actual - nominal) DESC
LIMIT 15;

-- Test 3: Statistical analysis with full precision
SELECT 
    client,
    COUNT(*) as total_measurements,
    COUNT(actual) as valid_actual,
    ROUND(AVG(actual), 6) as average_actual,
    ROUND(STDDEV(actual), 6) as stddev_actual,
    ROUND(MIN(actual), 6) as min_actual,
    ROUND(MAX(actual), 6) as max_actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
GROUP BY client;

-- Test 4: Elements analysis (should show clean text now)
SELECT 
    element,
    COUNT(*) as occurrences,
    AVG(actual) as avg_value
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
  AND element IS NOT NULL
GROUP BY element
ORDER BY occurrences DESC
LIMIT 20;

-- Test 5: Quality control analysis
SELECT 
    element,
    COUNT(*) as total,
    COUNT(CASE WHEN actual BETWEEN (nominal + tolerancia_negativa) AND (nominal + tolerancia_positiva) THEN 1 END) as within_tolerance,
    ROUND(
        (COUNT(CASE WHEN actual BETWEEN (nominal + tolerancia_negativa) AND (nominal + tolerancia_positiva) THEN 1 END) * 100.0 / COUNT(*)), 
        2
    ) as percentage_ok
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
  AND nominal IS NOT NULL
  AND tolerancia_negativa IS NOT NULL
  AND tolerancia_positiva IS NOT NULL
GROUP BY element
HAVING COUNT(*) > 10
ORDER BY percentage_ok DESC;

-- Test 6: Verify no encoding issues remain
SELECT 
    'Total BROSE records' as metric,
    COUNT(*)::text as value
FROM mesuresqualitat WHERE client LIKE 'BROSE%'
UNION ALL
SELECT 
    'Valid actual values',
    COUNT(*)::text
FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND actual IS NOT NULL
UNION ALL
SELECT 
    'Clean element names (no special chars)',
    COUNT(*)::text
FROM mesuresqualitat WHERE client LIKE 'BROSE%' AND element IS NOT NULL AND element !~ '[^[:ascii:]]'
UNION ALL
SELECT 
    'Records ready for analysis',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' 
  AND actual IS NOT NULL 
  AND element IS NOT NULL;
