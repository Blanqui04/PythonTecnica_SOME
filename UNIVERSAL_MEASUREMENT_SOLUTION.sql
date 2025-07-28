-- SOLUCIÓN UNIVERSAL PARA TODOS LOS CLIENTES CON MEDICIONES NUMÉRICAS
-- =====================================================================

-- SIEMPRE ejecutar primero:
SET CLIENT_ENCODING TO 'UTF8';

-- ✅ CONSULTA UNIVERSAL: Maneja formatos europeos (comas) y anglosajones (puntos)
SELECT 
    client,
    element,
    property,
    check_value as raw_measurement,
    CASE 
        -- Formato europeo con coma (0,25)
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
            REPLACE(check_value, ',', '.')::numeric(15,6)
        -- Formato anglosajón con punto (0.25)
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
            check_value::numeric(15,6)
        -- Enteros (25)
        WHEN check_value ~ '^-?[0-9]+$' THEN 
            check_value::numeric(15,6)
        -- Si hay datos en 'actual', usarlos también
        WHEN actual IS NOT NULL THEN
            actual::numeric(15,6)
        ELSE NULL
    END as measurement_with_full_precision,
    CASE 
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 'check_value_european'
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 'check_value_anglo'
        WHEN check_value ~ '^-?[0-9]+$' THEN 'check_value_integer'
        WHEN actual IS NOT NULL THEN 'actual_field'
        ELSE 'no_data'
    END as data_source,
    data_hora::date as measurement_date
FROM mesuresqualitat 
WHERE (
    -- Datos numéricos en check_value
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    -- O datos en actual
    OR actual IS NOT NULL
)
  AND check_value != 'DATUMS D A B-C'
ORDER BY client, data_hora DESC
LIMIT 50;

-- ✅ ESTADÍSTICAS POR CLIENTE:
SELECT 
    client,
    COUNT(*) as total_measurements,
    COUNT(CASE WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 1 END) as european_format_count,
    COUNT(CASE WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 1 END) as anglo_format_count,
    COUNT(CASE WHEN actual IS NOT NULL THEN 1 END) as actual_field_count,
    AVG(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN actual IS NOT NULL THEN
                actual::numeric(15,6)
        END
    ) as average_measurement
FROM mesuresqualitat 
WHERE (
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    OR actual IS NOT NULL
)
  AND check_value != 'DATUMS D A B-C'
GROUP BY client
ORDER BY total_measurements DESC;

-- ✅ CONSULTA PARA UN CLIENTE ESPECÍFICO (cambia 'CLIENTE_NOMBRE'):
SELECT 
    client,
    element,
    property,
    check_value as raw_value,
    CASE 
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
            REPLACE(check_value, ',', '.')::numeric(15,6)
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
            check_value::numeric(15,6)
        WHEN check_value ~ '^-?[0-9]+$' THEN 
            check_value::numeric(15,6)
        WHEN actual IS NOT NULL THEN
            actual::numeric(15,6)
    END as precise_measurement,
    data_hora::date
FROM mesuresqualitat 
WHERE client = 'BROSE'  -- Cambia aquí el nombre del cliente
  AND (
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    OR actual IS NOT NULL
  )
  AND check_value != 'DATUMS D A B-C'
ORDER BY data_hora DESC
LIMIT 20;

-- ✅ DISTRIBUCIÓN POR ELEMENTO (todos los clientes):
SELECT 
    client,
    element,
    property,
    COUNT(*) as measurement_count,
    AVG(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN actual IS NOT NULL THEN
                actual::numeric(15,6)
        END
    ) as avg_measurement,
    STDDEV(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN actual IS NOT NULL THEN
                actual::numeric(15,6)
        END
    ) as stddev_measurement
FROM mesuresqualitat 
WHERE (
    check_value ~ '^-?[0-9]+[,.][0-9]+$' 
    OR check_value ~ '^-?[0-9]+$'
    OR actual IS NOT NULL
)
  AND check_value != 'DATUMS D A B-C'
GROUP BY client, element, property
HAVING COUNT(*) >= 5  -- Solo elementos con al menos 5 mediciones
ORDER BY client, measurement_count DESC;

-- NOTA: Esta solución maneja:
-- 1. Formato europeo (comas): 0,25 → 0.250000
-- 2. Formato anglosajón (puntos): 0.25 → 0.250000  
-- 3. Enteros: 25 → 25.000000
-- 4. Datos en campo 'actual' cuando disponibles
-- 5. Precisión completa hasta 6 decimales para todos los clientes