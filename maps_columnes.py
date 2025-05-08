# Mapatge de taules i les seves columnes corresponents
table_mappings = {
    'eines':                    ['nom_matriu', 'num_picades', 'volum_anual', 'volum_projecte', 'cavitats', 'datainici', 'datafinal', 'responsable'],
    'escandalloferta':          ['num_escandall', 'cost'],
    'escandallofertatecnics':   ['num_escandall', 'num_tecnic'],
    'infoproduccio':            ['id_referencia_some', 'id_referencia_client', 'id_matriu', 'id_material'],       
    'lifetime':                 ['num_oferta', 'datainici', 'datafinal'], 
    'material':                 ['id_material', 'dimensiox', 'dimensioy', 'dimensioz', 'proveidor', 'pes', 'preu'],
    'oferta':                   ['num_oferta', 'cicles', 'num_processos', 'descripcio', 'nomclient', 'telefclient', 'id_referencia_client', 'num_escandall'], 
    'peþa':                     ['id_referencia_client', 'nom_client', 'planta', 'nom_projecte', 'facturacio', 'facturacio', 'descripcio', 'costos', 'pes', 'embalatges', 'recobriments', 'termics', 'id_tipus'],
    'planol':                   ['num_planol', 'id_referencia_client', 'imatge'],             
    'tipus':                    ['id_tipus', 'descripcio'], 
}

# Mapatge de columnes del DataFrame a columnes de la base de dades
column_mapping = {
    'eines': {
        '1 - Nº Matriu:': 'nom_matriu',
        '4 - Tool Lifetime': 'num_picades',
        '5 - Volum Anual:': 'volum_anual',
        '6 - Volum total Projecte:': 'volum_projecte',
        '8 - Cavitats:': 'cavitats',
        '2 - SOP projecte': 'datainici',
        '3 - EOP projecte': 'datafinal',
        '14 - Responsable Projecte:': 'responsable',
    },
    'escandalloferta': {
        'df_col1': 'num_escandall',
        'df_col2': 'cost'
    },
    'escandallofertatecnics': {
        'df_col1': 'num_escandall',
        'df_col2': 'num_tecnic'
    },
    'infoproduccio': {
        'df_col1': 'id_referencia_some',
        'df_col2': 'id_referencia_client',
        'df_col3': 'id_matriu',
        'df_col4': 'id_material'
    },
    'lifetime': {
        '13 - Nº Expedient:': 'num_oferta',
        '2 - SOP projecte': 'datainici',
        '3 - EOP projecte': 'datafinal',
        '10 - Data entrega matriu:': 'dataentrega_matriu',
    },
    'material': {
        '1 - Descripció material:': 'id_material',
        'BANDA': 'dimensiox',
        'PAS': 'dimensioy',
        'GRUIX': 'dimensioz',
        'df_col5': 'proveidor',
        'df_col6': 'pes',
        'df_col7': 'preu'
    },
    'oferta': {
        '13 - Nº Expedient:': 'num_oferta',
        'df_col2': 'cicles',
        'df_col3': 'num_processos',
        'df_col4': 'descripcio',
        'df_col5': 'nomclient',
        'df_col6': 'telefclient',
        'df_col7': 'id_referencia_client',
        'df_col8': 'num_escandall'
    },
    'peþa': {
        'df_col1': 'id_referencia_client',
        'df_col2': 'nom_client',
        'df_col3': 'planta',
        'df_col4': 'nom_projecte',
        'df_col5': 'facturacio',
        'df_col6': 'facturacio',
        'df_col7': 'descripcio',
        'df_col8': 'costos',
        'df_col9': 'pes',
        'df_col10': 'embalatges',
        'df_col11': 'recobriments',
        'df_col12': 'termics',
        'df_col13': 'id_tipus'
    },
    'planol': {
        'df_col1': 'num_planol',
        'df_col2': 'id_referencia_client',
        'df_col3': 'imatge'
    },
    'tipus': {
        '12 - Jerarquía:': 'id_tipus',
        '6 - Descripció actualitzada:': 'descripcio'
    }
}

# Taules sense dades del KOP
altres_taules = {
    'tecnics': {
        'df_col1': 'num_tecnic',
        'df_col2': 'nom',
        'df_col3': 'cognom1',
        'df_col4': 'cognom2',
        'df_col5': 'telefon',
        'df_col6': 'email'
    },
    'mesuresqualitat': {
        'df_col1': 'id_referencia_some',
        'df_col2': 'id_element',
        'df_col3': 'valor',
        'df_col4': 'ok'
    },
    'element': {
        'df_col4': 'id_referencia_client',
        'df_col5': 'id_element',
        'df_col6': 'tolerancia_superior',
        'df_col7': 'tolerancia_inferior',
        'df_col8': 'descripcio'
    },
    }


# Afegir a camps a 'eines':
# '9 - Matricer:': 'matricer',
# '7 - Referència/es peça:': 'pcs_matriu'
# 'Cost' = 'cost' <- Aquest ja hi és, però no trobo la dada al csv extret.
