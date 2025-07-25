# PythonTecnica_SOME

## Overview

PythonTecnica_SOME is a modular Python application for processing technical and business data from CSV and Excel files, generating reports, and supporting database integration. It is designed for professional, maintainable, and extensible use in technical and business environments.

---

## Project Structure

```
PythonTecnica_SOME/
│
├── src/                              # Main source code (all modules)
│   ├── __init__.py
│   │
│   ├── data_processing/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── excel_reader.py       # Test success!
│   │   ├── __init__.py
│   │   ├── data_processor.py         # Test success!
│   │   ├── data_transformer.py       # Test success!
│   │   └── pipeline_manager.py       # Test success!
│   │
│   ├── database/
│   │   ├── database_connection.py    # Test success!
│   │   └── database_uploader.py      # Test success!
│   │
│   ├── exceptions/
│   │   ├── __init__.py          
│   │   ├── transformation_errors.py  # Test success!
│   │   └── sample_errors.py          # Test success!
│   │
│   │── gui/
│   │    ├── __init__.py
│   │    ├── main_window.py               # Main application window
│   │    ├── logging_config.py            # Logging configuration for GUI
│   │    ├── widgets/                     # Custom UI widgets
│   │    │   ├── __init__.py
│   │    │   ├── element_input_widget.py        # Test success!
│   │    │   ├── buttons.py                     # Test success!
│   │    │   ├── inputs.py                      # Test success!
│   │    ├── panels/
│   │    │   ├── __init__.py
│   │    │   ├── header.py                      # Test success!
│   │    │   ├── left_panel.py                  # Test success!
│   │    │   ├── center_panel.py                # Test success!
│   │    │   ├── right_panel.py                 # Test success!
│   │    │   └── status_bar.py                  # Test success!
│   │    ├── workers/                      
│   │    │   └── capability_study_worker.py     # Test success!
│   │    ├── window/                      
│   │    │   ├── __init__.py
│   │    │   └── spc_chart_window.py            # Test success!
│   │    └── utils/
│   │        ├── chart_utils.py             # Chart utilities
│   │        ├── element_input_styles.py    # Styling utilities
│   │        └── styles.py                  # Styling utilities
│   │
│   ├── models/
│   │   │── plotting/
│   │   │   │── __init__.py  
│   │   │   │── logging_config.py               # Test success!
│   │   │   │── spc_charts_manager.py           # Test success!
│   │   │   │── base_chart.py                   # Test success!
│   │   │   │── spc_data_loader.py              # Test success!
│   │   │   │── capability_chart.py             # Test success!
│   │   │   │── normality_plot.py               # Test success!
│   │   │   │── extrapolation_chart.py          # Test success!
│   │   │   │── i_chart.py                      # Test success!
│   │   │   └── mr_chart.py                     # Test success!
│   │   │  
│   │   ├── capability/               # Statistical capability analysis
│   │   │   ├── __init__.py
│   │   │   ├── logging_config.py       
│   │   │   ├── sample_data_manager.py          # Test success!
│   │   │   ├── capability_analyzer.py          # Test success!
│   │   │   ├── capability_study_manager.py     # Test success!
│   │   │   └── extrapolation_manager.py        # Test success!
│   │   │ 
│   │   ├── dimensional/              # Dimensional analysis
│   │   │   ├── __init__.py
│   │   │   ├── gdt_interpreter.py              # Developing
│   │   │   ├── measurement_validator.py        # Developing
│   │   │   ├── dimensional_result.py           # Developing
│   │   │   └── dimensional_analyzer.py         # Developing
│   │   └── __init__.py
│   │
│   ├── services/
│   │    │── __init__.py 
│   │    │── dimensional_service.py             # Test success! <-
│   │    │── spc_chart_service.py               # Test success! <-
│   │    │── capacity_study_service.py          # Test success! <-
│   │    │── data_export_service.py             # Test success! <-
│   │    │── pdf_service.py                     # Test success! <-
│   │    │── data_processing_orchestrator.py    # Test success! <- to clean...
│   │    └── database_update.py                 # Test success! <- to clean...
│   │
│   └── utils/
│       └──  __init__.py
│
├── data/
│   │   │── pending/
│   │   └── processed/
│   │ 
│   ├── processed/
│   │   │── datasheets/
│   │   │── export/
│   │   └── reports/
│   │       │── dimensional/
│   │       └── statistics/
│   │
│   └── temp/
│       │── excel_processing/
│       └── report_generation/
│
├── config/
│   ├── database/
│   │   └── db_config.json            # Database connection configuration
│   ├── column_mappings/
│   │   ├── columns_to_drop.json      # Column filtering configuration
│   │   └── table_mappings.json       # Database table mappings
│   └── config.ini                    # Main application configuration
│
├── tests/                       # Unit and integration tests
│   ├── test_orchestrator.py          # Test success!
│   ├── test_spc_charts.py            # Test success!
│   ├── test_spc_manager.py           # Test success!
│   ├── test_data_uploader.py         # Test success!
│   ├── test_kop_processing.py        # Test success!
│   ├── test_data_transformer.py      # Test success!
│   ├── test_data_uploader.py         # Test success!
│   ├── test_dimensional_analyzer.py  # Test success!
│   ├── test_dimensional_export.py  # Test success!
│   └── test_excel_processing.py      # Test success!
│
├── docs/                        # Documentation
│   ├── capability/
│   │   ├── Estudi de capacitat.docx
│   │   └── Estudi de capacitat.pdf
│   ├── ddbb/
│   │   ├── Construcció_BBDD.docx
│   │   ├── Construcció_BBDD.pdf
│   │   ├── DDBB Class diagram.pdf
│   │   ├── DDBB Class diagram.svg
│   │   └── Diagrama de classes.drawio
│   └── dimensional/
│       ├── Dimensional.docx
│       └── Dimensional.pdf
│
├── assets/                           # Static assets
│   ├── images/
│   │   └── gui/
│   │       └── logo_some.png         # Application logo
│   └── templates/
│       ├── 6555945_003.pdf          # PDF template
│       └── qa/
│           └── Example QA - Report ZF.xls    # QA report template
│
├── i18n/                             # Internationalization
│   ├── ca.json                       # Catalan translations
│   ├── en.json                       # English translations
│   └── pl.json                       # Polish translations
│
├── logs/                             # Application logs
│   ├── gui.log                       # GUI application logs
│   └── db_operations.log             # Database operation logs
│
│
├── main_app.py                       # Application entry point
├── Configuració_Set_Up.txt           # Setup configuration notes
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
└── .gitignore                        # Git ignore configuration
```

---

## How It Works

- **src/** contains all logic, processing, and UI code. Each module is responsible for a specific part of the workflow:
  - **data_processing/**: Excel file processing, data transformation, and pipeline management
  - **database/**: PostgreSQL connection and data upload with PDF handling capabilities
  - **gui/**: Complete PyQt5 GUI application with PDF viewer, data export, and interactive panels
  - **models/**: Statistical analysis including capability studies, dimensional analysis, and SPC plotting
  - **services/**: Application orchestration, database updates, and data export to Downloads folder
- **config/** contains all configuration files for database connections, column mappings, and application settings
- **assets/** contains static files including the application logo, PDF templates, and QA report examples
- **i18n/** provides internationalization support for Catalan, English, and Polish languages
- **logs/** stores application logs for debugging and monitoring
- **tests/** contains comprehensive test suites for all major components
- **docs/** contains project documentation including capability studies, database design, and dimensional analysis guides

## Key Features

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
