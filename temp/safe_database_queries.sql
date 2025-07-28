-- ================================================
-- CONSULTES SQL SEGURES PER EVITAR PROBLEMES D'ENCODING
-- ================================================
-- Aquestes consultes estan dissenyades per evitar errors d'encoding
-- quan es treballa amb caràcters Unicode (com Δ, α, etc.)

-- IMPORTANT: Executar sempre aquestes comandes abans de les consultes
SET CLIENT_ENCODING TO 'UTF8';
SET DateStyle TO 'ISO, DMY';

-- ================================================
-- 1. CONSULTA BROSE SEGURA AMB PRECISIÓ COMPLETA (NOMÉS VALORS VÀLIDS)
-- ================================================
SELECT 
    client,
    element,
    CAST(actual AS DECIMAL(15,6)) as actual_precisio_completa,
    CAST(nominal AS DECIMAL(15,6)) as nominal_precisio_completa,
    CAST(tolerancia_negativa AS DECIMAL(15,6)) as tol_negativa,
    CAST(tolerancia_positiva AS DECIMAL(15,6)) as tol_positiva,
    data_hora,
    id_lot,
    fase
FROM mesuresqualitat 
WHERE client ILIKE '%brose%'
  AND actual IS NOT NULL 
  AND actual != 'NaN'
  AND nominal IS NOT NULL
  AND nominal != 'NaN'
ORDER BY data_hora DESC
LIMIT 50;

-- ================================================
-- 2. ESTADÍSTIQUES DE PRECISIÓ PER CLIENT (NOMÉS VALORS VÀLIDS)
-- ================================================
SELECT 
    client,
    COUNT(*) as total_mesures,
    COUNT(CASE WHEN actual IS NOT NULL AND actual != 'NaN' THEN 1 END) as mesures_valides,
    ROUND(AVG(CASE WHEN actual != 'NaN' THEN CAST(actual AS DECIMAL(15,6)) END), 6) as actual_mitjana,
    ROUND(STDDEV(CASE WHEN actual != 'NaN' THEN CAST(actual AS DECIMAL(15,6)) END), 6) as desviacio_estandard,
    ROUND(MIN(CASE WHEN actual != 'NaN' THEN CAST(actual AS DECIMAL(15,6)) END), 6) as valor_minim,
    ROUND(MAX(CASE WHEN actual != 'NaN' THEN CAST(actual AS DECIMAL(15,6)) END), 6) as valor_maxim
FROM mesuresqualitat 
WHERE client IS NOT NULL 
GROUP BY client
ORDER BY mesures_valides DESC;

-- ================================================
-- 3. BUSCAR ELEMENTS AMB CARÀCTERS ESPECIALS
-- ================================================
SELECT 
    element,
    COUNT(*) as aparicions,
    string_agg(DISTINCT client, ', ') as clients
FROM mesuresqualitat 
WHERE element IS NOT NULL
GROUP BY element
HAVING element ~ '[^[:ascii:]]'  -- Caràcters no-ASCII
ORDER BY aparicions DESC;

-- ================================================
-- 4. CONSULTA DETALLADA AMB TOTS ELS DECIMALS
-- ================================================
-- Aquesta consulta mostra tots els decimals sense arrodoniment
SELECT 
    client,
    id_lot,
    element,
    property,
    actual::text as actual_text_complet,     -- Veure com està emmagatzemat
    nominal::text as nominal_text_complet,
    (actual - nominal) as diferencia,
    CASE 
        WHEN actual BETWEEN (nominal + tolerancia_negativa) AND (nominal + tolerancia_positiva) 
        THEN 'OK' 
        ELSE 'NOK' 
    END as estat_qualitat,
    data_hora
FROM mesuresqualitat 
WHERE client ILIKE '%brose%'
  AND actual IS NOT NULL
  AND nominal IS NOT NULL
ORDER BY ABS(actual - nominal) DESC  -- Ordenar per major diferència
LIMIT 30;

-- ================================================
-- 5. VERIFICAR ENCODING I TIPUS DE DADES
-- ================================================
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale
FROM information_schema.columns 
WHERE table_name = 'mesuresqualitat'
  AND column_name IN ('actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva', 'element', 'client')
ORDER BY column_name;

-- ================================================
-- 6. CONSULTA PER TROBAR PROBLEMES DE PRECISIÓ
-- ================================================
-- Aquesta consulta identifica valors que poden haver perdut precisió
SELECT 
    client,
    element,
    actual,
    LENGTH(actual::text) - LENGTH(TRIM(TRAILING '0' FROM actual::text)) as zeros_finals,
    CASE 
        WHEN actual::text LIKE '%.%' 
        THEN LENGTH(actual::text) - POSITION('.' IN actual::text) 
        ELSE 0 
    END as decimals_actuals
FROM mesuresqualitat 
WHERE client ILIKE '%brose%'
  AND actual IS NOT NULL
  AND actual != TRUNC(actual)  -- Només valors amb decimals
ORDER BY decimals_actuals DESC
LIMIT 20;

-- ================================================
-- 7. EXPORTAR DADES A CSV (executar si cal)
-- ================================================
-- NOTA: Aquesta comanda ha de ser executada amb permisos adequats
-- \copy (SELECT * FROM mesuresqualitat WHERE client ILIKE '%brose%') TO 'brose_data_export.csv' WITH (FORMAT CSV, HEADER, ENCODING 'UTF8');

-- ================================================
-- 8. CONSULTA RESUM PER DIAGNÒSTIC AMB ANÀLISI DE QUALITAT DE DADES
-- ================================================
SELECT 
    'Total registres' as metrica,
    COUNT(*)::text as valor
FROM mesuresqualitat
UNION ALL
SELECT 
    'Registres amb client',
    COUNT(*)::text
FROM mesuresqualitat WHERE client IS NOT NULL
UNION ALL
SELECT 
    'Registres BROSE',
    COUNT(*)::text
FROM mesuresqualitat WHERE client ILIKE '%brose%'
UNION ALL
SELECT 
    'BROSE amb actual vàlid',
    COUNT(*)::text
FROM mesuresqualitat WHERE client ILIKE '%brose%' AND actual IS NOT NULL AND actual != 'NaN'
UNION ALL
SELECT 
    'BROSE amb actual = NaN',
    COUNT(*)::text
FROM mesuresqualitat WHERE client ILIKE '%brose%' AND (actual IS NULL OR actual = 'NaN')
UNION ALL
SELECT 
    'Registres amb elements Unicode',
    COUNT(*)::text
FROM mesuresqualitat WHERE element ~ '[^[:ascii:]]'
ORDER BY metrica;

-- ================================================
-- 9. ANÀLISI ESPECÍFICA DE PROBLEMES BROSE
-- ================================================
SELECT 
    'Problema' as tipus,
    'Descripció' as descripcio,
    'Quantitat' as quantitat
UNION ALL
SELECT 
    'Actual NULL/NaN',
    'Valors actual que són NULL o NaN',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE client ILIKE '%brose%' AND (actual IS NULL OR actual = 'NaN')
UNION ALL
SELECT 
    'Nominal NULL/NaN',
    'Valors nominal que són NULL o NaN', 
    COUNT(*)::text
FROM mesuresqualitat 
WHERE client ILIKE '%brose%' AND (nominal IS NULL OR nominal = 'NaN')
UNION ALL
SELECT 
    'Tots els valors vàlids',
    'Registres amb actual i nominal vàlids',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE client ILIKE '%brose%' 
  AND actual IS NOT NULL AND actual != 'NaN'
  AND nominal IS NOT NULL AND nominal != 'NaN';

-- ================================================
-- 10. TROBAR VALORS AMB MÀXIMA PRECISIÓ (NOMÉS VÀLIDS)
-- ================================================
SELECT 
    client,
    element,
    actual,
    LENGTH(TRIM(TRAILING '0' FROM actual::text)) as longitud_sense_zeros,
    actual::text as valor_complet
FROM mesuresqualitat 
WHERE client ILIKE '%brose%'
  AND actual IS NOT NULL
  AND actual != 'NaN'
  AND LENGTH(actual::text) > 10  -- Valors amb més de 10 caràcters
ORDER BY LENGTH(actual::text) DESC
LIMIT 15;

-- ================================================
-- 11. CONSULTA PER INVESTIGAR EL PROBLEMA DELS NaN
-- ================================================
-- Aquesta consulta t'ajudarà a entendre d'on venen els valors NaN
SELECT 
    element,
    COUNT(*) as total_registres,
    COUNT(CASE WHEN actual IS NOT NULL AND actual != 'NaN' THEN 1 END) as valors_valids,
    COUNT(CASE WHEN actual IS NULL OR actual = 'NaN' THEN 1 END) as valors_nan,
    ROUND(
        (COUNT(CASE WHEN actual IS NOT NULL AND actual != 'NaN' THEN 1 END) * 100.0 / COUNT(*)), 
        2
    ) as percentatge_valids
FROM mesuresqualitat 
WHERE client ILIKE '%brose%'
GROUP BY element
ORDER BY valors_valids DESC
LIMIT 20;
