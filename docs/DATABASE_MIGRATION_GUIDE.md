# 📋 Guia de Migració a Nova Arquitectura de Base de Dades

## 🎯 Objectiu
Separar les dades de mesures en 4 taules diferents segons la màquina:
- `mesures_gompcnou` (màquina 'gompc')
- `mesures_gompc_projecets` (màquina 'gompc_projectes')
- `mesureshoytom` (màquina 'hoytom')
- `mesurestoriso` (màquina 'toriso')

## 📐 Arquitectura Nova

```
┌─────────────────────────────────────────────────────────────┐
│  AIRFLOW_DB (172.26.11.201)                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Schema: qualitat                                     │   │
│  │  ├─ mesures_gompcnou                                 │   │
│  │  ├─ mesures_gompc_projecets                          │   │
│  │  ├─ mesureshoytom                                    │   │
│  │  └─ mesurestoriso                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Còpia automàtica (cada nit 24h)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  DOCUMENTACIO_TECNICA (172.26.11.201)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Schema: public                                       │   │
│  │  ├─ mesures_gompcnou                                 │   │
│  │  ├─ mesures_gompc_projecets                          │   │
│  │  ├─ mesureshoytom                                    │   │
│  │  └─ mesurestoriso                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Passos de Migració

### Pas 1: Crear les Taules Noves a `airflow_db`

Executa el script SQL per crear les 4 taules noves al schema `qualitat`:

```bash
# Connectar a airflow_db
psql -h 172.26.11.201 -p 5432 -U airflow_user -d airflow_db

# Executar script
\i C:/Github/PythonTecnica_SOME/PythonTecnica_SOME/scripts/migrate_to_separate_tables.sql
```

Aquest script:
1. Crea el schema `qualitat` si no existeix
2. Crea les 4 taules noves amb la mateixa estructura
3. Crea índexs per millorar el rendiment
4. Migra les dades de `mesuresqualitat` (si existeix) segons la columna `maquina`

### Pas 2: Copiar Taules de `qualitat` a `public` (a airflow_db)

Un cop migrades les dades al schema `qualitat`, copiar-les al schema `public`:

```sql
-- A airflow_db
CREATE TABLE public.mesures_gompcnou AS SELECT * FROM qualitat.mesures_gompcnou;
CREATE TABLE public.mesures_gompc_projecets AS SELECT * FROM qualitat.mesures_gompc_projecets;
CREATE TABLE public.mesureshoytom AS SELECT * FROM qualitat.mesureshoytom;
CREATE TABLE public.mesurestoriso AS SELECT * FROM qualitat.mesurestoriso;

-- Recrear índexs
CREATE INDEX idx_gompcnou_client ON public.mesures_gompcnou(client);
CREATE INDEX idx_gompcnou_data_hora ON public.mesures_gompcnou(data_hora);
-- ... (veure script SQL per tots els índexs)
```

### Pas 3: Copiar a `documentacio_tecnica`

Pots fer-ho manualment o usar l'script Python:

**Opció A: Manual amb pg_dump**
```bash
# Exportar de airflow_db
pg_dump -h 172.26.11.201 -U airflow_user -d airflow_db -t mesures_gompcnou -t mesures_gompc_projecets -t mesureshoytom -t mesurestoriso > mesures_export.sql

# Importar a documentacio_tecnica
psql -h 172.26.11.201 -U tecnica -d documentacio_tecnica < mesures_export.sql
```

**Opció B: Amb script Python (Recomanat)**
```bash
# Sincronització completa (primera vegada)
python scripts/sync_databases.py --full-sync

# Sincronització incremental (diària)
python scripts/sync_databases.py

# Només verificar estat
python scripts/sync_databases.py --verify-only
```

### Pas 4: Configurar Tasca Automàtica (Windows Task Scheduler)

1. Obrir **Task Scheduler** (Programador de tasques)
2. Crear nova tasca:
   - **Nom**: Sync Databases - PythonTecnica
   - **Trigger**: Diari a les 24:00 (00:00)
   - **Acció**: Executar `C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\scripts\sync_databases_auto.bat`
   - **Condicions**: 
     - ☑ Executar encara que l'usuari no hagi iniciat sessió
     - ☑ Executar amb els màxims privilegis

## 📊 Verificació

### Comprovar que tot funciona:

```bash
# Test de connexions i taules
python test_new_db_structure.py

# Verificar sincronització
python scripts/sync_databases.py --verify-only
```

### Resultats Esperats:

```
✅ Primary DB (documentacio_tecnica): Connexió OK
   • mesures_gompcnou: XXXXX registres
   • mesures_gompc_projecets: XXXXX registres
   • mesureshoytom: XXXXX registres
   • mesurestoriso: XXXXX registres

✅ Secondary DB (airflow_db): Connexió OK
   • mesures_gompcnou: XXXXX registres
   • mesures_gompc_projecets: XXXXX registres
   • mesureshoytom: XXXXX registres
   • mesurestoriso: XXXXX registres
```

## 🔧 Com Funciona l'Aplicació Ara

### Lectura de Dades (Primary: documentacio_tecnica)
Tots els mòduls que llegeixen dades (capacity studies, search, reports) ara usen **UNION ALL** automàticament per consultar les 4 taules:

```python
# MeasurementHistoryService fa això automàticament:
SELECT * FROM mesures_gompcnou WHERE client = 'AUTOLIV'
UNION ALL
SELECT * FROM mesures_gompc_projecets WHERE client = 'AUTOLIV'
UNION ALL
SELECT * FROM mesureshoytom WHERE client = 'AUTOLIV'
UNION ALL
SELECT * FROM mesurestoriso WHERE client = 'AUTOLIV'
```

### Escriptura de Dades (Secondary: airflow_db)
Els processos d'import segueixen inserint a `airflow_db`:
- Network Scanner → `airflow_db.public.mesures_*`
- Després tu copies → `documentacio_tecnica.public.mesures_*`

## 📁 Fitxers Modificats

### Configuració:
- `config/database/db_config.json` - Primary i Secondary configurats

### Serveis de Lectura:
- `src/services/measurement_history_service.py` - UNION automàtic
- `src/gui/windows/dimensional_study_window.py` - Llegeix de mesures_gompc_projecets

### Scripts Nous:
- `scripts/migrate_to_separate_tables.sql` - Crear i migrar taules
- `scripts/sync_databases.py` - Còpia automàtica Python
- `scripts/sync_databases_auto.bat` - Batch per Task Scheduler
- `test_new_db_structure.py` - Tests de verificació

## ❓ Preguntes Freqüents

### Com funciona la sincronització incremental?
Només copia registres nous (on `data_hora > última_data_copiada`). És ràpid i eficient per execucions diàries.

### Què passa si falla la còpia automàtica?
L'aplicació segueix funcionant amb les dades de `documentacio_tecnica`. Pots executar manualment la sincronització quan es resolgui el problema.

### Puc fer servir l'aplicació durant la còpia?
Sí! La còpia és a nivell de base de dades i no bloqueja l'ús de l'aplicació.

### Com afegir una nova màquina?
1. Afegir la taula a `MEASUREMENT_TABLES` a `measurement_history_service.py`
2. Afegir la taula a `TABLES_TO_SYNC` a `scripts/sync_databases.py`
3. Crear la taula amb la mateixa estructura

## 📞 Suport

Per problemes o dubtes, revisar:
- `logs/database_sync.log` - Logs de sincronització
- `logs/gui.log` - Logs de l'aplicació

---

**Data de creació**: 5 novembre 2025  
**Versió**: 1.0  
**Autor**: GitHub Copilot
