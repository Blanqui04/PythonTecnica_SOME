# Mapatge de taules i les seves columnes corresponents
table_mappings = {
    'tipus':                    ['id_tipus', 'descripcio'],
    'client':                   ['id_client', 'nom_contacte'],
    'material':                 ['id_material', 'dimensiox', 'dimensioy', 'dimensioz', 'proveidor', 'pes', 'preu'],
    'eines':                    ['nom_matriu', 'num_picades', 'volum_anual', 'volum_projecte', 'cavitats', 'responsable', 'matricer'],
    'peca':                     ['id_referencia_client', 'nom_client', 'planta', 'nom_projecte', 'facturacio', 'quantitats', 'descripcio', 'costos', 'pes', 'id_tipus', 'id_embalatge', 'id_tractament'],
    'embalatge':                ['caixa_codi', 'regio', 'caixa_descripcio', 'tapa_altres', 'pallet_codi', 'pallet_descripcio', 'peces_caixa', 'caixes_pallet', 'id_referencia_client'],
    'tractament':               ['ordre', 'descripcio', 'proveidor', 'preu', 'id_referencia_client'],
    'planol':                   ['num_planol', 'id_referencia_client'],
    'infoproduccio':            ['id_referencia_some', 'id_referencia_client', 'id_matriu', 'id_material'],
    'escandalloferta':          ['num_escandall', 'preuvenda'],
    'escandallofertatecnics':   ['num_escandall', 'num_tecnic'],
    'oferta':                   ['num_oferta', 'num_processos', 'id_referencia_client', 'num_escandall', 'id_client'],
    'ctoferta':                 ['num_oferta', 'centretreball', 'oee', 'cicles'],
    'lifetime':                 ['num_oferta', 'datainici', 'datafinal', 'dataentregamatriu'],
    'element':                  ['id_referencia_client', 'id_element', 'tolerancia_superior', 'tolerancia_inferior', 'descripcio', 'valor_nominal', 'classe', 'lim_sup', 'lim_inf', 'propietat']
}

## ------------------ % Altres taules de la base de dades que no s'omplena partir del KOP de comercial % ----------------------------##
# 'mesuresqualitat':    ['id_referencia_some', 'id_referencia_client', 'id_element', 'valor', 'ok']
# 'tecnics':            ['num_tecnic', 'nom', 'cognom1', 'cognom2', telefon', 'email']
# 'ct':                 ['centretreball', 'descripcio']
# 'tipus':              ['id_tipus', 'descripcio']
# 'client':             ['id_client', 'nom_contacte', 'email_contacte']
## ------------------------------------------------------------------------------------------------------------------------------------

# Columnes a eliminar del CSV obtingudes del KOP:
col_elim = [r'7 - SOP:',
            r'7 - SOP:.1',
            r'7 - SOP:.2',
            r'2 - Plànol:',
            r'2 - Plànol:.1',
            r'11.1 - EUROPA',
            r'Nº MATRIU SOME',
            r'1 - Descripció:',
            r'11.2 - OVERSEAS',
            r'11 - Embalatge:', 
            r'2 - SOP projecte',
            r'3 - EOP projecte',
            r'1 - Descripció:.1',
            r'10 - Tractaments:',
            r'COMPONENT 1 COMPRA',
            r'COMPONENT 2 COMPRA',
            r'COMPONENT 3 COMPRA',
            r'COMPONENT ESTAMPACIÓ 1',
            r'COMPONENT ESTAMPACIÓ 2',
            r'7 - Referència client:',
            r'7 - Referència/es peça:',
            r'ENTRADA DADES FORMULARIS',
            r'DADES PER ESTRUCTURAR NOVES PECES',
            r'Dades necessàries per estructurar una Matriu',
            r'Dades necessàries per estructurar una Matèria prima',
            r'Dades necessàries per estructurar una peça / conjunt',
            r'Dades necessàries per estructurar un Component / Material Aux.',
            r'PD. La resta d\'informació que s\'entra ja l\'aconseguèix la persona que estructura.'
            ]
