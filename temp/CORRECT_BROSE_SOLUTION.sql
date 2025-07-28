-- SOLUCIÓN CORRECTA PARA DATOS BROSE CON DECIMALES COMPLETOS
-- ===========================================================

-- SIEMPRE ejecutar primero:
SET CLIENT_ENCODING TO 'UTF8';

-- ✅ CONSULTA CORRECTA: Los datos están en 'check_value' con comas como decimales
SELECT 
    client,
    element,
    property,
    check_value as raw_measurement,
    CASE 
        WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
            REPLACE(check_value, ',', '.')::numeric(15,6)
        WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
            check_value::numeric(15,6)
        WHEN check_value ~ '^-?[0-9]+$' THEN 
            check_value::numeric(15,6)
        ELSE NULL
    END as measurement_with_full_precision,
    data_hora::date as measurement_date
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND LENGTH(TRIM(COALESCE(check_value, ''))) > 0
  AND check_value != 'DATUMS D A B-C'
  AND (check_value ~ '^-?[0-9]+,[0-9]+$' 
       OR check_value ~ '^-?[0-9]+\.[0-9]+$'
       OR check_value ~ '^-?[0-9]+$')
ORDER BY data_hora DESC
LIMIT 10;

-- ✅ ESTADÍSTICAS CON PRECISIÓN COMPLETA:
SELECT 
    'BROSE Measurements from check_value' as description,
    COUNT(*) as total_numeric_measurements,
    AVG(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
        END
    ) as average_with_full_precision,
    STDDEV(
        CASE 
            WHEN check_value ~ '^-?[0-9]+,[0-9]+$' THEN 
                REPLACE(check_value, ',', '.')::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+\.[0-9]+$' THEN 
                check_value::numeric(15,6)
            WHEN check_value ~ '^-?[0-9]+$' THEN 
                check_value::numeric(15,6)
        END
    ) as stddev_with_full_precision
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND (check_value ~ '^-?[0-9]+,[0-9]+$' 
       OR check_value ~ '^-?[0-9]+\.[0-9]+$'
       OR check_value ~ '^-?[0-9]+$');

-- ✅ DISTRIBUCIÓN POR ELEMENTO:
SELECT 
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
        END
    ) as avg_measurement
FROM mesuresqualitat 
WHERE client LIKE 'BROSE%'
  AND (check_value ~ '^-?[0-9]+,[0-9]+$' 
       OR check_value ~ '^-?[0-9]+\.[0-9]+$'
       OR check_value ~ '^-?[0-9]+$')
GROUP BY element, property
ORDER BY measurement_count DESC
LIMIT 15;
