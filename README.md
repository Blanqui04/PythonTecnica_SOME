# PythonTecnica_SOME

## Overview

PythonTecnica_SOME is a modular Python application for processing technical and business data from CSV and Excel files, generating reports, and supporting database integration. It is designed for professional, maintainable, and extensible use in technical and business environments.

---

## Project Structure

```
PythonTecnica_SOME/
│
├── src/                # Main source code (all modules)
│   ├── blueprints/
│   │   │── blueprint_client.py     # Empty rn
│   │   └── blueprint_manager.py    # Empty rn
│   ├── data_processing/
│   │   │── utils/
│   │   │   │── __init__.py
│   │   │   └── excel_reader.py     # Test succes!
│   │   │── __init__.py
│   │   │── data_processor.py       # Test success!
│   │   │── data_transformer.py     # Test success!
│   │   └── pipeline_manager.py     # Okay for now - yet to test alltogether
│   ├── database/
│   │   │── database_connection.py  # Test success!
│   │   └── database_uploader.py    # Test to reviw data uploaded, None, NaN, etc.
│   ├── exceptions/
│   │   │── transformation_errors.py  # Test success!
│   │   └──  __init__.py
│   ├── gui/
│   │   └──  __init__.py
│   ├── models/
│   │   │──statistics/
│   │   │   │── __init__.py
│   │   │   └── capability.py         # Empty rn
│   │   │── dimensional/
│   │   │   │── __init__.py
│   │   │   └── dimenisonal.py        # Empty rn
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
│   │   └── db_config.json        # Tests OK
│   ├── column_mappings/
│   │   │── columns_to_drop.json  # Tests OK
│   │   └── table_mappings.json   # Tests OK
│   └── config.ini
│
├── tests/                        # Unit and integration tests
│   ├── tests_services/
│   ├── tests_utils/
│   ├── test_data_uploader.py     # Test success!
│   ├── test_data_transformer.py  # Test success!
│   └── test_excel_processing.py  # Test success!
│
├── docs/              # Documentation (usage, API, developer notes)
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
├── assets/                       # Static assets (icons, images)
│   ├── README.md
│   ├── icons/
│   │   └── README.md
│   ├── sql/
│   │   └── README.md
│   ├── templates/
│   │   └── Example QA - Report ZF.xslx
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
├── test_data_uploader.py     # Test NOT OK, review data uploaded: None, NaN, etc.
├── test_kop_processing.py    # Test succes!
├── test_data_transformer.py  # Test success!
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
  Use the `process_csv_data` function in `src/csv_func.py` to process CSV files. All outputs will be saved in the `data/` folder.

- **UI Integration:**
  If using a UI, launch the UI module in `src/dbb_ui.py` (requires PyQt5 or PySide2, not included by default).

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
