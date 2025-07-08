# PythonTecnica_SOME

## Overview

PythonTecnica_SOME is a modular Python application for processing technical and business data from CSV and Excel files, generating reports, and supporting database integration. It is designed for professional, maintainable, and extensible use in technical and business environments.

---

## Project Structure

```
PythonTecnica_SOME/
│               # Main source code (all modules)
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
├── requirements.txt    # Python dependencies with comments
├── README.md           # Project overview and instructions
└── ...                 # Other legacy or config files
```

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

## Folder/Module Relations

## Requirements

See `requirements.txt` for all dependencies. Each is commented for clarity.

---

## Contributing

- Follow the modular structure.
- Write tests for new features.
- Update documentation as needed.

---

## License
---

## Contact
---

## Notes

