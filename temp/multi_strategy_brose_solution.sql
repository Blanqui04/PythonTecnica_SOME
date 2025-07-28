-- SOLUCIONS MÚLTIPLES PER PROBLEMES IDENTIFICATS
-- =================================================

-- SEMPRE EXECUTA PRIMER:
SET CLIENT_ENCODING TO 'UTF8';

-- ESTRATÈGIA 1: Si les dades estan en els camps 'actual'/'nominal'
-- ----------------------------------------------------------------
SELECT 
    client,
    element,
    property,
    actual::numeric(15,6) as actual_precision,
    nominal::numeric(15,6) as nominal_precision,
    data_hora::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND actual IS NOT NULL
ORDER BY data_hora DESC
LIMIT 10;

-- ESTRATÈGIA 2: Si les dades estan en 'check_value' (probable!)
-- -------------------------------------------------------------
SELECT 
    client,
    element,
    property,
    check_value as measured_value,
    CASE WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' 
         THEN check_value::numeric(15,6) 
         ELSE NULL END as numeric_value,
    data_hora::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND LENGTH(TRIM(COALESCE(check_value, ''))) > 0
  AND check_value != 'DATUMS D A B-C'
ORDER BY data_hora DESC
LIMIT 10;

-- ESTRATÈGIA 3: Combinada - buscar dades en tots els camps
-- --------------------------------------------------------
SELECT 
    client,
    element,
    property,
    COALESCE(
        CASE WHEN actual IS NOT NULL THEN actual::text END,
        CASE WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' THEN check_value END,
        'No numeric data'
    ) as value_found,
    CASE 
        WHEN actual IS NOT NULL THEN 'actual_field'
        WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' THEN 'check_value_field'
        ELSE 'no_data'
    END as data_source,
    data_hora::date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
ORDER BY data_hora DESC
LIMIT 15;

-- ESTRATÈGIA 4: Estadístiques per identificar millor font de dades
-- ----------------------------------------------------------------
SELECT 
    'Data source analysis' as analysis,
    COUNT(CASE WHEN actual IS NOT NULL THEN 1 END) as actual_count,
    COUNT(CASE WHEN check_value ~ '^-?[0-9]*\.?[0-9]+$' THEN 1 END) as numeric_check_count,
    COUNT(CASE WHEN LENGTH(TRIM(COALESCE(check_value, ''))) > 0 
               AND check_value !~ '^-?[0-9]*\.?[0-9]+$' THEN 1 END) as text_check_count
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%';

-- ESTRATÈGIA 5: Corregir problemes d'encoding en elements
-- -------------------------------------------------------
SELECT 
    client,
    element,
    REPLACE(REPLACE(element, '├│n', 'ón'), '├ÿ', '') as element_fixed,
    property,
    REPLACE(REPLACE(property, '├│n', 'ón'), '├ÿ', '') as property_fixed,
    check_value,
    actual
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND (element LIKE '%├%' OR property LIKE '%├%')
LIMIT 10;

-- NOTA IMPORTANT:
-- Segons l'anàlisi, sembla que les dades numèriques estan principalment
-- en el camp 'check_value' i no en 'actual'/'nominal'.
-- Prova primer l'ESTRATÈGIA 2 per veure els valors mesurats reals.