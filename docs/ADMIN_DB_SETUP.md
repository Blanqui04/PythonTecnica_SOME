# INSTRUCCIONS PER L'ADMINISTRADOR DE BASE DE DADES

## OBJECTIU
Configurar el flux automàtic de dades per l'aplicació PythonTecnica:

```
DADES NOVES → airflow_db.qualitat (ETL inserta aquí)
                  ↓
              (DAG Airflow copia cada nit)
                  ↓
           documentacio_tecnica.qualitat
                  ↓
           📱 APLICACIÓ (lectura)
```

## TASQUES A FER

### 1️⃣ CREAR SCHEMA 'qualitat' A documentacio_tecnica

**Script a executar:**
```bash
psql -h 172.26.11.201 -p 5432 -U postgres -d documentacio_tecnica -f scripts/create_qualitat_schema_documentacio.sql
```

**O manualment amb DBeaver/pgAdmin:**
- Obrir el fitxer: `scripts/create_qualitat_schema_documentacio.sql`
- Executar-lo a la BD `documentacio_tecnica`

**Què fa aquest script:**
- Crea el schema `qualitat`
- Crea 4 taules: `mesures_gompcnou`, `mesures_gompc_projectes`, `mesureshoytom`, `mesurestorsio`
- Crea índexs per optimitzar consultes
- Dona permisos de SELECT a l'usuari `tecnica`

---

### 2️⃣ CONFIGURAR DAG D'AIRFLOW

**Objectiu:** Copiar dades cada nit de `airflow_db.qualitat` → `documentacio_tecnica.qualitat`

**Opcions:**

#### Opció A: Utilitzar script Python existent
Ja tenim el script `scripts/sync_databases.py` que fa aquesta còpia.

**Crear DAG d'Airflow:**
```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 10),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sync_qualitat_to_documentacio',
    default_args=default_args,
    description='Sincronitza dades de qualitat entre BDs',
    schedule_interval='0 0 * * *',  # Cada dia a les 00:00
    catchup=False
)

sync_task = BashOperator(
    task_id='sync_databases',
    bash_command='cd /path/to/PythonTecnica_SOME && python scripts/sync_databases.py',
    dag=dag
)
```

#### Opció B: Query SQL directe
Si preferiu fer-ho amb SQL directe dins d'Airflow:

```sql
-- Truncar taules destí
TRUNCATE TABLE documentacio_tecnica.qualitat.mesures_gompc_projectes;

-- Copiar dades
INSERT INTO documentacio_tecnica.qualitat.mesures_gompc_projectes
SELECT * FROM airflow_db.qualitat.mesures_gompc_projectes;

-- Repetir per les altres 3 taules...
```

---

### 3️⃣ VERIFICAR

Després de la primera execució del DAG:

```sql
-- Verificar que les dades s'han copiat
SELECT 
    'airflow_db' as source,
    COUNT(*) as count
FROM airflow_db.qualitat.mesures_gompc_projectes

UNION ALL

SELECT 
    'documentacio_tecnica' as source,
    COUNT(*) as count
FROM documentacio_tecnica.qualitat.mesures_gompc_projectes;
```

**Resultat esperat:**
```
source                 | count
-----------------------|----------
airflow_db             | 1,154,880
documentacio_tecnica   | 1,154,880
```

---

## ESTAT ACTUAL

✅ **airflow_db**:
- Schema `qualitat` creat ✅
- 4 taules creades ✅
- Dades: `mesures_gompc_projectes` té 1,154,880 registres ✅

❌ **documentacio_tecnica**:
- Schema `qualitat` NO EXISTEIX ⚠️
- Cal executar el script SQL (tasca 1️⃣)

✅ **Aplicació**:
- Codi actualitzat per detectar automàticament el schema ✅
- Si troba `qualitat`, l'utilitza (ETL automàtic)
- Si no, utilitza `public` (legacy) com a fallback ✅

---

## DESPRÉS DE COMPLETAR LES TASQUES

L'aplicació automàticament:
1. ✅ Detectarà el schema `qualitat`
2. ✅ Llegirà les dades fresques que arriben cada dia via ETL
3. ✅ Els estudis de capacitat utilitzaran dades actualitzades

**LOG al iniciar l'aplicació:**
```
INFO - ✅ Utilitzant schema 'qualitat' (alimentat per Airflow ETL)
```

---

## CONTACTE

Per dubtes o problemes:
- Script SQL: `scripts/create_qualitat_schema_documentacio.sql`
- Script Python sync: `scripts/sync_databases.py`
- Documentació completa: `docs/DATABASE_MIGRATION_GUIDE.md`
