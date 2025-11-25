# 🚀 Guia Ràpida - PythonTecnica SOME

## Començar en 5 Minuts

### 1. Iniciar l'Aplicació
```
Doble clic a RUN_APP.bat
```

### 2. Introduir Dades del Projecte
- **Client:** Seleccionar de la llista
- **Referència:** Codi del projecte/peça
- **LOT/Batch:** Número de lot

### 3. Modes de Treball

| Mode | Quan Utilitzar |
|------|----------------|
| **Automàtic** | Carregar dades de la base de dades |
| **Manual** | Introduir dades manualment |

---

## ⌨️ Dreceres Essencials

| Drecera | Acció |
|---------|-------|
| **Ctrl+C** | Copiar |
| **Ctrl+V** | Enganxar |
| **Ctrl+S** | Guardar |
| **Ctrl+O** | Obrir |
| **Delete** | Esborrar |

---

## 📋 Copiar des d'Excel

1. **Excel:** Seleccionar cel·les → Ctrl+C
2. **App:** Seleccionar cel·la destí → Ctrl+V
3. ✅ Les dades s'enganxen automàticament

---

## 📐 Plantilles per Referència i LOT

### Crear Plantilla Base

1. Configura tots els elements (toleràncies, instruments)
2. Clic a **"📐 Plantilla per LOT"**
3. Pestanya **"📋 Plantilles Base"**
4. Introdueix nom, client, referència
5. Clic a **"💾 Guardar com a Nova Plantilla"**

### Treballar amb un LOT

1. Clic a **"📐 Plantilla per LOT"**
2. Pestanya **"📋 Plantilles Base"** → Selecciona i **"📂 Carregar"**
3. Pestanya **"📦 Treballar per LOT"**
4. Selecciona el LOT
5. Clic a **"✅ Treballar amb aquest LOT"**

### Guardar/Carregar Estudis

- Pestanya **"📊 Estudis per LOT"** per veure estudis guardats
- Els estudis es guarden automàticament per LOT

---

## 🚀 Executar Anàlisi

1. Verificar que les dades estan completes
2. Clic a **"🚀 Run Dimensional Study"**
3. Esperar que es completi
4. Revisar resultats a les columnes calculades

---

## 📊 Interpretar Resultats

| Estat | Significat |
|-------|------------|
| ✅ OK | Dins de tolerància |
| ❌ NOK | Fora de tolerància |
| ⚠️ TO CHECK | Requereix revisió |

| Ppk | Qualitat |
|-----|----------|
| ≥ 1.33 | ✅ Capaç |
| 1.00 - 1.33 | ⚠️ Acceptable |
| < 1.00 | ❌ No capaç |

---

## 💾 Guardar i Exportar

- **Guardar:** Ctrl+S o botó 💾
- **Exportar Excel:** Botó 📤 → Excel
- **Exportar PDF:** Botó 📤 → PDF

---

## ❓ Ajuda

- **Manual complet:** `docs/MANUAL_USUARI_COMPLET.md`
- **Logs:** `logs/dimensional.log`
- **Suport:** suport@some.com

---

*v2.1.0 - Novembre 2025*
