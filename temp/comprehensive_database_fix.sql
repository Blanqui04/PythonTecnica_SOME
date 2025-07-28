
-- SCRIPT DE CORRECCIÓ COMPLET PER LA TAULA mesuresqualitat
-- Executar pas a pas per evitar problemes

-- 1. CONFIGURAR ENCODING
SET CLIENT_ENCODING TO 'UTF8';
SET DateStyle TO 'ISO, DMY';

-- 2. CORREGIR CARÀCTERS UNICODE PROBLEMÀTICS
UPDATE mesuresqualitat SET element = REPLACE(element, 'Δ', 'Delta') WHERE element LIKE '%Δ%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'α', 'alpha') WHERE element LIKE '%α%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'β', 'beta') WHERE element LIKE '%β%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'γ', 'gamma') WHERE element LIKE '%γ%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'μ', 'mu') WHERE element LIKE '%μ%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'π', 'pi') WHERE element LIKE '%π%';
UPDATE mesuresqualitat SET element = REPLACE(element, 'σ', 'sigma') WHERE element LIKE '%σ%';
UPDATE mesuresqualitat SET element = REPLACE(element, '°', 'deg') WHERE element LIKE '%°%';
UPDATE mesuresqualitat SET element = REPLACE(element, '±', '+/-') WHERE element LIKE '%±%';

-- 3. CORREGIR VALORS NaN I PROBLEMÀTICS
UPDATE mesuresqualitat SET actual = NULL WHERE actual::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET nominal = NULL WHERE nominal::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET tolerancia_negativa = NULL WHERE tolerancia_negativa::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET tolerancia_positiva = NULL WHERE tolerancia_positiva::text IN ('NaN', 'nan', 'Infinity', '-Infinity');
UPDATE mesuresqualitat SET desviacio = NULL WHERE desviacio::text IN ('NaN', 'nan', 'Infinity', '-Infinity');

-- 4. NETEJAR PATRONS PROBLEMÀTICS
UPDATE mesuresqualitat SET element = REPLACE(element, '¿¿¿???', '') WHERE element LIKE '%¿¿¿???%';
UPDATE mesuresqualitat SET element = REPLACE(element, '???', '') WHERE element LIKE '%???%';
UPDATE mesuresqualitat SET element = TRIM(element) WHERE element IS NOT NULL;

-- 5. CONSULTA VERIFICACIÓ FINAL
SELECT 
    'Registres totals' as metric,
    COUNT(*)::text as value
FROM mesuresqualitat
UNION ALL
SELECT 
    'BROSE amb actual vàlid',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%' AND actual IS NOT NULL AND actual::text NOT IN ('NaN', 'nan')
UNION ALL
SELECT 
    'Elements amb Unicode',
    COUNT(*)::text
FROM mesuresqualitat 
WHERE element ~ '[^[:ascii:]]';
