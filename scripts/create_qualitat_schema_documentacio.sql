-- ============================================================
-- CREAR SCHEMA QUALITAT I TAULES A documentacio_tecnica
-- ============================================================
-- Aquest script crea el schema qualitat i les 4 taules
-- a documentacio_tecnica per rebre les dades d'Airflow
-- ============================================================

-- PART 1: Crear schema qualitat
CREATE SCHEMA IF NOT EXISTS qualitat;

-- PART 2: Crear les 4 taules (estructura igual que a airflow_db)

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
    CONSTRAINT mesures_gompcnou_pkey PRIMARY KEY (id_element)
);

-- Taula 2: mesures_gompc_projectes
DROP TABLE IF EXISTS qualitat.mesures_gompc_projectes CASCADE;
CREATE TABLE qualitat.mesures_gompc_projectes (
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
    operari character varying(100),
    proces character varying(100),
    ref_ma character varying(100),
    tipus_control character varying(100),
    num_cavitats integer,
    observacions text,
    temps_mesura integer,
    foto_peça boolean,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT mesures_gompc_projectes_pkey PRIMARY KEY (id_element)
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
    CONSTRAINT mesureshoytom_pkey PRIMARY KEY (id_element)
);

-- Taula 4: mesurestorsio
DROP TABLE IF EXISTS qualitat.mesurestorsio CASCADE;
CREATE TABLE qualitat.mesurestorsio (
    id_referencia_some SERIAL,
    id_element BIGSERIAL,
    client character varying(100),
    data_hora timestamp without time zone,
    maquina character varying(50) DEFAULT 'torsio',
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
    CONSTRAINT mesurestorsio_pkey PRIMARY KEY (id_element)
);

-- PART 3: Crear índexs per optimitzar les consultes
CREATE INDEX idx_gompcnou_client_ref ON qualitat.mesures_gompcnou(client, id_referencia_client);
CREATE INDEX idx_gompcnou_lot ON qualitat.mesures_gompcnou(id_lot);
CREATE INDEX idx_gompcnou_data ON qualitat.mesures_gompcnou(data_hora);

CREATE INDEX idx_gompc_proj_client_ref ON qualitat.mesures_gompc_projectes(client, id_referencia_client);
CREATE INDEX idx_gompc_proj_lot ON qualitat.mesures_gompc_projectes(id_lot);
CREATE INDEX idx_gompc_proj_data ON qualitat.mesures_gompc_projectes(data_hora);

CREATE INDEX idx_hoytom_client_ref ON qualitat.mesureshoytom(client, id_referencia_client);
CREATE INDEX idx_hoytom_lot ON qualitat.mesureshoytom(id_lot);
CREATE INDEX idx_hoytom_data ON qualitat.mesureshoytom(data_hora);

CREATE INDEX idx_torsio_client_ref ON qualitat.mesurestorsio(client, id_referencia_client);
CREATE INDEX idx_torsio_lot ON qualitat.mesurestorsio(id_lot);
CREATE INDEX idx_torsio_data ON qualitat.mesurestorsio(data_hora);

-- PART 4: Grants (permisos de lectura per l'usuari tecnica)
GRANT USAGE ON SCHEMA qualitat TO tecnica;
GRANT SELECT ON ALL TABLES IN SCHEMA qualitat TO tecnica;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA qualitat TO tecnica;

-- Verificació
SELECT 'Schema qualitat creat correctament' AS status;
