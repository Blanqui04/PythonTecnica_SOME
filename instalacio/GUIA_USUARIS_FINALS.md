# 📖 GUIA D'INSTAL·LACIÓ PER USUARIS FINALS
## PythonTecnica SOME - Versió Estable

### 🎯 **RESUM RÀPID:**
1. Instal·lar Python (només una vegada)
2. Descarregar aplicació 
3. Executar SETUP.bat (només una vegada)
4. Executar RUN_APP.bat (cada vegada que la vulguis usar)

---

## 📋 **PAS A PAS DETALLAT:**

### **ABANS DE COMENÇAR:**
- Assegura't que tens connexió a internet
- Tens permisos d'administrador al PC
- Tens almenys 500MB d'espai lliure

---

### **PAS 1: INSTAL·LAR PYTHON** ⚠️ MOLT IMPORTANT

1. **Descarregar Python:**
   - Anar a: https://www.python.org/downloads/
   - Clic "Download Python 3.12.x" (o la versió més recent)

2. **Instal·lar Python:**
   - Executar el fitxer descarregat
   - ✅ **MARCAR: "Add Python to PATH"** (OBLIGATORI!)
   - Clic "Install Now"
   - Esperar que acabi
   - **Reiniciar el PC**

3. **Verificar instal·lació:**
   - Obrir "Símbol del sistema" (cmd)
   - Escriure: `python --version`
   - Ha de mostrar la versió de Python

---

### **PAS 2: DESCARREGAR L'APLICACIÓ**

#### **Mètode Recomanat (ZIP):**
1. Anar a: https://github.com/Blanqui04/PythonTecnica_SOME/tree/PythonTecnica-SOME-Stable
2. Clic botó verd **"Code"**
3. Clic **"Download ZIP"**
4. Guardar a l'escriptori o carpeta que vulguis
5. Clic dret al ZIP → **"Extreure tot"**
6. Triar carpeta destí (ex: `C:\PythonTecnica\`)

#### **Mètode Alternatiu (Git):**
Si tens Git instal·lat:
```cmd
git clone -b PythonTecnica-SOME-Stable https://github.com/Blanqui04/PythonTecnica_SOME.git
```

---

### **PAS 3: CONFIGURAR L'APLICACIÓ** (només una vegada)

1. **Obrir la carpeta** on has extret l'aplicació
2. **Doble clic a `SETUP.bat`**
3. **Esperar** que aparegui una finestra negra
4. El script farà:
   - Verificar que Python està instal·lat
   - Crear un entorn virtual
   - Descarregar totes les llibreries necessàries
   - Configurar tot automàticament
5. **Quan acabi**, apareixerà "CONFIGURACIÓ COMPLETADA!"
6. **Premere qualsevol tecla** per tancar

⏱️ **Temps aproximat:** 5-10 minuts (depèn de la velocitat d'internet)

---

### **PAS 4: EXECUTAR L'APLICACIÓ** (cada vegada)

1. **Anar a la carpeta** de l'aplicació
2. **Doble clic a `RUN_APP.bat`**
3. **L'aplicació s'obre automàticament**

🎉 **Fet! L'aplicació ja està funcionant**

---

## 🚨 **RESOLUCIÓ DE PROBLEMES COMUNS:**

### **"Python no està instal·lat"**
- Python no està instal·lat o no està al PATH
- **Solució:** Tornar al PAS 1 i assegurar-se de marcar "Add Python to PATH"

### **"Entorn virtual no trobat"**
- El SETUP.bat no s'ha executat correctament
- **Solució:** Executar `CLEAN.bat` i després `SETUP.bat` altra vegada

### **Error durant SETUP.bat**
- Problemes de connexió a internet o permisos
- **Solució:** 
  1. Executar com a administrador (clic dret → "Executar com a administrador")
  2. Comprovar connexió a internet
  3. Desactivar temporalment l'antivirus

### **L'aplicació no s'obre**
- **Solució:** Executar `VERIFY_SYSTEM.bat` per veure què passa

### **Vull reinstal·lar tot**
- **Solució:** Executar `CLEAN.bat` i després `SETUP.bat`

---

## 📞 **SUPORT TÈCNIC:**

Si continues tenint problemes:

1. **Executar `VERIFY_SYSTEM.bat`**
2. **Copiar tot el text** que apareix
3. **Contactar amb l'administrador** amb:
   - Sistema operatiu (Windows 10/11)
   - Versió de Python (`python --version`)
   - Output del VERIFY_SYSTEM.bat
   - Captura de pantalla de l'error

---

## 🔄 **ACTUALITZACIONS:**

Quan surti una nova versió:
1. Descarregar la nova versió
2. Executar `CLEAN.bat` (opcional)
3. Executar `SETUP.bat`
4. Tot actualitzat!

---

## 📁 **FITXERS IMPORTANTS:**

| Fitxer | Quan usar-lo |
|--------|-------------|
| `SETUP.bat` | Primera instal·lació o després de problemes |
| `RUN_APP.bat` | Cada vegada que vulguis usar l'aplicació |
| `VERIFY_SYSTEM.bat` | Per diagnosticar problemes |
| `CLEAN.bat` | Per netejar i reinstal·lar |

---

**🎯 Recordatori:** Només cal fer SETUP.bat una vegada per PC. Després, sempre RUN_APP.bat!