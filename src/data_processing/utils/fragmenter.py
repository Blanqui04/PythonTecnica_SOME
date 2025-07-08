def fragment_dataframe(df):
    # Fragmentem per valor únic d'una columna com "PartID" (exemple)
    fragments = {}
    if 'PartID' in df.columns:
        for part_id, group in df.groupby('PartID'):
            fragments[str(part_id)] = group
    else:
        # Tot en un únic fragment si no hi ha PartID
        fragments["default"] = df
    return fragments
