# 📖 Manual d'Usuari Complet - PythonTecnica SOME

## Aplicació d'Anàlisi Dimensional i Control de Qualitat

**Versió:** 2.1.0  
**Data:** Novembre 2025  
**Autor:** Equip de Desenvolupament SOME

---

## 📋 Índex

1. [Introducció](#1-introducció)
2. [Requisits del Sistema](#2-requisits-del-sistema)
3. [Instal·lació i Configuració](#3-installació-i-configuració)
4. [Inici de l'Aplicació](#4-inici-de-laplicació)
5. [Finestra Principal - Estudi Dimensional](#5-finestra-principal---estudi-dimensional)
6. [Operacions amb Dades](#6-operacions-amb-dades)
7. [Funcionalitats de Clipboard (Ctrl+C/Ctrl+V)](#7-funcionalitats-de-clipboard-ctrlcctrlv)
8. [Plantilles Dimensionals per Referència/LOT](#8-plantilles-dimensionals-per-referèncialot)
9. [Anàlisi i Càlculs](#9-anàlisi-i-càlculs)
10. [Gestió de Sessions](#10-gestió-de-sessions)
11. [Exportació de Dades](#11-exportació-de-dades)
12. [Estudis de Capacitat (SPC)](#12-estudis-de-capacitat-spc)
13. [Comparació Multi-LOT](#13-comparació-multi-lot)
14. [Resolució de Problemes](#14-resolució-de-problemes)
15. [Dreceres de Teclat](#15-dreceres-de-teclat)
16. [Glossari](#16-glossari)

---

## 1. Introducció

### 1.1 Què és PythonTecnica SOME?

PythonTecnica SOME és una aplicació professional d'anàlisi dimensional dissenyada per al sector de l'automoció. Permet:

- ✅ Registrar i analitzar mesures dimensionals
- ✅ Calcular índexs de capacitat de procés (Cp, Cpk, Pp, Ppk)
- ✅ Generar informes PPAP i altres tipus d'auditories
- ✅ Gestionar múltiples LOTs i referències
- ✅ Exportar dades en diversos formats

### 1.2 Per a qui és aquesta aplicació?

- Tècnics de qualitat
- Enginyers de processos
- Metròlegs
- Responsables de producció
- Auditors interns i externs

---

## 2. Requisits del Sistema

### 2.1 Requisits Mínims

| Component | Requisit Mínim |
|-----------|----------------|
| Sistema Operatiu | Windows 10/11 (64-bit) |
| Processador | Intel Core i3 o equivalent |
| Memòria RAM | 4 GB |
| Espai en Disc | 500 MB |
| Resolució Pantalla | 1366 x 768 |
| Python | 3.9 o superior |

### 2.2 Requisits Recomanats

| Component | Requisit Recomanat |
|-----------|-------------------|
| Sistema Operatiu | Windows 11 (64-bit) |
| Processador | Intel Core i5 o superior |
| Memòria RAM | 8 GB o més |
| Espai en Disc | 1 GB |
| Resolució Pantalla | 1920 x 1080 o superior |

---

## 3. Instal·lació i Configuració

### 3.1 Instal·lació Ràpida

1. **Descarregar** el paquet d'instal·lació
2. **Executar** `SETUP.bat` com a administrador
3. **Esperar** que s'instal·lin les dependències
4. **Verificar** amb `VERIFY_SYSTEM.bat`

### 3.2 Instal·lació Manual

```powershell
# 1. Crear entorn virtual
python -m venv env

# 2. Activar entorn
.\env\Scripts\Activate.ps1

# 3. Instal·lar dependències
pip install -r requirements.txt

# 4. Executar aplicació
python main_app.py
```

### 3.3 Configuració de Base de Dades

L'aplicació pot connectar-se a bases de dades PostgreSQL per obtenir dades de mesures. Configureu el fitxer `config/database/db_config.json`:

```json
{
    "host": "servidor_db",
    "port": 5432,
    "database": "qualitat",
    "user": "usuari",
    "password": "contrasenya"
}
```

---

## 4. Inici de l'Aplicació

### 4.1 Executar l'Aplicació

**Opció 1:** Doble clic a `RUN_APP.bat`

**Opció 2:** Des de terminal:
```powershell
python main_app.py
```

### 4.2 Pantalla d'Inici de Sessió

1. Introduïu les vostres **credencials** (si s'ha configurat autenticació)
2. Seleccioneu el **client** de la llista desplegable
3. Introduïu la **referència del projecte**
4. Especifiqueu el **número de LOT/Batch**
5. Feu clic a **"Iniciar Estudi"**

![Pantalla Login](assets/images/gui/login_screen.png)

---

## 5. Finestra Principal - Estudi Dimensional

### 5.1 Descripció General de la Interfície

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 CAPÇALERA - Informació del Projecte                         │
│ ┌──────────────┬──────────────────┬──────────────────────────┐ │
│ │ Client       │ Configuració     │ Logo                     │ │
│ │ Projecte     │ Tipus Informe    │                          │ │
│ │ Batch        │ Toleràncies      │                          │ │
│ └──────────────┴──────────────────┴──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 🎛️ BARRA DE CONTROL                                            │
│ [Mode] [Carregar DB] [+Fila] [Duplicar] [Eliminar] [Analitzar] │
│ [Guardar] [Carregar] [Exportar] [Netejar] [Plantilla per LOT]  │
├─────────────────────────────────────────────────────────────────┤
│ 📊 ÀREA DE CONTINGUT                                           │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [Summary] [LOT 1] [LOT 2] [LOT 3] ...                       ││
│ │                                                             ││
│ │  TAULA DE DADES DIMENSIONALS                               ││
│ │  ─────────────────────────────────────────────             ││
│ │  Element | Batch | Nominal | Tol- | Tol+ | M1 | M2 | ...   ││
│ │                                                             ││
│ └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ 📈 BARRA D'ESTAT                                               │
│ Registres: 25 | Última acció: Dades carregades | ⚠ No guardat │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Capçalera - Informació del Projecte

| Camp | Descripció |
|------|------------|
| 🏢 **Client** | Nom del client seleccionat |
| 📁 **Projecte** | Referència del projecte/peça |
| 📦 **Batch** | Número de lot en anàlisi |
| 📊 **Tipus d'Informe** | PPAP, FOT, Auditoria, etc. |
| 📏 **Toleràncies** | Percentatge d'enginyeria aplicat |

### 5.3 Tipus d'Informes Disponibles

| Tipus | Descripció | Ús Típic |
|-------|------------|----------|
| **PPAP** | Production Part Approval Process | Aprovació de peces noves |
| **FOT** | First Off Tool | Primeres peces de motlle |
| **Process Validation** | Validació de procés | Canvis de procés |
| **Internal Audit** | Auditoria interna | Control periòdic |
| **Customer Audit** | Auditoria de client | Visites de client |
| **Tool Modification** | Modificació d'eina | Després de reparacions |
| **Serial Production Control** | Control de producció en sèrie | Seguiment continu |

### 5.4 Barra de Control

#### Mode de Treball

| Botó | Funció |
|------|--------|
| 🔄 **Mode Manual/Auto** | Alterna entre mode manual (edició) i automàtic |
| 📥 **Carregar DB** | Carrega dades des de la base de dades |

#### Controls Manuals (visibles en Mode Manual)

| Botó | Funció | Drecera |
|------|--------|---------|
| ➕ **Add Row** | Afegeix una nova fila buida | - |
| 📋 **Duplicate** | Duplica la fila seleccionada | - |
| 🗑️ **Delete** | Elimina la fila seleccionada | Delete |

#### Anàlisi

| Botó | Funció |
|------|--------|
| 🚀 **Run Dimensional Study** | Executa l'anàlisi dimensional complet |

#### Sessió

| Botó | Funció | Drecera |
|------|--------|---------|
| 💾 **Save** | Guarda la sessió actual | Ctrl+S |
| 📂 **Load** | Carrega una sessió guardada | Ctrl+O |
| 📤 **Export** | Exporta dades a Excel/CSV | Ctrl+E |
| 🧹 **Clear** | Neteja totes les dades | - |

#### Plantilles

| Botó | Funció |
|------|--------|
| 📐 **Plantilla per LOT** | Obre el diàleg de plantilles dimensional |

---

## 6. Operacions amb Dades

### 6.1 Estructura de la Taula de Dades

| Columna | Descripció | Editable | Exemple |
|---------|------------|----------|---------|
| **Element ID** | Identificador únic | ✅ | Nº001 |
| **Batch** | Número de lot | ✅ | 2024001 |
| **Cavity** | Número de cavitat | ✅ | 1 |
| **Class** | Classificació (CC, SC, etc.) | ✅ | CC |
| **Description** | Descripció de la cota | ✅ | Diàmetre exterior |
| **Measuring Instrument** | Instrument de mesura | ✅ | CMM |
| **Unit** | Unitat de mesura | ✅ | mm |
| **Datum** | Referència datum | ✅ | A |
| **Evaluation Type** | Tipus d'avaluació | ✅ | Normal |
| **Nominal** | Valor nominal | ✅ | 25.000 |
| **Lower Tolerance** | Tolerància inferior | ✅ | -0.050 |
| **Upper Tolerance** | Tolerància superior | ✅ | +0.050 |
| **Measurement 1-5** | Valors mesurats | ✅ | 25.012 |
| **Minimum** | Valor mínim | ❌ | 24.998 |
| **Maximum** | Valor màxim | ❌ | 25.025 |
| **Mean** | Mitjana | ❌ | 25.010 |
| **Std Deviation** | Desviació estàndard | ❌ | 0.008 |
| **Pp** | Índex de capacitat | ❌ | 1.45 |
| **Ppk** | Índex de capacitat centrat | ❌ | 1.32 |
| **Status** | Estat (OK/NOK) | ❌ | ✅ OK |
| **Force Status** | Forçar estat manualment | ✅ | AUTO |

### 6.2 Classificacions d'Elements (Class)

| Codi | Significat | Descripció |
|------|------------|------------|
| **CC** | Critical Characteristic | Característica crítica per seguretat |
| **SC** | Significant Characteristic | Característica significativa |
| **IC** | Important Characteristic | Característica important |
| **KC** | Key Characteristic | Característica clau (automoció) |
| **PC** | Process Characteristic | Característica de procés |
| **NC** | Non-Critical | No crítica |

### 6.3 Tipus d'Avaluació

| Tipus | Descripció | Càlcul |
|-------|------------|--------|
| **Normal** | Avaluació estàndard | Totes les estadístiques |
| **Basic** | Avaluació bàsica | Només OK/NOK |
| **Informative** | Només informatiu | Sense avaluació |
| **Note** | Nota/Comentari | Sense càlculs |
| **GD&T** | Geometric Dimensioning | Amb símbols GD&T |

### 6.4 Introduir Dades Manualment

1. **Activar Mode Manual**: Feu clic al botó de mode o marqueu la casella
2. **Afegir Fila**: Feu clic a "➕ Add Row"
3. **Omplir Camps**:
   - Feu doble clic a cada cel·la per editar
   - Utilitzeu Tab per moure's entre cel·les
   - Els valors numèrics s'auto-formaten a 3 decimals

### 6.5 Carregar Dades des de Base de Dades

1. Feu clic a **"📥 Carregar DB"**
2. Seleccioneu els criteris de filtre:
   - Client
   - Referència
   - LOT/Batch
   - Màquina (opcional)
3. Feu clic a **"Carregar"**
4. Les dades apareixeran a la taula organitzades per pestanyes

---

## 7. Funcionalitats de Clipboard (Ctrl+C/Ctrl+V)

### 7.1 Dreceres de Teclat Disponibles

| Drecera | Acció | Descripció |
|---------|-------|------------|
| **Ctrl+C** | Copiar | Copia les cel·les seleccionades al portapapers |
| **Ctrl+V** | Enganxar | Enganxa dades del portapapers a la taula |
| **Ctrl+X** | Retallar | Copia i neteja les cel·les seleccionades |
| **Ctrl+A** | Seleccionar Tot | Selecciona totes les cel·les de la taula |
| **Delete** | Netejar | Neteja el contingut de les cel·les seleccionades |
| **Backspace** | Netejar | Igual que Delete |

### 7.2 Com Copiar Dades (Ctrl+C)

1. **Seleccioneu les cel·les** que voleu copiar:
   - Clic + arrossegar per seleccionar un rang
   - Ctrl + Clic per seleccionar cel·les individuals
   - Shift + Clic per seleccionar un rang continu
   
2. **Premeu Ctrl+C**

3. Les dades es copiaran en format **tabulat** (compatible amb Excel)

**Exemple:**
```
25.012    25.018    25.005
24.998    25.001    25.010
```

### 7.3 Com Enganxar Dades (Ctrl+V)

#### Des d'Excel o Calc:

1. **A Excel**: Seleccioneu les cel·les i copieu (Ctrl+C)
2. **A l'aplicació**: 
   - Seleccioneu la cel·la inicial on voleu enganxar
   - Premeu **Ctrl+V**
3. Les dades s'enganxaran automàticament

#### Des d'un fitxer de text:

L'aplicació accepta dades separades per:
- **Tabuladors** (recomanat)
- **Comes**
- **Punts i comes**

**Format acceptat:**
```
25.012	25.018	25.005
24.998	25.001	25.010
```

### 7.4 Comportament Intel·ligent de l'Enganxat

| Situació | Comportament |
|----------|--------------|
| **Valors numèrics** | S'auto-formaten a 3 decimals |
| **Valors no numèrics** | Es descarten amb avís |
| **Columnes calculades** | Es protegeixen (no s'enganxa) |
| **Cel·les amb dropdown** | S'intenta assignar el valor si existeix |
| **Més files que disponibles** | S'afegeixen files automàticament |

### 7.5 Copiar/Enganxar Files Completes

#### Copiar una fila:
1. Clic dret a la fila desitjada
2. Seleccioneu **"📄 Copy Row"**

#### Enganxar una fila:
1. Seleccioneu la fila de destí
2. Clic dret i seleccioneu **"📋 Paste Row"**

### 7.6 Exemples Pràctics

#### Exemple 1: Copiar mesures des d'Excel

```
Excel:                          Aplicació:
┌────────┬────────┬────────┐   ┌────────┬────────┬────────┐
│ 25.012 │ 25.018 │ 25.005 │ → │ 25.012 │ 25.018 │ 25.005 │
│ 24.998 │ 25.001 │ 25.010 │   │ 24.998 │ 25.001 │ 25.010 │
└────────┴────────┴────────┘   └────────┴────────┴────────┘
```

#### Exemple 2: Copiar una columna de valors

1. A Excel, seleccioneu una columna de mesures
2. Copieu amb Ctrl+C
3. A l'aplicació, seleccioneu la primera cel·la de la columna "Measurement 1"
4. Enganxeu amb Ctrl+V

---

## 8. Plantilles Dimensionals per Referència/LOT

### 8.1 Què és una Plantilla Dimensional?

Una plantilla dimensional permet:
- 📐 **Configurar** tots els elements d'una referència una sola vegada
- 🔄 **Reutilitzar** la configuració per a diferents LOTs
- ⚡ **Accelerar** la introducció de dades
- 📊 **Comparar** resultats entre LOTs

### 8.2 Obrir el Diàleg de Plantilles

1. Feu clic al botó **"📐 Plantilla per LOT"** a la barra de control
2. S'obrirà el diàleg de plantilles dimensionals

### 8.3 Interfície del Diàleg de Plantilles

```
┌─────────────────────────────────────────────────────────────────┐
│ 📐 Plantilla Dimensional - [Referència]                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────┐  ┌───────────────────────────────────┐ │
│ │ 📦 SELECCIÓ DE LOTs │  │ 📋 CONFIGURACIÓ DE PLANTILLA     │ │
│ │                     │  │                                   │ │
│ │ 🔍 Filtrar: [____]  │  │ Elements: Configuració carregada │ │
│ │                     │  │                                   │ │
│ │ ☐ LOT 2024001      │  │ Màquina: [all           ▼]       │ │
│ │ ☐ LOT 2024002      │  │                                   │ │
│ │ ☑ LOT 2024003      │  │ ☑ Copiar configuració d'elements │ │
│ │ ☑ LOT 2024004      │  │ ☐ Preservar mesures existents    │ │
│ │ ☐ LOT 2024005      │  │                                   │ │
│ │                     │  ├───────────────────────────────────┤ │
│ │ [Seleccionar Tot]   │  │ 👁️ PREVISUALITZACIÓ              │ │
│ │ [Netejar Selecció]  │  │ ┌───────────────────────────────┐│ │
│ │                     │  │ │ Element | Desc | Nom | Tol   ││ │
│ └─────────────────────┘  │ │ Nº001   | Diam | 25  | ±0.05 ││ │
│                          │ │ Nº002   | Long | 100 | ±0.10 ││ │
│ LOTs seleccionats: 2     │ └───────────────────────────────┘│ │
│                          └───────────────────────────────────┘ │
│                                                                 │
│ [🔄 Actualitzar LOTs]              [✅ Aplicar] [❌ Cancel·lar] │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4 Seleccionar LOTs

1. **Filtrar** (opcional): Escriviu al camp de cerca per filtrar LOTs
2. **Seleccionar**:
   - Clic per seleccionar un LOT individual
   - Ctrl + Clic per seleccionar múltiples
   - **"Seleccionar Tot"** per seleccionar tots els visibles
3. El comptador mostrarà quants LOTs heu seleccionat

### 8.5 Opcions de Configuració

| Opció | Descripció |
|-------|------------|
| **Màquina** | Seleccioneu la màquina de mesura (o "all" per totes) |
| **Copiar configuració** | Copia toleràncies, instruments i altres configuracions |
| **Preservar mesures** | Manté les mesures existents quan canvieu de LOT |

### 8.6 Aplicar la Plantilla

1. Seleccioneu els LOTs desitjats
2. Configureu les opcions
3. Feu clic a **"✅ Aplicar Plantilla"**

**Resultat:**
- Si seleccioneu **1 LOT**: S'actualitza la vista actual
- Si seleccioneu **múltiples LOTs**: Es creen pestanyes separades per cada LOT

### 8.7 Flux de Treball Recomanat

```
1. Configurar Referència
   └── Definir tots els elements (cotes, toleràncies, instruments)
   
2. Guardar Sessió
   └── La configuració es guarda com a plantilla base
   
3. Aplicar a Nous LOTs
   └── Utilitzar "Plantilla per LOT" per seleccionar nous LOTs
   
4. Introduir Mesures
   └── Només cal introduir les mesures, la configuració ja està
   
5. Analitzar i Comparar
   └── Executar anàlisi i comparar resultats entre LOTs
```

---

## 9. Anàlisi i Càlculs

### 9.1 Executar Anàlisi Dimensional

1. Assegureu-vos que teniu dades a la taula
2. Feu clic a **"🚀 Run Dimensional Study"**
3. Espereu que es completi l'anàlisi (barra de progrés)
4. Els resultats s'actualitzaran a les columnes calculades

### 9.2 Càlculs Realitzats

#### Estadístiques Bàsiques

| Càlcul | Fórmula | Descripció |
|--------|---------|------------|
| **Mínim** | min(x₁, x₂, ..., xₙ) | Valor més petit mesurat |
| **Màxim** | max(x₁, x₂, ..., xₙ) | Valor més gran mesurat |
| **Mitjana** | Σxᵢ / n | Promig de les mesures |
| **Desv. Estàndard** | √(Σ(xᵢ - x̄)² / (n-1)) | Dispersió de les mesures |

#### Índexs de Capacitat

| Índex | Fórmula | Interpretació |
|-------|---------|---------------|
| **Pp** | (USL - LSL) / 6σ | Capacitat potencial del procés |
| **Ppk** | min[(USL - x̄), (x̄ - LSL)] / 3σ | Capacitat real centrada |

On:
- USL = Límit Superior d'Especificació (Nominal + Tolerància Superior)
- LSL = Límit Inferior d'Especificació (Nominal + Tolerància Inferior)
- σ = Desviació estàndard
- x̄ = Mitjana

### 9.3 Interpretació dels Resultats

#### Valors de Pp/Ppk

| Valor | Interpretació | Acció |
|-------|---------------|-------|
| **≥ 1.67** | Excel·lent | Procés molt capaç |
| **1.33 - 1.67** | Bo | Procés capaç |
| **1.00 - 1.33** | Acceptable | Monitoritzar |
| **< 1.00** | Inadequat | Millora necessària |

#### Estats (Status)

| Estat | Significat | Color |
|-------|------------|-------|
| ✅ **OK** | Dins de tolerància | Verd |
| ❌ **NOK** | Fora de tolerància | Vermell |
| ⚠️ **TO CHECK** | Requereix revisió | Groc |
| 📝 **T.E.D.** | Tolerància d'enginyeria | Taronja |

### 9.4 Pestanya Summary (Resum)

La pestanya Summary mostra:

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 RESUM DE L'ESTUDI DIMENSIONAL                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📈 ESTADÍSTIQUES GENERALS                                   │
│ ────────────────────────                                    │
│ Total Elements:     25                                      │
│ Elements OK:        22 (88%)                                │
│ Elements NOK:       3 (12%)                                 │
│ Estudis Executats:  3                                       │
│                                                             │
│ 📊 CAPACITAT DE PROCÉS                                      │
│ ────────────────────────                                    │
│ Pp Mitjà:          1.45                                     │
│ Ppk Mitjà:         1.32                                     │
│ Pp Mínim:          0.98                                     │
│ Ppk Mínim:         0.85                                     │
│                                                             │
│ ⚠️ ELEMENTS CRÍTICS                                         │
│ ────────────────────────                                    │
│ • Nº005 - Diàmetre interior: Ppk = 0.85 (NOK)              │
│ • Nº012 - Planitud: Ppk = 0.92 (TO CHECK)                  │
│ • Nº018 - Concentricitat: Fora de tolerància               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Gestió de Sessions

### 10.1 Guardar Sessió

1. Feu clic a **"💾 Save"** o premeu **Ctrl+S**
2. Seleccioneu la ubicació i nom del fitxer
3. L'extensió serà `.dimensional_session`

**Contingut guardat:**
- Totes les dades de les taules
- Configuració d'elements
- Resultats de l'anàlisi
- Configuració de la vista

### 10.2 Carregar Sessió

1. Feu clic a **"📂 Load"** o premeu **Ctrl+O**
2. Seleccioneu el fitxer `.dimensional_session`
3. Les dades es carregaran a l'aplicació

### 10.3 Auto-guardtat

L'aplicació guarda automàticament:
- Cada 5 minuts (configurable)
- Després de cada anàlisi
- Abans de tancar (amb confirmació)

**Ubicació auto-guardats:** `data/sessions/autosave/`

### 10.4 Recuperar Sessions

Si l'aplicació es tanca inesperadament:
1. A l'iniciar, apareixerà un diàleg de recuperació
2. Seleccioneu la sessió a recuperar
3. Feu clic a "Recuperar"

---

## 11. Exportació de Dades

### 11.1 Formats d'Exportació

| Format | Extensió | Ús |
|--------|----------|-----|
| **Excel** | .xlsx | Informes complets amb format |
| **CSV** | .csv | Dades per importar a altres sistemes |
| **PDF** | .pdf | Informes per impressió |
| **JSON** | .json | Intercanvi de dades |

### 11.2 Exportar a Excel

1. Feu clic a **"📤 Export"**
2. Seleccioneu **"Excel (.xlsx)"**
3. Trieu la ubicació i nom
4. L'informe inclourà:
   - Capçalera amb informació del projecte
   - Taula de dades amb format
   - Gràfics de capacitat
   - Resum estadístic

### 11.3 Exportar a CSV

1. Feu clic a **"📤 Export"**
2. Seleccioneu **"CSV (.csv)"**
3. Trieu les opcions:
   - Separador (coma, punt i coma, tabulador)
   - Codificació (UTF-8, ANSI)
4. Guardeu el fitxer

### 11.4 Generar Informe PDF

1. Feu clic a **"📤 Export"**
2. Seleccioneu **"PDF Report"**
3. Configureu opcions de l'informe:
   - Incloure gràfics
   - Incloure resum
   - Format (A4, Letter)
4. Genereu l'informe

---

## 12. Estudis de Capacitat (SPC)

### 12.1 Accedir a Estudis de Capacitat

Des del menú principal o la barra d'eines:
- **"📊 Estudi de Capacitat"** o **"SPC Charts"**

### 12.2 Tipus de Gràfics Disponibles

| Gràfic | Descripció | Ús |
|--------|------------|-----|
| **X-bar R** | Mitjana i rang | Control de procés |
| **X-bar S** | Mitjana i desv. estàndard | Subgrups grans |
| **Histograma** | Distribució de dades | Anàlisi de normalitat |
| **Diagrama de Capacitat** | Pp/Ppk visual | Presentacions |

### 12.3 Interpretar Gràfics de Control

```
     UCL ─────────────────────── Límit Superior de Control
          ·   ·       ·   ·
      x̄  ─────·───·───────·───── Línia Central (Mitjana)
              ·   ·   ·
     LCL ─────────────────────── Límit Inferior de Control
```

**Senyals d'alarma:**
- Punt fora dels límits de control
- 7 punts consecutius per sobre o sota de la mitjana
- Tendències ascendents o descendents
- Patrons no aleatoris

---

## 13. Comparació Multi-LOT

### 13.1 Accedir a la Comparació

1. Menú **"Anàlisi"** → **"Comparar LOTs"**
2. O des del botó **"📊 Multi-LOT"**

### 13.2 Seleccionar LOTs a Comparar

1. Marqueu els LOTs que voleu comparar
2. Mínim 2 LOTs, màxim recomanat 10
3. Feu clic a **"Comparar"**

### 13.3 Resultats de la Comparació

La comparació mostra:

| Mètrica | LOT 1 | LOT 2 | LOT 3 | Tendència |
|---------|-------|-------|-------|-----------|
| Elements | 25 | 25 | 25 | = |
| OK (%) | 92% | 88% | 95% | ↑ |
| Pp Mitjà | 1.45 | 1.38 | 1.52 | ↑ |
| Ppk Mitjà | 1.32 | 1.25 | 1.41 | ↑ |

### 13.4 Exportar Comparació

Feu clic a **"Exportar Comparació"** per generar un informe amb:
- Taula comparativa
- Gràfics d'evolució
- Anàlisi de tendències

---

## 14. Resolució de Problemes

### 14.1 Problemes Comuns

#### L'aplicació no s'inicia

**Causa possible:** Dependències no instal·lades
```powershell
# Solució:
pip install -r requirements.txt
```

#### Error de connexió a base de dades

**Causa possible:** Configuració incorrecta
1. Verifiqueu `config/database/db_config.json`
2. Comproveu que el servidor està accessible
3. Verifiqueu credencials

#### Les dades no es carreguen

**Causa possible:** Permisos o filtres incorrectes
1. Comproveu els filtres de cerca
2. Verifiqueu permisos d'usuari
3. Reviseu el log: `logs/dimensional.log`

#### Error en l'anàlisi

**Causa possible:** Dades invàlides
1. Verifiqueu que tots els camps obligatoris estan omplerts
2. Comproveu que les toleràncies són correctes
3. Assegureu-vos que hi ha almenys 2 mesures

### 14.2 Registre d'Errors (Logs)

**Ubicació:** `logs/dimensional.log`

**Nivells de log:**
- `INFO` - Informació general
- `WARNING` - Avisos
- `ERROR` - Errors
- `DEBUG` - Informació detallada (mode debug)

### 14.3 Contactar Suport

Si el problema persisteix:
1. Copieu el missatge d'error
2. Adjunteu el fitxer de log
3. Descriviu els passos per reproduir l'error
4. Envieu a: suport@some.com

---

## 15. Dreceres de Teclat

### 15.1 Dreceres Generals

| Drecera | Acció |
|---------|-------|
| **Ctrl+S** | Guardar sessió |
| **Ctrl+O** | Obrir sessió |
| **Ctrl+E** | Exportar dades |
| **Ctrl+N** | Nova sessió |
| **Ctrl+Z** | Desfer |
| **Ctrl+Y** | Refer |
| **F5** | Actualitzar/Refrescar |
| **F1** | Ajuda |
| **Esc** | Cancel·lar/Tancar diàleg |

### 15.2 Dreceres de Taula

| Drecera | Acció |
|---------|-------|
| **Ctrl+C** | Copiar cel·les seleccionades |
| **Ctrl+V** | Enganxar des del portapapers |
| **Ctrl+X** | Retallar cel·les |
| **Ctrl+A** | Seleccionar tot |
| **Delete** | Netejar cel·les seleccionades |
| **Tab** | Moure a la següent cel·la |
| **Shift+Tab** | Moure a la cel·la anterior |
| **Enter** | Confirmar edició |
| **F2** | Editar cel·la seleccionada |
| **↑↓←→** | Navegar per la taula |

### 15.3 Dreceres d'Anàlisi

| Drecera | Acció |
|---------|-------|
| **Ctrl+R** | Executar anàlisi |
| **Ctrl+G** | Generar gràfics |
| **Ctrl+P** | Imprimir/PDF |

---

## 16. Glossari

### Termes Tècnics

| Terme | Definició |
|-------|-----------|
| **Batch/LOT** | Conjunt de peces fabricades sota les mateixes condicions |
| **Cavity** | Número de cavitat del motlle (per peces d'injecció) |
| **CMM** | Coordinate Measuring Machine (Màquina de mesura per coordenades) |
| **Cp** | Índex de capacitat potencial del procés |
| **Cpk** | Índex de capacitat real del procés (centrat) |
| **Datum** | Referència geomètrica per a mesures |
| **GD&T** | Geometric Dimensioning and Tolerancing |
| **LSL** | Lower Specification Limit (Límit inferior d'especificació) |
| **Nominal** | Valor teòric o de disseny |
| **Pp** | Índex de capacitat preliminar |
| **Ppk** | Índex de capacitat preliminar centrat |
| **PPAP** | Production Part Approval Process |
| **SPC** | Statistical Process Control |
| **USL** | Upper Specification Limit (Límit superior d'especificació) |

### Classificacions de Característiques

| Terme | Definició |
|-------|-----------|
| **CC (Critical)** | Afecta seguretat o compliment normatiu |
| **SC (Significant)** | Afecta funció o rendiment |
| **KC (Key)** | Característica clau per al client |
| **PC (Process)** | Controlada pel procés de fabricació |

### Estats de Mesura

| Terme | Definició |
|-------|-----------|
| **OK** | Dins de tolerància, procés capaç |
| **NOK** | Fora de tolerància o procés no capaç |
| **TO CHECK** | Requereix verificació addicional |
| **T.E.D.** | Tolerància d'Enginyeria Desviada (concessió) |

---

## 📞 Suport i Contacte

**Suport Tècnic:**
- Email: informatica@some.es


---

*© 2025 SOME - Tots els drets reservats*
*Manual d'Usuari v2.1.0 - Novembre 2025*
