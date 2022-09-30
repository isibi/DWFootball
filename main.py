from flashscore import Flashscore
from conexion_BBDD import Conexion_BBDD
from datetime import datetime
import scrap_statistics

# instanciamos las clases que vamos a usar
flashscore = Flashscore()
conexion = Conexion_BBDD()
conexion = conexion.conexion()
cursor = conexion.cursor()
start = datetime.now()

# Competiciones que queremos obtener información
#dict_all = {'francia': {'copa-de-francia': ['2018-2019']}}

# Seleccionamos el tipo de Scrap que vamos hacer
modo = "resultados"  # ("resultados" o "calendario") resulatods scrap el pasado. calendario los proximos partidos
# ("competition" o "jornada") competicion  scrap toda la competicion. jornada ultimos partidos
tipo_scrap = "competition"
year = ""  # Si esta vacío obtendra el año actual
n_partidos = 10  # Solo para tipo_scrap = jornada. Numero de partidos por jornada
stage_area = "StageArea.Matches2"  # ("StageArea.Calendario" / "StageArea.Matches" o "StageArea.Matches2")
guardar_escudo = "yes"  # {'yes' o 'no'} Guarda el escudo de los equipos durante el scrp

if modo == "resultados":
    s_url = '/resultados/'
    # Fichero con todos los paises con sus competiciones y años
    with open('D:/Business Intelligence/DWFutbol/scrap_dict_custom.txt', 'r', encoding='utf-8') as dict_file:
        dict_text = dict_file.read()
    dict_all = eval(dict_text)
else:
    s_url = '/partidos/'
    # Fichero con todos los paises con sus competiciones y años
    with open('D:/Business Intelligence/DWFutbol/scrap_dict_calendario.txt', 'r', encoding='utf-8') as dict_file:
        dict_text = dict_file.read()
    dict_all = eval(dict_text)

for country, competitions in dict_all.items():
    for competition, years in competitions.items():
        for year in years:
            if year == str(datetime.now().year) + '-' + str(datetime.now().year + 1):
                year = ''
            # list_matches = ['fqL7WBrH']  # PROBAR UN PARTIDO SOLO
            list_matches = flashscore.scrap_competition(country, competition, year, s_url, tipo_scrap, n_partidos)
            scrap_statistics.begin_scrap(list_matches, modo, flashscore, year, conexion, cursor, country
                                         , competition, stage_area, guardar_escudo)
            runtime = str(datetime.now() - start)
            print('[ ' + country.upper() + ' ' + competition.upper() + ' ' + str(year) + ' FINISHED: ' + runtime + ']')
