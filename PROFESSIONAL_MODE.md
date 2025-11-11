# 🎨 Mode Professional - Sense Finestra de Consola

## Què ha canviat?

Hem millorat l'experiència d'usuari per fer l'aplicació més professional:

### ✨ Abans
Quan executaves `run_app.bat`, es veien **2 finestres**:
- ❌ Finestra CMD negra (consola)
- ✅ Interfície gràfica de l'aplicació

### ✨ Ara
Quan executes `run_app.bat`, només veus **1 finestra**:
- ✅ Interfície gràfica de l'aplicació (experiència professional)

---

## 📋 Scripts Disponibles

### 1️⃣ `run_app.bat` (MODE NORMAL)
**Quan utilitzar:** Ús diari normal

**Què fa:**
- Obre només la interfície gràfica
- NO mostra finestra de consola
- Experiència professional i neta

```cmd
run_app.bat
```

### 2️⃣ `run_app_debug.bat` (MODE DEBUG)
**Quan utilitzar:** Si hi ha problemes o errors

**Què fa:**
- Obre la interfície gràfica
- TAMBÉ mostra finestra de consola
- Veus missatges d'error i logs
- Útil per troubleshooting

```cmd
run_app_debug.bat
```

### 3️⃣ `create_desktop_shortcut.bat` (OPCIONAL)
**Quan utilitzar:** Per crear icona a l'escriptori

**Què fa:**
- Crea un accés directe a l'escriptori
- Nom: "PythonTecnica SOME"
- Al fer doble clic, executa `run_app.bat`
- Si tens icona personalitzada a `assets/images/gui/app_icon.ico`, la utilitzarà

```cmd
create_desktop_shortcut.bat
```

---

## 🔧 Com Funciona?

### Tecnologia Utilitzada

**Python** té 2 executables:
- `python.exe` → Amb consola (mostra finestra CMD)
- `pythonw.exe` → Sense consola (només GUI)

Hem canviat `run_app.bat` per utilitzar `pythonw.exe`, que és l'estàndard per aplicacions gràfiques professionals.

### Codi Abans vs Ara

**Abans:**
```bat
call venv\Scripts\activate.bat
python main_app.py
```
→ Mostra consola + GUI

**Ara:**
```bat
start "" "venv\Scripts\pythonw.exe" main_app.py
```
→ Només mostra GUI

---

## ❓ Preguntes Freqüents

### On van els errors si no veig la consola?

Els errors es guarden automàticament als logs:
```
data/logs/
```

També pots executar `run_app_debug.bat` per veure errors en temps real.

### Com sé si l'aplicació està oberta?

Mira:
- La finestra de l'aplicació (oberta)
- El Gestor de Tasques → `pythonw.exe` en execució

### Vull tornar a veure la consola sempre

Opció 1: Utilitza `run_app_debug.bat` sempre

Opció 2: Modifica `run_app.bat`:
```bat
REM Canvia aquesta línia:
start "" "venv\Scripts\pythonw.exe" main_app.py

REM Per aquesta:
call venv\Scripts\activate.bat
python main_app.py
```

### L'aplicació no s'obre i no veig res

1. Executa `run_app_debug.bat` per veure què passa
2. Revisa els logs a `data/logs/`
3. Verifica que `setup.bat` ha completat correctament

---

## 📦 Per Desenvolupadors

Si estàs desenvolupant i vols veure prints i logs:

```cmd
# Utilitzar sempre:
run_app_debug.bat

# O des de terminal:
venv\Scripts\activate
python main_app.py
```

---

## ✅ Avantatges del Mode Professional

✅ **Experiència neta**: Només veus la UI que necessites
✅ **Menys confusió**: Els usuaris no tanquen accidentalment la consola
✅ **Aspecte professional**: Com qualsevol aplicació comercial
✅ **Flexibilitat**: Mode debug disponible quan cal

---

**Gràcies per utilitzar PythonTecnica SOME!**
