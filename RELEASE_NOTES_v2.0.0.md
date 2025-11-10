# 📦 PythonTecnica SOME v2.0.0 - Release Notes

**Data de Release:** 10 de Novembre de 2025  
**Versió:** 2.0.0  
**Branch:** Report-estudi-capacitat

---

## 🎉 Novetats Principals

### ✨ Mòdul d'Estudis de Capacitat

- **Anàlisi estadístic complet** amb càlcul de Cp, Cpk, Pp, Ppk
- **Gràfics interactius**: histogrames, gràfics de control, distribució normal
- **Exportació a PDF** amb informes professionals
- **Filtratge avançat** per client, projecte, element, datum, property
- **Suport per grans volums** de dades (1.15M+ registres)

### 🔄 Millores de Base de Dades

- **Auto-detecció de schema** 'qualitat' amb fallback a 'public'
- **Queries optimitzades** amb UNION per combinar múltiples taules
- **Integració amb Airflow ETL** per dades actualitzades automàticament
- **Sincronització nocturna** configurada

### 🐛 Correccions

- Resolt bug de connexió a PostgreSQL
- Millores en gestió d'errors i missatges informatius
- Optimització de rendiment en càrrega de dades
- Correcció de problemes amb codificació de caràcters

---

## 📊 Especificacions Tècniques

### Requisits del Sistema

- **Sistema Operatiu:** Windows 10/11 (64-bit)
- **RAM:** Mínim 4GB, recomanat 8GB+
- **Disc:** 500MB d'espai lliure
- **Connexió:** Accés a PostgreSQL (172.26.11.201:5432)

### Credencials Requerides

- **Usuari BD:** tecnica
- **Contrasenya:** Some2025.!$%
- **Base de Dades:** documentacio_tecnica
- **Schema:** qualitat (auto-detectat)

### Taules Utilitzades

- `mesures_gompcnou` (28 columnes)
- `mesures_gompc_projectes` (28 columnes, 1.15M+ registres)
- `mesureshoytom` (46 columnes)
- `mesurestorsio` (38 columnes)

---

## 📥 Instal·lació

### Actualització des de v1.x

1. **Descarrega** `PythonTecnica_SOME_v2.0.0.zip` des de GitHub Releases
2. **Descomprimeix** l'arxiu a una carpeta temporal
3. **Executa** `INSTALAR.bat` (com a administrador si cal)
4. El script detectarà automàticament la versió anterior
5. **Preservarà** la teva configuració existent
6. **Actualitzarà** tots els fitxers necessaris

### Instal·lació Nova

1. **Descarrega** `PythonTecnica_SOME_v2.0.0.zip`
2. **Descomprimeix** a la ubicació desitjada (ex: `C:\Program Files\PythonTecnica_SOME\`)
3. **Executa** `PythonTecnica_SOME.exe`
4. **Configura** les credencials de base de dades (ja preconfigurades)

---

## 🚀 Primeres Passes

### Accedir al Mòdul d'Estudis de Capacitat

1. Obre l'aplicació
2. **Login** amb les teves credencials d'usuari
3. Al menú principal, selecciona **"Estudis de Capacitat"**
4. Selecciona els filtres desitjats:
   - Client
   - Projecte (id_referencia_client)
   - Element
   - Datum
   - Property
5. Clica **"Generar Estudi"**
6. **Revisa** els resultats estadístics i gràfics
7. **Exporta** a PDF si cal

### Exemple d'Ús

**Cas d'ús:** Analitzar capacitat del projecte AUTOLIV_PRJ1205926A

```
Filtres:
- Client: AUTOLIV
- Projecte: PRJ1205926A
- Element: N15
- Datum: (tots)
- Property: X

Resultats esperats:
- Histograma amb distribució normal
- Cp, Cpk calculats
- Gràfic de control amb LSL/USL
- Informe PDF generat
```

---

## 🔧 Configuració Avançada

### Canviar Connexió a Base de Dades

Si necessites modificar la connexió:

1. Navega a: `<INSTALL_DIR>\config\database\db_config.json`
2. Edita els paràmetres:
   ```json
   {
       "primary": {
           "host": "172.26.11.201",
           "port": "5432",
           "database": "documentacio_tecnica",
           "user": "tecnica",
           "password": "Some2025.!$%"
       }
   }
   ```
3. Guarda i reinicia l'aplicació

### Logs i Diagnòstic

Els logs es generen a:
```
%LOCALAPPDATA%\PythonTecnica_SOME\logs\
```

Tipus de logs:
- `app.log` - Log general de l'aplicació
- `database.log` - Connexions i queries
- `errors.log` - Errors i excepcions

---

## 🆘 Solució de Problemes

### L'aplicació no inicia

1. **Verifica l'antivirus:** Afegeix excepció per `PythonTecnica_SOME.exe`
2. **Executa com a administrador:** Click dret → "Executar com a administrador"
3. **Comprova logs:** Revisa `%LOCALAPPDATA%\PythonTecnica_SOME\logs\errors.log`

### Error de connexió a base de dades

```
Error: connection refused / timeout
```

**Solucions:**
1. Verifica connexió de xarxa al servidor `172.26.11.201`
2. Comprova que el servei PostgreSQL està actiu
3. Verifica credencials a `config/database/db_config.json`
4. Contacta amb l'administrador de BD

### No es carreguen dades / Taula buida

```
Schema: public (en lloc de qualitat)
```

**Solucions:**
1. L'aplicació està utilitzant schema 'public' (legacy)
2. Pot ser que les dades encara no s'hagin sincronitzat
3. Espera a la propera sincronització nocturna (00:00)
4. O contacta l'administrador per forçar sincronització

### Error al generar PDF

```
Error: Permission denied / Access denied
```

**Solucions:**
1. Tanca qualsevol PDF obert de l'aplicació
2. Verifica permisos d'escriptura a la carpeta de destí
3. Selecciona una carpeta diferent per exportar

---

## 📞 Suport

### Contacte

- **Repositori:** https://github.com/Blanqui04/PythonTecnica_SOME
- **Issues:** https://github.com/Blanqui04/PythonTecnica_SOME/issues
- **Administrador BD:** [Contacte intern]

### Reportar Bugs

1. Ves a GitHub Issues
2. Crea un nou issue amb:
   - Títol descriptiu
   - Passos per reproduir
   - Comportament esperat vs. obtingut
   - Screenshots si escau
   - Logs rellevants

---

## 🔄 Roadmap Futur

### v2.1.0 (Planificat)

- [ ] Més tipus de gràfics (Pareto, scatter plots)
- [ ] Exportació a Excel
- [ ] Comparació entre projectes
- [ ] Dashboard amb mètriques globals

### v2.2.0 (Planificat)

- [ ] Anàlisi de tendències temporals
- [ ] Alertes automàtiques
- [ ] Integració amb altres sistemes
- [ ] Millores de rendiment

---

## 📄 Llicència i Crèdits

**Desenvolupat per:** Equip SOME  
**Repositori:** PythonTecnica_SOME  
**Data:** 2025  

---

## ✅ Checklist Post-Instal·lació

Després d'instal·lar, verifica:

- [ ] L'aplicació inicia correctament
- [ ] Login funcional
- [ ] Connexió a BD establerta
- [ ] Schema 'qualitat' detectat
- [ ] Mòdul d'estudis de capacitat accessible
- [ ] Dades carreguen correctament
- [ ] Gràfics es generen
- [ ] Exportació PDF funcional

---

**Gràcies per utilitzar PythonTecnica SOME!** 🚀

Si tens qualsevol pregunta o suggeriment, no dubtis en contactar-nos.
