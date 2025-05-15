# Mapatge de taules i les seves columnes corresponents
table_mappings = {
    'eines':                    ['nom_matriu', 'num_picades', 'volum_anual', 'volum_projecte', 'cavitats', 'datainici', 'datafinal', 'responsable', 'matricer'],
    'escandalloferta':          ['num_escandall', 'preuvenda'],
    'material':                 ['id_material', 'dimensiox', 'dimensioy', 'dimensioz', 'proveidor', 'pes', 'preu'],
    'tipus':                    ['id_tipus', 'descripcio'],
    'peça':                     ['id_referencia_client', 'nom_client', 'planta', 'nom_projecte', 'facturacio', 'quantitats', 'descripcio', 'costos', 'pes', 'embalatges', 'recobriments', 'termics', 'id_tipus'],
    'planol':                   ['num_planol', 'id_referencia_client'],     #'imatge'
    'infoproduccio':            ['id_referencia_some', 'id_referencia_client', 'id_matriu', 'id_material'], 
    'oferta':                   ['num_oferta', 'cicles', 'num_processos', 'descripcio', 'nomclient', 'mailclient', 'telefclient', 'id_referencia_client', 'num_escandall'], 
    'lifetime':                 ['num_oferta', 'datainici', 'datafinal', 'dataentregamatriu']                
}

# Mapatge de columnes del DataFrame a columnes de la base de dades:
col_map = {
    'eines': {
        '1 - Nº Matriu:':               'nom_matriu',
        '4 - Tool Lifetime':            'num_picades',
        '5 - Volum Anual:':             'volum_anual',
        '6 - Volum total Projecte:':    'volum_projecte',
        '8 - Cavitats:':                'cavitats',
        'S.O.P. CLIENT':                'datainici',
        'E.O.P. CLIENT':                'datafinal',
        '14 - Responsable Projecte:':   'responsable',
        '9 - Matricer:':                'matricer',
    },
    'escandalloferta': {
        '13 - Nº Expedient:':                       'num_escandall',
        '17 - Preu Peça (Oferta a Client)':         'preuvenda'
    },
    'material': {
        '1 - Descripció material:':     'id_material',
        'BANDA':                        'dimensiox',
        'PAS':                          'dimensioy',
        'GRUIX':                        'dimensioz',
        '3 - Proveïdor:':               'proveidor',
        '7 - Pes estimat del Rull:':    'pes',
        '4 - Preu actualitzat:':        'preu'
    },
    'tipus': {
        '12 - Jerarquía:':              'id_tipus',
        '6 - Descripció actualitzada:': 'descripcio'
    },
    'peça': {
        #'df_col2':                                 'id_referencia_client',
        '1 - Client:':                              'nom_client',
        '2 - Tipus:  SQB / KSW / MIXTE:':           'planta',
        '11 - Projecte:':                           'nom_projecte',
        '3 - Tipus Facturació: A / B / C:':         'facturacio',
        'LOT PRODUCCIÓ INFORMAT A CLIENT':          'quantitats',
        '6 - Descripció actualitzada:':             'descripcio',
        '12 - Pes Brut:':                           'pes_brut',
        '13 - Pes Net:':                            'pes',
        '16 - Cost Peça (Intern SOME)':             'costos',
        '17 - Preu Peça (Oferta a Client)':         'preu',
        'Caixa:':                                   'embalatges',
        '* Descripció complerta del tractament 2:': 'recobriments',
        '* Descripció complerta del tractament 1:': 'termics',
        '12 - Jerarquía:':                          'id_tipus'
    },
    'planol': {
        '15 - Plànol actualitzat':          'num_planol',
        '13 - Nº Expedient:':               'id_referencia_client',
        #'df_col3': 'imatge'
    },
    'infoproduccio': {
        #'df_col1':                 'id_referencia_some',
        #'df_col2':                 'id_referencia_client',
        '1 - Nº Matriu:':           'id_matriu',
        '1 - Descripció material:': 'id_material'
    },
    'oferta': {
        '13 - Nº Expedient:':           'num_oferta',
        'CPM':                          'cicles',
        #'df_col3':              'num_processos',
        #'df_col4':              'descripcio',
        '1 - Client:':                  'nomclient',
        #'df_col5':              'mailclient'
        #'df_col6':              'telefclient',
        #'df_col2':                     'id_referencia_client',
        '13 - Nº Expedient:':           'num_escandall'
    },
    'lifetime': {
        '13 - Nº Expedient:':                       'num_oferta',
        'S.O.P. CLIENT':                            'datainici',
        'E.O.P. CLIENT':                            'datafinal',
        'DATA KOP':                                 'data_kop',
        'DATA ENVIAMENT PSA':                       'data_psa',
        'DATA ENTREGA PLANNING MATRIU':             'data_planning_mat',
        'DATA ENTREGA LAYOUT MATRIU':               'data_layout_mat',
        'DATA FOTs MATRICER':                       'data_fots_mat',
        'DATA PROBA A SOME MATRICER (PPAP)':        'data_pmat_some',       
        'DATA PRIMERES MOSTRES  F.O.T A CLIENT':    'data_fot_client',
        'DATA ENTREGA PECES PPAP A CLIENT':         'data_ent_pcs_ppap',
        '10 - Data entrega matriu:':                'dataentregamatriu'
    }
}

# Taules sense dades del KOP:
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

# Columnes a eliminar del CSV obtingudes del KOP:
col_elim = [r'2 - Mides (BANDA x PAS x GRUIX):', 
            r'Dades necessàries per estructurar una Matèria prima',
            r'Dades necessàries per estructurar una Matriu',
            r'Dades necessàries per estructurar un Component / Material Aux.',
            r'Dades necessàries per estructurar una peça / conjunt',
            r'COMPONENT ESTAMPACIÓ 1',
            r'1 - Descripció:',
            r'2 - Plànol:',
            r'COMPONENT ESTAMPACIÓ 2',
            r'1 - Descripció:.1',
            r'2 - Plànol:.1', 
            r'COMPONENT 1 COMPRA',
            r'COMPONENT 2 COMPRA',
            r'COMPONENT 3 COMPRA',
            r'DADES PER ESTRUCTURAR NOVES PECES', 
            r'10 - Tractaments:',
            r'11 - Embalatge:', 
            r'PD. La resta d\'informació que s\'entra ja l\'aconseguèix la persona que estructura.',
            r'ENTRADA DADES FORMULARIS',
            r'7 - SOP:',
            r'7 - SOP:.1',
            r'7 - SOP:.2',
            r'Nº MATRIU SOME',
            r'7 - Referència/es peça:',
            r'2 - SOP projecte',
            r'3 - EOP projecte',
            r'7 - Referència client:'
            r'11.1 - EUROPA',
            r'11.2 - OVERSEAS'
            #r'* cpm o (peces/hora) per CT'
            ]

# Columnes que contenen dates:
dates = ['10 - Data entrega matriu:', 
         'DATA ENTREGA PLANNING MATRIU', 
         'DATA ENTREGA LAYOUT MATRIU', 
         'DATA FOTs MATRICER', 
         'DATA PROBA A SOME MATRICER (PPAP)',
         'S.O.P. CLIENT',
         'E.O.P. CLIENT',
         'DATA KOP',
         'DATA ENVIAMENT PSA']  # Afegir aquí totes les columnes que saps que són dates

### Afegir a camps a 'eines':
    # 'Cost' = 'cost' <- Aquest ja hi és, però no trobo la dada al csv extret.
