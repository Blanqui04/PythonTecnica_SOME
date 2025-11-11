# 📦 PythonTecnica SOME v2.0.0

## 🚀 Instal·lació Ràpida

### Requisits Previs

- **Windows 10/11** (64-bit)
- **Python 3.9 o superior** ([Descarregar aquí](https://www.python.org/downloads/))
  - ⚠️ **IMPORTANT:** Durant la instal·lació, marca **"Add Python to PATH"**

### Passos d'Instal·lació

1. **Descarrega** el codi des de [GitHub Releases](https://github.com/Blanqui04/PythonTecnica_SOME/releases)
   - Descarrega `Source code (zip)`

2. **Descomprimeix** l'arxiu a la ubicació desitjada
   - Exemple: `C:\PythonTecnica_SOME\`

3. **Executa `setup.bat`** (només la primera vegada)
   - Click dret → **Executar com a administrador**
   - Espera que s'instal·lin totes les dependencies (2-5 minuts)

4. **Executa `run_app.bat`** per obrir l'aplicació
   - S'obre directament sense finestra de consola (mode professional)
   
5. **[OPCIONAL]** Crea un accés directe a l'escriptori:
   - Executa `create_desktop_shortcut.bat`
   - Apareixerà una icona "PythonTecnica SOME" a l'escriptori

---

## 📋 Ús Diari

### Iniciar l'Aplicació

**Mode Normal** (sense consola):
```
run_app.bat
```
- S'obre només la interfície gràfica
- Experiència professional, sense finestres extra

**Mode Debug** (amb consola per troubleshooting):
```
run_app_debug.bat
```
- Mostra la consola amb missatges d'error
- Útil per diagnosticar problemes

### Primera Vegada

Després de descarregar:
1. Executa `setup.bat` → Instal·la dependencies (NOMÉS 1 VEGADA)
2. Executa `run_app.bat` → Obre l'aplicació (SEMPRE)
3. [Opcional] `create_desktop_shortcut.bat` → Crea icona a l'escriptori

---

## 🔧 Configuració

### Connexió a Base de Dades

La configuració per defecte ja està establerta:
- **Servidor:** 172.26.11.201:5432
- **Base de Dades:** documentacio_tecnica
- **Usuari:** tecnica

Si necessites canviar-la, edita:
```
config/database/db_config.json
```

---

## ✨ Novetats v2.0.0

### Mòdul d'Estudis de Capacitat

- **Anàlisi estadístic:** Cp, Cpk, Pp, Ppk
- **Gràfics interactius:** Histogrames, control charts
- **Exportació PDF:** Informes professionals
- **1.15M+ registres** de dades

### Millores

- Auto-detecció de schema 'qualitat'
- Queries optimitzades amb UNION
- Integració amb dades actualitzades automàticament
- Millor gestió d'errors

---

## 🆘 Solució de Problemes

### Error: "Python no està instal·lat"

**Solució:**
1. Descarrega Python des de [python.org](https://www.python.org/downloads/)
2. Instal·la marcant **"Add Python to PATH"**
3. Reinicia l'ordinador
4. Torna a executar `setup.bat`

### Error: "No s'ha pogut instal·lar dependencies"

**Solució:**
```cmd
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Error: "L'entorn virtual no existeix"

**Solució:**
Executa `setup.bat` abans de `run_app.bat`

### Error de connexió a base de dades

**Verificar:**
- Tens connexió a la xarxa interna
- El servidor PostgreSQL està accessible (172.26.11.201)
- Les credencials són correctes

**Contactar:** Administrador de BD

### L'aplicació no mostra dades

**Possible causa:** Les dades encara no s'han sincronitzat

**Solució:**
- Espera a la propera sincronització nocturna (00:00)
- O contacta l'administrador per forçar sincronització

---

## 📂 Estructura del Projecte

```
PythonTecnica_SOME/
├── main_app.py              ← Punt d'entrada principal
├── setup.bat                ← Instal·lació (1 vegada)
├── run_app.bat              ← Executar aplicació
├── requirements.txt         ← Dependencies Python
├── config/                  ← Configuració
│   ├── database/
│   │   └── db_config.json
│   └── requirements.txt
├── src/                     ← Codi font
│   ├── gui/                 ← Interfície gràfica
│   ├── services/            ← Lògica de negoci
│   ├── database/            ← Gestió BD
│   └── reports/             ← Generació informes
├── assets/                  ← Recursos (imatges, etc.)
├── i18n/                    ← Traduccions
├── data/                    ← Dades locals
│   └── logs/                ← Logs de l'aplicació
└── venv/                    ← Entorn virtual (creat per setup.bat)
```

---

## 🔄 Actualitzacions

### Per actualitzar a una nova versió:

1. **Descarrega** la nova versió des de GitHub Releases
2. **Descomprimeix** a una carpeta nova
3. **Copia** la configuració de la versió anterior:
   ```
   Copia: config/database/db_config.json
   A: [nova_versió]/config/database/
   ```
4. **Executa** `setup.bat` a la nova versió
5. **Executa** `run_app.bat`

### O simplement:

Sobreescriu tots els fitxers EXCEPTE:
- `config/database/db_config.json` (si l'has personalitzat)
- `venv/` (pots eliminar-lo i tornar a executar setup.bat)

---

## 📞 Suport

- **GitHub:** [PythonTecnica_SOME](https://github.com/Blanqui04/PythonTecnica_SOME)
- **Issues:** [Reportar problema](https://github.com/Blanqui04/PythonTecnica_SOME/issues)

---

## 📄 Llicència

Desenvolupat per l'equip SOME - 2025

---

## ✅ Checklist Post-Instal·lació

Després d'instal·lar, verifica que:

- [ ] `setup.bat` ha completat sense errors
- [ ] `run_app.bat` obre l'aplicació
- [ ] Pots fer login
- [ ] La connexió a BD funciona
- [ ] Pots accedir al mòdul d'estudis de capacitat
- [ ] Les dades es carreguen correctament

Si tot funciona → **Tot correcte!** 🎉

---

**Gràcies per utilitzar PythonTecnica SOME!**
