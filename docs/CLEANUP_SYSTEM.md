# Sistema de Neteja Automàtica Universal de Fitxers Temporals

## Descripció

Aquest sistema s'encarrega d'eliminar automàticament els fitxers CSV i altres fitxers temporals que es generen durant el processament de dades per **TOTS els clients** (ZF, SEAT, BMW, Audi, Mercedes, etc.), evitant que s'acumulin i omplin el disc.

## Característiques Principals

### 🚀 Neteja Automàtica Universal

- **Neteja per tots els clients**: Funciona amb ZF, SEAT, BMW, Audi, VW, Mercedes, Porsche i qualsevol altre client
- **Polítiques intel·ligents per client**: Cada tipus de client té temps de retenció optimitzats
- **Neteja després de pujades exitoses**: Els fitxers s'eliminen automàticament quan les dades s'han carregat correctament
- **Detecció automàtica de tipus de client**: Aplica la política correcta segons el nom del client

### 🎯 Polítiques per Tipus de Client

| Client | Temporals | Processats | Exports | Descripció |
|--------|-----------|------------|---------|------------|
| **ZF** | 30 min | 2 hores | 4 hores | Neteja ràpida per volum alt |
| **SEAT/Audi/VW** | 45 min | 4 hores | 8 hores | Política intermèdia VAG |
| **BMW/MINI** | 90 min | 8 hores | 16 hores | Política conservadora |
| **Mercedes/Porsche** | 2 hores | 12 hores | 24 hores | Política premium |
| **Altres clients** | 2 hores | 12 hores | 48 hores | Política estàndard |

### 🛡️ Seguretat

- **Verificacions de seguretat universals**: Els fitxers només s'eliminen si passen verificacions
- **Edat mínima**: Els fitxers han de tenir una edat mínima abans de ser eliminats
- **Patrons d'exclusió**: Fitxers importants (*backup*, *important*) mai s'eliminen
- **Mode dry-run**: Permet simular la neteja sense eliminar fitxers realment

## Ús

### 1. Neteja Automàtica (Recomanat)

La neteja s'executa automàticament després de cada pujada exitosa a la base de dades:

```python
from src.database.database_uploader import DatabaseUploader

uploader = DatabaseUploader(client="ZF", ref_project="004938000151")
uploader.upload_all()  # La neteja s'executa automàticament si la pujada és exitosa
```

### 2. Neteja Manual

#### Neteja específica per projectes ZF:
```python
from src.services.temp_file_cleaner import TempFileCleaner

cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
result = cleaner.clean_for_zf_project("004938000151", aggressive=False)
print(f"Fitxers netejats: {result['files_cleaned']}")
```

#### Neteja general:
```python
cleaner = TempFileCleaner()
cleaned_files = cleaner.clean_all_old_files()
print(f"S'han eliminat {len(cleaned_files)} fitxers antics")
```

### 3. Scripts d'Automatització

#### Executar neteja des de línia de comandaments:
```bash
# Neteja normal
python maintenance\auto_cleanup.py

# Neteja agressiva
python maintenance\auto_cleanup.py --aggressive

# Neteja per projecte específic
python maintenance\auto_cleanup.py --project-id 004938000151

# Simular neteja (no elimina fitxers)
python maintenance\auto_cleanup.py --dry-run
```

#### Executar des de Windows:
```batch
# Doble clic al fitxer o executar des de cmd
maintenance\run_cleanup.bat
```

## Configuració

### Polítiques de Retenció per Defecte

| Tipus de Fitxer | Temps de Retenció | Descripció |
|------------------|-------------------|------------|
| Temporals (`data/temp/`) | 1 hora | Fitxers de processament temporal |
| Processats (`data/processed/`) | 6 hores | Fitxers de dades processades |
| Exports (`data/processed/exports/`) | 24 hores | Fitxers d'exportació |

### Polítiques Específiques per ZF

| Tipus de Fitxer | Normal | Agressiu |
|------------------|---------|----------|
| Temporals | 30 min | 10 min |
| Processats | 2 hores | 1 hora |
| Exports | 4 hores | 2 hores |

### Personalitzar Configuració

Edita el fitxer `config/cleanup_config.json`:

```json
{
  "auto_cleanup_config": {
    "retention_policies": {
      "zf_projects": {
        "age_minutes_temp": 30,
        "age_hours_processed": 2,
        "age_hours_exports": 4
      }
    }
  }
}
```

## Directoris que es Netegen

1. **`data/temp/`** - Fitxers temporals de processament
2. **`data/processed/exports/`** - Fitxers CSV d'exportació
3. **`data/processed/datasheets/`** - Fulls de dades processats (només CSV)
4. **Directori temporal del sistema** - Fitxers temporals de l'aplicació

## Fitxers que es Netegen

- **Fitxers CSV**: `*.csv` amb patrons específics del projecte
- **Fitxers temporals**: `*.tmp`, `*.temp`
- **Fitxers de processament**: Amb patrons com `datasheet_CLIENT_PROJECT*`

## Fitxers que NO es Netegen

- **Fitxers de backup**: `*.bak`, `*_backup_*`
- **Fitxers importants**: `important_*`
- **Fitxers massa nous**: Menys de 5 minuts d'edat
- **Fitxers JSON**: Es mantenen més temps que els CSV

## Programació Automàtica

### Windows Task Scheduler

1. Obrir Task Scheduler (`taskschd.msc`)
2. Crear tasca bàsica
3. Configurar:
   - **Trigger**: Diàriament a les 02:00
   - **Action**: Executar `C:\ruta\al\projecte\maintenance\run_cleanup.bat`
   - **Settings**: Executar encara que l'usuari no estigui connectat

### Exemple de configuració de tasca:
```xml
<!-- Importar aquesta configuració al Task Scheduler -->
<Task>
  <RegistrationInfo>
    <Description>Neteja automàtica de fitxers temporals PythonTecnica</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T02:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\maintenance\run_cleanup.bat</Command>
    </Exec>
  </Actions>
</Task>
```

## Logs i Monitoratge

### Logs de Neteja
- **Fitxer**: `logs/auto_cleanup.log`
- **Rotació**: 10 MB màxim, 5 fitxers de backup
- **Contingut**: Detalls de cada operació de neteja

### Verificar Logs
```bash
# Veure els últims logs
tail -f logs/auto_cleanup.log

# Cercar neteja d'un projecte específic
grep "004938000151" logs/auto_cleanup.log
```

## Resolució de Problemes

### Error: "No s'ha pogut eliminar fitxer"
- **Causa**: Fitxer en ús per una altra aplicació
- **Solució**: Tancar l'aplicació que està utilitzant el fitxer

### Error: "Configuració no trobada"
- **Causa**: Fitxer `config/cleanup_config.json` no existeix
- **Solució**: El sistema utilitzarà configuració per defecte

### Massa fitxers s'eliminen
- **Solució**: Ajustar els temps de retenció al fitxer de configuració
- **Temporal**: Usar `--dry-run` per simular abans d'executar

### No s'eliminen fitxers
- **Verificar**: Els fitxers tenen l'edat suficient segons la política
- **Logs**: Revisar `logs/auto_cleanup.log` per detalls

## Test del Sistema

Executar els tests per verificar que tot funciona:

```bash
python tests\test_temp_file_cleanup.py
```

## Beneficis

1. **🗂️ Espaí de disc**: Evita l'acumulació de fitxers temporals
2. **🚀 Rendiment**: Menys fitxers = millor rendiment del sistema
3. **🔄 Automatització**: No cal recordar eliminar fitxers manualment
4. **🛡️ Seguretat**: Els fitxers s'eliminen de forma segura
5. **📊 Control**: Logs detallats de totes les operacions

---

**Nota**: Aquest sistema està dissenyat específicament per als fitxers CSV temporals generats durant el processament de dades de projectes com ZF. No afecta fitxers de dades importants o de configuració.
