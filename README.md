# PythonTecnica_SOME

## Overview

PythonTecnica_SOME is a modular Python application for processing technical and business data from CSV and Excel files, generating reports, and supporting database integration. It is designed for professional, maintainable, and extensible use in technical and business environments.

---

## Project Structure

```
PythonTecnica_SOME/
│
├── src/                # Main source code (all modules)
│   ├── __init__.py
│   ├── csv_func.py
│   ├── connexio_bbdd.py
│   ├── dbb_ui.py
│   ├── dim.py
│   ├── e_cap.py
│   ├── e_cap_plots.py
│   ├── e_cap_report.py
│   ├── e_cap_ZF.py
│   ├── from_sql.py
│   ├── kop_csv.py
│   ├── lectura_qa_zf.py
│   ├── maps_columnes.py
│   ├── mmc calc.py
│   ├── to_sql.py
│   └── translation_dict.py
│
├── data/               # All input/output data (CSV, Excel, generated files)
│   └── README.md
│
├── tests/              # Unit and integration tests
│   ├── __init__.py
│   └── test_csv_func.py
│
├── docs/               # Documentation (usage, API, developer notes)
│   └── README.md
│
├── assets/             # Static assets (icons, images)
│   ├── README.md
│   ├── icons/
│   │   └── README.md
│   └── images/
│       └── README.md
│
├── requirements.txt    # Python dependencies with comments
├── README.md           # Project overview and instructions
└── ...                 # Other legacy or config files
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
