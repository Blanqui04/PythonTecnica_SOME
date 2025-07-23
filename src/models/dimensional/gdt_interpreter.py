# src/models/dimensional/gdt_interpreter.py

def parse_gdt_flags(description: str) -> dict:
    desc = description.upper()
    return {
        "MIN": "MIN" in desc,
        "MAX": "MAX" in desc,
        "DATUM": "DATUM" in desc,
        "PROFILE": "PROFILE" in desc,
        "FLATNESS": "FLATNESS" in desc,
        "PARALLELISM": "PARALLELISM" in desc,
        "PERPENDICULARITY": "PERPENDICULARITY" in desc,
        "CIRCULARITY": "CIRCULARITY" in desc,
        "CYLINDRICITY": "CYLINDRICITY" in desc,
        "RUNOUT": "RUNOUT" in desc,
        "CONCENTRICITY": "CONCENTRICITY" in desc,
        "SYMMETRY": "SYMMETRY" in desc,
        "MMC": "MMC" in desc,
        "LMC": "LMC" in desc,
        # Add more as needed
    }
