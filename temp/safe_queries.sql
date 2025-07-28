-- Consultes SQL segures per evitar problemes d'encoding
-- Generat automàticament per fix_database_encoding.py

-- CONSULTA_BROSE_SEGURA

                -- Consulta segura per dades BROSE
                SET CLIENT_ENCODING TO 'UTF8';
                SELECT 
                    client,
                    element,
                    ROUND(actual::numeric, 6) as actual_precis,
                    ROUND(nominal::numeric, 6) as nominal_precis,
                    ROUND(tolerancia_negativa::numeric, 6) as tol_neg,
                    ROUND(tolerancia_positiva::numeric, 6) as tol_pos,
                    data_hora
                FROM mesuresqualitat 
                WHERE client ILIKE 'brose%'
                ORDER BY data_hora DESC
                LIMIT 100;
            

-- ESTADISTIQUES_PRECISIO

                -- Estadístiques de precisió per client
                SET CLIENT_ENCODING TO 'UTF8';
                SELECT 
                    client,
                    COUNT(*) as total_mesures,
                    ROUND(AVG(actual::numeric), 6) as actual_mitjana,
                    ROUND(STDDEV(actual::numeric), 6) as actual_desviacio,
                    ROUND(MIN(actual::numeric), 6) as actual_min,
                    ROUND(MAX(actual::numeric), 6) as actual_max
                FROM mesuresqualitat 
                WHERE client IS NOT NULL AND actual IS NOT NULL
                GROUP BY client
                ORDER BY total_mesures DESC;
            

-- ELEMENTS_AMB_UNICODE

                -- Buscar elements que encara poden tenir caràcters especials
                SET CLIENT_ENCODING TO 'UTF8';
                SELECT DISTINCT element, COUNT(*)
                FROM mesuresqualitat 
                WHERE element ~ '[^[:ascii:]]'
                GROUP BY element
                ORDER BY count DESC;
            

