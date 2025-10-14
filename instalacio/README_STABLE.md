# 🚀 PythonTecnica SOME - Versió Estable d'Instal·lació

> **Aquesta és la versió estable preparada per a distribució i ús en producció**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Stable](https://img.shields.io/badge/status-stable-green.svg)]()
[![Windows](https://img.shields.io/badge/platform-windows-lightgrey.svg)]()

## 📦 Instal·lació Ultra-Ràpida

### Prerequisits
- **Python 3.8+** instal·lat amb "Add to PATH" activat
- Sistema Windows 10/11
- Connexió a internet per descarregar dependències

### Passos d'instal·lació

1. **Descarregar el codi**
   ```bash
   git clone https://github.com/[TU_USUARI]/PythonTecnica-SOME-Stable.git
   cd PythonTecnica-SOME-Stable
   ```
   
   *O descarregar com a ZIP i extreure*

2. **Configurar automàticament**
   ```cmd
   SETUP.bat
   ```
   
3. **Executar l'aplicació**
   ```cmd
   RUN_APP.bat
   ```

**Això és tot!** L'aplicació s'obrirà automàticament.

## 🛠️ Scripts Disponibles

| Script | Funció |
|--------|--------|
| `SETUP.bat` | Configuració inicial (només una vegada) |
| `RUN_APP.bat` | Executar l'aplicació |
| `VERIFY_SYSTEM.bat` | Verificar instal·lació |
| `CLEAN.bat` | Netejar i reinstal·lar |

## ⚡ Característiques Principals

- 📊 **Anàlisi SPC i Capacitat** - Control estadístic de processos
- 📈 **Gràfics Interactius** - Visualitzacions professionals
- 🗄️ **Gestió Base de Dades** - PostgreSQL integrat
- 📄 **Processament Excel** - Importació i exportació automàtica
- 🎯 **Interfície Intuïtiva** - PyQt5 moderna i responsiva

## 🔧 Requisits Tècnics

- **RAM:** 2GB mínim, 4GB recomanat
- **Disc:** 500MB espai lliure
- **SO:** Windows 10/11 (64-bit)
- **Python:** 3.8, 3.9, 3.10, 3.11 o 3.12

## 🚨 Resolució de Problemes

### Error: "Python no detectat"
```cmd
# Descarregar Python de: https://www.python.org/downloads/
# IMPORTANT: Marcar "Add Python to PATH" durant la instal·lació
```

### Error: "Entorn virtual no trobat"
```cmd
CLEAN.bat
SETUP.bat
```

### L'aplicació no s'obre
```cmd
VERIFY_SYSTEM.bat
```

## 📞 Suport Tècnic

Si tens problemes:

1. Executar `VERIFY_SYSTEM.bat` i enviar l'output
2. Comprovar que Python està instal·lat: `python --version`
3. Crear un **Issue** en aquest repositori amb:
   - Sistema operatiu i versió
   - Versió de Python
   - Missatge d'error complet
   - Passos per reproduir el problema

## 🔄 Actualitzacions

Aquest fork es manté sincronitzat amb versions estables del repositori principal. Les actualitzacions inclouen:

- Correccions de bugs crítics
- Millores de rendiment
- Noves funcionalitats testejades
- Actualitzacions de seguretat

Per actualitzar:
```cmd
git pull origin main
CLEAN.bat
SETUP.bat
```

## 📜 Llicència

Aquest projecte està sota llicència MIT. Veure el fitxer LICENSE per més detalls.

---

**🎯 Objectiu d'aquest fork:** Proporcionar una versió estable, fàcil d'instal·lar i mantenir de PythonTecnica SOME per a usuaris finals i entorns de producció.