-- ============================================================
-- SCRIPT DE MIGRACIÓ: mesuresqualitat → 4 taules separades
-- ============================================================
-- Aquest script crea 4 taules noves separades per màquina
-- i migra les dades de la taula mesuresqualitat original
--
-- Taules noves:
--   1. mesures_gompcnou (màquina 'gompc')
--   2. mesures_gompc_projecets (màquina 'gompc_projectes')
--   3. mesureshoytom (màquina 'hoytom')
--   4. mesurestoriso (màquina 'toriso')
-- ============================================================

-- IMPORTANT: Executar a la base de dades airflow_db primer
-- Després es copiarà a documentacio_tecnica

\c airflow_db;

-- ============================================================
-- PART 1: Crear schema qualitat si no existeix
-- ============================================================
CREATE SCHEMA IF NOT EXISTS qualitat;

-- ============================================================
-- PART 2: Crear les 4 taules noves
-- ============================================================

-- Taula 1: mesures_gompcnou
DROP TABLE IF EXISTS qualitat.mesures_gompcnou CASCADE;
CREATE TABLE qualitat.mesures_gompcnou (
    id_referencia_some SERIAL,
    id_element BIGSERIAL,
    client character varying(100),
    data_hora timestamp without time zone,
    maquina character varying(50) DEFAULT 'gompc',
    fase character varying(100),
    id_referencia_client character varying(100),
    id_lot character varying(100),
    cavitat character varying(50),
    pieza character varying(200),
    element character varying(200),
    datum character varying(200),
    property character varying(200),
    actual double precision,
    nominal double precision,
    tolerancia_negativa double precision,
    tolerancia_positiva double precision,
    desviacio double precision,
    check_value character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT mesures_gompcnou_pkey PRIMARY KEY (id_referencia_some, id_element)
);

-- Taula 2: mesures_gompc_projecets
DROP TABLE IF EXISTS qualitat.mesures_gompc_projecets CASCADE;
CREATE TABLE qualitat.mesures_gompc_projecets (
    id_referencia_some SERIAL,
    id_element BIGSERIAL,
    client character varying(100),
    data_hora timestamp without time zone,
    maquina character varying(50) DEFAULT 'gompc_projectes',
    fase character varying(100),
    id_referencia_client character varying(100),
    id_lot character varying(100),
    cavitat character varying(50),
    pieza character varying(200),
    element character varying(200),
    datum character varying(200),
    property character varying(200),
    actual double precision,
    nominal double precision,
    tolerancia_negativa double precision,
    tolerancia_positiva double precision,
    desviacio double precision,
    check_value character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT mesures_gompc_projecets_pkey PRIMARY KEY (id_referencia_some, id_element)
);

-- Taula 3: mesureshoytom
DROP TABLE IF EXISTS qualitat.mesureshoytom CASCADE;
CREATE TABLE qualitat.mesureshoytom (
    id_referencia_some SERIAL,
    id_element BIGSERIAL,
    client character varying(100),
    data_hora timestamp without time zone,
    maquina character varying(50) DEFAULT 'hoytom',
    fase character varying(100),
    id_referencia_client character varying(100),
    id_lot character varying(100),
    cavitat character varying(50),
    pieza character varying(200),
    element character varying(200),
    datum character varying(200),
    property character varying(200),
    actual double precision,
    nominal double precision,
    tolerancia_negativa double precision,
    tolerancia_positiva double precision,
    desviacio double precision,
    check_value character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT mesureshoytom_pkey PRIMARY KEY (id_referencia_some, id_element)
);

-- Taula 4: mesurestoriso
DROP TABLE IF EXISTS qualitat.mesurestoriso CASCADE;
CREATE TABLE qualitat.mesurestoriso (
    id_referencia_some SERIAL,
    id_element BIGSERIAL,
    client character varying(100),
    data_hora timestamp without time zone,
    maquina character varying(50) DEFAULT 'toriso',
    fase character varying(100),
    id_referencia_client character varying(100),
    id_lot character varying(100),
    cavitat character varying(50),
    pieza character varying(200),
    element character varying(200),
    datum character varying(200),
    property character varying(200),
    actual double precision,
    nominal double precision,
    tolerancia_negativa double precision,
    tolerancia_positiva double precision,
    desviacio double precision,
    check_value character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT mesurestoriso_pkey PRIMARY KEY (id_referencia_some, id_element)
);

-- ============================================================
-- PART 3: Crear índexs per millorar el rendiment
-- ============================================================

-- Índexs per mesures_gompcnou
CREATE INDEX idx_gompcnou_client ON qualitat.mesures_gompcnou(client);
CREATE INDEX idx_gompcnou_lot ON qualitat.mesures_gompcnou(id_lot);
CREATE INDEX idx_gompcnou_data_hora ON qualitat.mesures_gompcnou(data_hora);
CREATE INDEX idx_gompcnou_referencia_client ON qualitat.mesures_gompcnou(id_referencia_client);
CREATE INDEX idx_gompcnou_element ON qualitat.mesures_gompcnou(element);

-- Índexs per mesures_gompc_projecets
CREATE INDEX idx_gompc_proj_client ON qualitat.mesures_gompc_projecets(client);
CREATE INDEX idx_gompc_proj_lot ON qualitat.mesures_gompc_projecets(id_lot);
CREATE INDEX idx_gompc_proj_data_hora ON qualitat.mesures_gompc_projecets(data_hora);
CREATE INDEX idx_gompc_proj_referencia_client ON qualitat.mesures_gompc_projecets(id_referencia_client);
CREATE INDEX idx_gompc_proj_element ON qualitat.mesures_gompc_projecets(element);

-- Índexs per mesureshoytom
CREATE INDEX idx_hoytom_client ON qualitat.mesureshoytom(client);
CREATE INDEX idx_hoytom_lot ON qualitat.mesureshoytom(id_lot);
CREATE INDEX idx_hoytom_data_hora ON qualitat.mesureshoytom(data_hora);
CREATE INDEX idx_hoytom_referencia_client ON qualitat.mesureshoytom(id_referencia_client);
CREATE INDEX idx_hoytom_element ON qualitat.mesureshoytom(element);

-- Índexs per mesurestoriso
CREATE INDEX idx_toriso_client ON qualitat.mesurestoriso(client);
CREATE INDEX idx_toriso_lot ON qualitat.mesurestoriso(id_lot);
CREATE INDEX idx_toriso_data_hora ON qualitat.mesurestoriso(data_hora);
CREATE INDEX idx_toriso_referencia_client ON qualitat.mesurestoriso(id_referencia_client);
CREATE INDEX idx_toriso_element ON qualitat.mesurestoriso(element);

-- ============================================================
-- PART 4: Afegir comentaris a les taules
-- ============================================================

COMMENT ON TABLE qualitat.mesures_gompcnou IS 'Mesures de qualitat de la màquina GOMPC';
COMMENT ON TABLE qualitat.mesures_gompc_projecets IS 'Mesures de qualitat de la màquina GOMPC Projectes';
COMMENT ON TABLE qualitat.mesureshoytom IS 'Mesures de qualitat de la màquina HOYTOM';
COMMENT ON TABLE qualitat.mesurestoriso IS 'Mesures de qualitat de la màquina TORISO';

-- ============================================================
-- PART 5: Migrar dades de mesuresqualitat (si existeix)
-- ============================================================
-- NOTA: Aquesta part només s'executa si tens dades a mesuresqualitat
-- que vols migrar. Si no, pots saltar aquesta part.

DO $$
BEGIN
    -- Verificar si existeix la taula mesuresqualitat
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'mesuresqualitat'
    ) THEN
        RAISE NOTICE 'Taula mesuresqualitat trobada. Migrant dades...';
        
        -- Migrar dades a mesures_gompcnou (maquina = 'gompc')
        INSERT INTO qualitat.mesures_gompcnou (
            client, data_hora, maquina, fase, id_referencia_client, id_lot, 
            cavitat, pieza, element, datum, property, actual, nominal, 
            tolerancia_negativa, tolerancia_positiva, desviacio, 
            check_value, created_at, updated_at
        )
        SELECT 
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        FROM public.mesuresqualitat
        WHERE maquina = 'gompc' OR maquina IS NULL
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Dades migrades a mesures_gompcnou: % registres', 
            (SELECT COUNT(*) FROM qualitat.mesures_gompcnou);
        
        -- Migrar dades a mesures_gompc_projecets (maquina = 'gompc_projectes')
        INSERT INTO qualitat.mesures_gompc_projecets (
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        )
        SELECT 
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        FROM public.mesuresqualitat
        WHERE maquina = 'gompc_projectes'
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Dades migrades a mesures_gompc_projecets: % registres',
            (SELECT COUNT(*) FROM qualitat.mesures_gompc_projecets);
        
        -- Migrar dades a mesureshoytom (maquina = 'hoytom')
        INSERT INTO qualitat.mesureshoytom (
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        )
        SELECT 
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        FROM public.mesuresqualitat
        WHERE maquina = 'hoytom'
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Dades migrades a mesureshoytom: % registres',
            (SELECT COUNT(*) FROM qualitat.mesureshoytom);
        
        -- Migrar dades a mesurestoriso (maquina = 'toriso')
        INSERT INTO qualitat.mesurestoriso (
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        )
        SELECT 
            client, data_hora, maquina, fase, id_referencia_client, id_lot,
            cavitat, pieza, element, datum, property, actual, nominal,
            tolerancia_negativa, tolerancia_positiva, desviacio,
            check_value, created_at, updated_at
        FROM public.mesuresqualitat
        WHERE maquina = 'toriso'
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Dades migrades a mesurestoriso: % registres',
            (SELECT COUNT(*) FROM qualitat.mesurestoriso);
            
    ELSE
        RAISE NOTICE 'Taula mesuresqualitat no trobada. No es migren dades.';
    END IF;
END $$;

-- ============================================================
-- PART 6: Verificar migració
-- ============================================================

SELECT 
    'mesures_gompcnou' as taula,
    COUNT(*) as total_registres,
    MIN(data_hora) as data_primera_mesura,
    MAX(data_hora) as data_ultima_mesura
FROM qualitat.mesures_gompcnou
UNION ALL
SELECT 
    'mesures_gompc_projecets',
    COUNT(*),
    MIN(data_hora),
    MAX(data_hora)
FROM qualitat.mesures_gompc_projecets
UNION ALL
SELECT 
    'mesureshoytom',
    COUNT(*),
    MIN(data_hora),
    MAX(data_hora)
FROM qualitat.mesureshoytom
UNION ALL
SELECT 
    'mesurestoriso',
    COUNT(*),
    MIN(data_hora),
    MAX(data_hora)
FROM qualitat.mesurestoriso;

-- ============================================================
-- FINALITZAT!
-- ============================================================
-- Ara has de:
-- 1. Executar aquest script a airflow_db
-- 2. Copiar les taules del schema qualitat a public:
--    - qualitat.mesures_gompcnou → public.mesures_gompcnou
--    - qualitat.mesures_gompc_projecets → public.mesures_gompc_projecets
--    - qualitat.mesureshoytom → public.mesureshoytom
--    - qualitat.mesurestoriso → public.mesurestoriso
-- 3. Després copiar de airflow_db a documentacio_tecnica
-- ============================================================
