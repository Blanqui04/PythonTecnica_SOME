# PythonTecnica_SOME v2.0.0

## Overview

PythonTecnica_SOME is a modular Python application for technical and business data processing, statistical analysis (SPC/capability), and database/reporting workflows. It features a modern PyQt5 GUI, advanced charting, and robust session management.

## 🚀 Instal·lació Ràpida

### Requisits
- **Windows 10/11** (64-bit)
- **Python 3.9+** ([Descarregar](https://www.python.org/downloads/))
  - ⚠️ **IMPORTANT:** Marca "Add Python to PATH" durant la instal·lació

### Instal·lació pas a pas

1. **Descarrega** el codi font:
   - Desde [GitHub Releases](https://github.com/Blanqui04/PythonTecnica_SOME/releases) → `Source code (zip)`
   - O clonar: `git clone https://github.com/Blanqui04/PythonTecnica_SOME.git`

2. **Verifica prerequisits** (opcional):
   ```cmd
   check_prerequisites.bat
   ```

3. **Configura l'entorn** (només primera vegada):
   ```cmd
   setup.bat
   ```
   - Crea l'entorn virtual
   - Instal·la totes les dependències
   - 2-5 minuts d'espera

4. **Executa l'aplicació**:
   ```cmd
   run_app.bat
   ```

### Scripts disponibles
- `check_prerequisites.bat` - Verifica Python i connectivitat
- `setup.bat` - Configuració inicial (només 1 vegada)
- `run_app.bat` - Executar l'aplicació (sense consola, mode professional)
- `run_app_debug.bat` - Executar amb consola visible (per debugging)
- `create_desktop_shortcut.bat` - Crear accés directe a l'escriptori
- `verify_setup.py` - Verificar base de dades i configuració

📖 **Guia completa d'instal·lació**: Veure [INSTALL.md](INSTALL.md)

📖 **Notes de versió**: Veure [RELEASE_NOTES_v2.0.0.md](RELEASE_NOTES_v2.0.0.md)

---

## Project Structure

```
PythonTecnica_SOME/
│
├── src/
│   ├── __init__.py
│   ├── data_processing/
│   │   ├── utils/
│   │   ├── data_processor.py
│   │   ├── data_transformer.py
│   │   └── pipeline_manager.py
│   ├── database/
│   │   ├── database_connection.py
│   │   └── database_uploader.py
│   ├── exceptions/
│   │   ├── transformation_errors.py
│   │   └── sample_errors.py
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── logging_config.py
│   │   ├── widgets/
│   │   │   ├── element_input_widget.py
│   │   │   ├── element_edit_dialog.py
│   │   │   ├── realtime_calculations_panel.py
│   │   │   ├── buttons.py
│   │   │   ├── inputs.py
│   │   ├── panels/
│   │   ├── workers/
│   │   │   └── capability_study_worker.py
│   │   ├── windows/
│   │   │   ├── capability_study_window.py
│   │   │   ├── spc_chart_window.py
│   │   └── utils/
│   │       ├── chart_utils.py
│   │       ├── element_input_styles.py
│   │       ├── session_manager.py
│   │       └── styles.py
│   ├── models/
│   │   ├── plotting/
│   │   │   ├── spc_charts_manager.py
│   │   │   ├── base_chart.py
│   │   │   ├── spc_data_loader.py
│   │   │   ├── capability_chart.py
│   │   │   ├── normality_plot.py
│   │   │   ├── extrapolation_chart.py
│   │   │   ├── i_chart.py
│   │   │   └── mr_chart.py
│   │   ├── capability/
│   │   │   ├── capability_analyzer.py
│   │   │   ├── capability_study_manager.py
│   │   │   ├── extrapolation_manager.py
│   │   │   ├── sample_data_manager.py
│   │   └── dimensional/
│   │       ├── dimensional_analyzer.py
│   │       └── gdt_interpreter.py
│   ├── services/
│   │   ├── capacity_study_service.py
│   │   ├── spc_chart_service.py
│   │   ├── data_export_service.py
│   │   ├── measurement_history_service.py
│   │   └── database_update.py
│   └── utils/
│       └── __init__.py
│
├── data/
│   ├── sessions/
│   ├── spc/
│   ├── reports/
│   ├── processed/
│   └── temp/
│
├── config/
│   ├── database/
│   ├── column_mappings/
│   └── config.ini
│
├── assets/
│   ├── images/
│   └── templates/
│
├── i18n/
│   ├── ca.json
│   ├── en.json
│   └── pl.json
│
├── logs/
│   ├── gui.log
│   └── db_operations.log
│
├── tests/
│   ├── test_orchestrator.py
│   ├── test_spc_charts.py
│   ├── test_spc_manager.py
│   ├── test_data_uploader.py
│   ├── test_kop_processing.py
│   ├── test_data_transformer.py
│   ├── test_dimensional_analyzer.py
│   ├── test_dimensional_export.py
│   └── test_excel_processing.py
│
├── docs/
│   ├── capability/
│   ├── ddbb/
│   └── dimensional/
│
├── main_app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Key Scripts & Entry Points

- **main_app.py**: Launches the main PyQt5 GUI application.
- **src/gui/main_window.py**: Main application window and navigation.
- **src/gui/windows/capability_study_window.py**: Capability study workflow (input, run, results, export).
- **src/gui/windows/spc_chart_window.py**: Interactive SPC chart viewer and exporter.
- **src/services/capacity_study_service.py**: Orchestrates capability study calculations and chart generation.
- **src/services/spc_chart_service.py**: Handles SPC chart creation and management.
- **src/models/capability/capability_study_manager.py**: Core capability study logic and result management.
- **src/models/plotting/spc_charts_manager.py**: Loads and manages SPC chart data and files.
- **src/gui/utils/session_manager.py**: Session save/load for study configurations and results.

---

## New & Enhanced Features

- **Session Management**: Save/load full study sessions, including all elements, settings, and results.
- **Modern GUI**: Responsive, scalable PyQt5 interface with scrollable and resizable panels.
- **Manual & Database Entry**: Add elements manually or load from database, with class and sigma selection.
- **Editable Metrics**: Edit measured values and statistical metrics (average, deviations) per element.
- **Advanced Extrapolation**: Configure p-value, attempts, and target sample size for extrapolation.
- **Real-Time Indicators**: Live summary and per-element metrics, color-coded and editable.
- **SPC Charting**: Generate and view all SPC/capability charts in-app, with export options.
- **Results Tab**: Charts and metrics are shown directly in the Results tab (no popups).
- **Export**: Export study results and charts from the Results tab.
- **Scalable Layouts**: All panels and chart displays are scrollable and adapt to large datasets.

---

## Usage

### Running the Application

```sh
python main_app.py
```

### Main Workflows

- **Add Elements**: Use the configuration tab to add elements (manual or database), set class and sigma, and input values.
- **Edit Metrics**: Click "Edit" on any element to modify values or metrics.
- **Configure Extrapolation**: Set p-value, attempts, and target sample size as needed.
- **Run Study**: Click "Run Study" to calculate all metrics and generate charts.
- **View Results**: Switch to the Results tab to see all charts and export options.
- **Save/Load Session**: Use the session controls to save or restore your work at any time.

---

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies.

---

## Contributing

- Follow the modular structure.
- Write tests for new features.
- Update documentation as needed.

---

## License

[Specify your license here]

---

## Contact

[Add contact or maintainer info here]

---
- **🔄 Data Processing Pipeline**: Automated Excel processing with KOP client support
- **📊 Statistical Analysis**: Capability studies, SPC charts, and normality analysis
- **🖥️ Modern GUI**: PyQt5 interface with PDF viewer toggle functionality
- **�️ Database Editor**: Visual database table editor with real-time editing, querying, and data management
- **�📁 Smart Export**: Data export directly to user's Downloads folder with cross-platform support
- **🗄️ Database Integration**: PostgreSQL connection with automatic data upload
- **📈 SPC Charts**: Individual charts, moving range charts, capability charts, and extrapolation plots
- **🌍 Internationalization**: Multi-language support (Catalan, English, Polish)
- **🧪 Comprehensive Testing**: Full test coverage for all major components
- **📅 Automatic Backup**: Scheduled 24-hour data synchronization from GOMPC network to database

### 🗃️ Database Editor Features

The integrated Database Editor provides comprehensive database management capabilities:

#### **Visual Table Management**
- **Table Selection**: Dropdown selector for all available database tables
- **Real-time Data Loading**: Background loading with progress indicators
- **Column Sorting**: Click headers to sort data by any column
- **Row Limits**: Configurable row limits (10-10,000) or show all records

#### **Data Editing**
- **In-place Editing**: Click any cell to edit data directly
- **Visual Change Tracking**: Modified rows highlighted in yellow
- **Batch Save**: Save multiple changes in a single transaction
- **Add/Delete Rows**: Insert new records or remove selected rows
- **Undo Support**: Track and revert unsaved changes

#### **Advanced Operations**
- **Custom SQL Queries**: Execute SELECT, UPDATE, INSERT, DELETE queries
- **Data Export**: Export table data to CSV format
- **Table Statistics**: Real-time row and column counts
- **Error Handling**: Comprehensive error reporting and recovery

#### **Professional Interface**
- **Responsive Design**: Resizable panels and columns
- **Progress Tracking**: Visual feedback for long-running operations
- **Information Panel**: Detailed operation logs and table information
- **Keyboard Shortcuts**: Standard editing shortcuts supported

#### **Safety Features**
- **Confirmation Dialogs**: Confirm destructive operations
- **Transaction Safety**: Automatic rollback on errors
- **Connection Management**: Automatic connection handling
- **Unsaved Changes Warning**: Prompt before closing with unsaved data

To access the Database Editor, click the **"Edit Data"** button in the main application's right panel.

---

## Installation

1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd PythonTecnica_SOME
   ```
2. Create a virtual environment (recommended):
   ```sh
   python -m venv env
   .\env\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

---

## Usage

### Running the Application

Launch the GUI application:

```sh
python main_app.py
```

### Core Functionalities

- **📊 Data Processing:**
  Use the GUI or run scripts directly to process Excel quotation files. The `pipeline_manager.py` orchestrates the entire workflow from Excel reading to data transformation. Processed data is saved in structured formats for database upload.

- **🗄️ Database Operations:**
  Upload filtered and transformed data to PostgreSQL database using the GUI's database update functionality. The system handles column mappings, data validation, and PDF storage automatically.

- **📱 GUI Features:**
  - **PDF Viewer**: Toggle between text and PDF views using the "View Drawing" button
  - **Data Export**: Export dimensional and capability studies directly to your Downloads folder
  - **Statistical Analysis**: Generate SPC charts, capability studies, and dimensional reports
  - **Project Search**: Quick search functionality for project references and data

- **📈 Statistical Analysis:**
  Generate comprehensive reports including:
  - Capability studies with Cp, Cpk, Pp, Ppk indices
  - SPC control charts (Individual, Moving Range)
  - Normality analysis and extrapolation charts
  - Dimensional analysis reports

- **🔄 Data Export:**
  Export analysis results as Excel or CSV files with automatic Downloads folder detection. Supports multiple sheets and cross-platform compatibility.

### Testing

Run all tests:

```sh
python -m unittest discover tests
```

Run specific component tests:

```sh
python test_orchestrator.py
python test_spc_charts.py
python test_data_transformer.py
```

---

## Adding New Modules

- Place new processing modules in `src/`.
- Add new tests in `tests/`.
- Document new features in `docs/`.
- Add new assets in `assets/icons/` or `assets/images/` as appropriate.

---

## Folder/Module Relations

- All data flows from `src/` modules to the `data/` folder.
- Tests import from `src/`.
- Documentation in `docs/` references both `src/` and `data/`.
- Assets are referenced by both UI code and documentation.

---

## Requirements

See `requirements.txt` for all dependencies. Each is commented for clarity.

---

## Contributing

- Follow the modular structure.
- Write tests for new features.
- Update documentation as needed.

---

## License

[Specify your license here]

---

## Contact

[Add contact or maintainer info here]

---

## Notes

- All generated files are saved in `data/`.
- The project is designed for easy extension and professional maintainability.
- For any questions, see `docs/` or contact the maintainer.
