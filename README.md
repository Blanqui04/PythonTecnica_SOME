# PythonTecnica_SOME

## Overview

PythonTecnica_SOME is a modular Python application for processing technical and business data from CSV and Excel files, generating reports, and supporting database integration. It is designed for professional, maintainable, and extensible use in technical and business environments.

---

## Project Structure

```
PythonTecnica_SOME/
│
├── src/                              # Main source code (all modules)
│   ├── blueprints/
│   │   │── blueprint_client.py       # Empty rn <- to handle different QA from clients
│   │   └── blueprint_manager.py      # Empty rn <- to manage the data from the drawing, qa, etc. to the ddbb.
│   ├── data_processing/
│   │   │── utils/
│   │   │   │── __init__.py
│   │   │   └── excel_reader.py       # Test succes!
│   │   │── __init__.py
│   │   │── data_processor.py         # Test success!
│   │   │── data_transformer.py       # Test success!
│   │   └── pipeline_manager.py       # Test success!
│   ├── database/
│   │   │── database_connection.py    # Test success!
│   │   └── database_uploader.py      # Test success! - to reviw data uploaded, None, NaN, etc.
│   ├── exceptions/
│   │   │── sample_errors.py          # Test success!
│   │   │── transformation_errors.py  # Test success!
│   │   └──  __init__.py
│   ├── gui/
│   │   └──  __init__.py
│   ├── models/
│   │   │── capability/
│   │   │   │── __init__.py
│   │   │   │── capability_plotter.py        # Working on it
│   │   │   │── sample_data_manager.py       # Test success!
│   │   │   │── capability_analyzer.py       # Test success!
│   │   │   │── capability_plotter.py        # Test success!
│   │   │   └── extrapolation_manager.py     # Test success!
│   │   │── dimensional/
│   │   │   │── __init__.py
│   │   │   └── dimenisonal_analyzer.py        # Empty rn
│   │   └──  __init__.py
│   ├── services/
│   │   │── backup_manager.py         # Empty rn
│   │   │── file_monitor.py           # Empty rn
│   │   │── session_manager.py        # Empty rn
│   │   └── notification_manager.py   # Empty rn
│   └── utils/
│       └──  __init__.py
│
├── data/
│   │   │── pending/
│   │   └── processed/
│   ├── processed/
│   │   │── datasheets/
│   │   │── export/
│   │   └── reports/
│   │       │── dimensional/
│   │       └── statistics/
│   └── temp/
│       │── excel_processing/
│       └── report_generation/
│
├── config/
│   ├── database/
│   │   └── db_config.json
│   ├── column_mappings/
│   │   │── columns_to_drop.json
│   │   └── table_mappings.json
│   └── config.ini
│
├── tests/                        # Unit and integration tests
│   ├── tests_services/
│   ├── tests_utils/
│   ├── test_data_uploader.py     # Test success!
│   ├── test_data_transformer.py  # Test success!
│   └── test_excel_processing.py  # Test success!
│
├── docs/                         # Documentation (usage, API, developer notes)
│   ├── capability/
│   │   │── Estudi de capacitat.docx
│   │   └── Estudi de capacitat.pdf
│   ├── ddbb/
│   │   │── Construcció_BBDD.docx
│   │   │── Construcció_BBDD.pdf
│   │   │── DDBB Class diagram.pdf
│   │   │── DDBB Class diagram.svg
│   │   └── Diagrama de classes.drawio
│   └── dimensional/
│       │── Dimensional.docx
│       └── Dimensional.pdf
│
├── assets/                         # Static assets (icons, images)
│   ├── README.md
│   ├── icons/
│   │   └── README.md
│   ├── templates/
│   │   └── qa
│   │       └── Example QA - Report ZF.xslx
│   └── images/
│       │── gui/
│       │    └── dimensional/
│       └── README.md
│
├── i18n/
│   ├── ca.json
│   ├── en.json
│   └── pl.json
│
├── logs/
│
├── test_capability_manager.py      # Test success!
├── test_data_uploader.py           # Test success! Review data uploaded (integers, floats, misisng...)
├── test_kop_processing.py          # Test success!
├── test_data_transformer.py        # Test success!
│
├── main_app.py
├── Configuració Set-Up.txt
├── requirements.txt          # Python dependencies with comments
├── README.md                 # Project overview and instructions
└── ...                       # Other (now non existant files)
```

---

## How It Works

- **src/** contains all logic, processing, and UI code. Each module is responsible for a specific part of the workflow (CSV processing, database connection, UI, etc).
- **data/** is the only place where input and output files are stored. This keeps the project root clean and makes backups and deployments easier.
- **tests/** contains all test code. Use `pytest` or `unittest` to run tests.
- **docs/** contains all documentation, including API docs, usage guides, and developer notes.
- **assets/** contains all static files (icons, images) for UI and documentation.

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

- **Processing CSV Data:**
  Use the `data_processor.py` handled by the `pipeline_manager.py` script and `data_transformer.py` in `src/data_processing/` to process read the quotation offer, excel files, and filter the necessary data. All outputs will be saved in the `data/processed/datasheets`, `data/processed/exports` and `data/temp/excel_processing` folders.

- **Uploading data to the database:**
   The filtered data read from the quotation offer in `data/processed/exports` will be read by the `database_uploader.py`, which using the connection from `database_connection.py` and the parameters of the database `config/database/` in file `db_config.json` will be able to connect and upload the filtered data to the database.

- **UI Integration:**
  If using a UI, launch the UI module in `src/dbb_ui.py` (requires PyQt5 or PySide2, not included by default).

- **SPC:**
  Using the buttons and features from the GUI, the user will be able to perform statistical capability analysis, dimenisonal reports, or search quickly for info of the part.

- **Testing:**
  Run all tests with:
  ```sh
  python -m unittest discover tests
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
