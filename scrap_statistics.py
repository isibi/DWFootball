import os
import urllib.request
import unicodedata
from selenium import webdriver
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

URL_CABECERA = "https://www.flashscore.es/partido/"
URL_RESUMEN = "/#/resumen-del-partido/resumen-del-partido"
URL_ESTADISCTICAS = "/#/resumen-del-partido/estadisticas-del-partido/"
URL_GITHUB = "https://github.com/isibi/DWFootball/blob/master/escudos/"
FOLDER_ESCUDOS = "D:/Business Intelligence/DWFutbol/Imagenes/Escudos Equipos/"
AMARILLA = 'card-ico yellowCard-ico'
SEGUNDA_AMARILLA = 'card-ico'
ROJA = 'card-ico redCard-ico'
GOL = 'soccer '
YEAR = str(datetime.now().year) + '-' + str(datetime.now().year + 1)


def begin_scrap(list_matches, modo, flashscore, year, conexion, cursor, country, competition, stage_area
                , guardar_escudo):
    driver = webdriver.Chrome()
    driver.minimize_window()
    count = 0
    for match_id in list_matches:
        percentage = str(round((count / len(list_matches)) * 100, 2)) + ' %]'
        print('[' + percentage + '\n')
        if modo == 'resultados':
            statistics(flashscore, driver, match_id, year, conexion, cursor, country, competition, stage_area
                       , guardar_escudo)
        else:
            calendario(match_id, driver, year, conexion, cursor, stage_area, country, competition, guardar_escudo)
        count = count + 1


def init_match(driver, match_id, year):
    match = {"Label_Match": match_id,
             "Season": year,
             "Competition": driver.find_element(By.CLASS_NAME, "tournamentHeader__country").text,
             "Date_Time": driver.find_element(By.CLASS_NAME, "duelParticipant__startTime").text,
             "Teams": [team.text for team in driver.find_elements(By.CLASS_NAME, "participant__overflow a")]
             }

    return match


def statistics(flashscore, driver, match_id, year, conexion, cursor, country, competition, stage_area, guardar_escudo):
    try:
        url = URL_CABECERA + match_id + URL_RESUMEN
        driver.get(url)
        # driver.implicitly_wait(1)
        try:
            tab_group = driver.find_element(By.CLASS_NAME, "tabs__detail--nav")
            tabs = [tab.text for tab in tab_group.find_elements(By.CLASS_NAME, "tabs__tab")]
            # Tiene Estadisticas completas ó Estadisticas en el Resumen
            if "ESTADÍSTICAS" in tabs:
                match_type = 'all'
                all_statistics(driver, match_id, year, conexion, cursor, country, stage_area, guardar_escudo)
            else:
                match_type = 'resume'
                only_resume(driver, match_id, year, country, conexion, cursor, stage_area, guardar_escudo)
        except NoSuchElementException:
            # No tiene estadisticas
            try:
                anulado = driver.find_element(By.CLASS_NAME, "detailScore__status").text
                if anulado == "APLAZADO" or anulado == "ANULADO" or anulado == 'WALKOVER':
                    match_type = 'incident'
                    incident_match(driver, match_id, year, country, conexion, cursor, stage_area, guardar_escudo,
                                   anulado)
                else:
                    match_type = 'score'
                    only_score(driver, match_id, year, conexion, country, cursor, stage_area, guardar_escudo)
            except NoSuchElementException:
                pass
    except Exception as e:
        flashscore.save_log_error(country, competition, year, match_id, match_type, e)


def all_statistics(driver, match_id, year, cnxn, cursor, country, stage_area, guardar_escudo):
    # Informacion General
    if year == "":
        year = YEAR
    match = init_match(driver, match_id, year)
    # Info
    try:
        match["Info"] = [item.text.replace("\n", "") for item in driver.find_elements(By.CLASS_NAME, "mi__item")]
    except NoSuchElementException:
        pass

    # Resultado
    try:
        score = driver.find_elements(By.CLASS_NAME, "section__title")
        match["Score_1T"] = score[0].text.replace('1ER TIEMPO\n', '').split('-')
        match["Score_2T"] = score[1].text.replace('2º TIEMPO\n', '').split('-')

        # Resumen
        goals = []
        cards = []
        # time.sleep(1)

        # Incidentes del partido
        home_away = ['home', 'away']
        for h_a in home_away:
            try:
                # Home Team
                incidents = driver.find_elements(By.CLASS_NAME, "smv__" + h_a + "Participant")
                for incident in incidents:
                    try:
                        svg = incident.find_element(By.TAG_NAME, "svg").get_attribute("class")
                        if svg == AMARILLA:
                            cards.append(incident.find_element(By.CLASS_NAME, "smv__incident").text.replace("\n", "")
                                         .replace("'", '-') + "-yellow")
                        elif svg == SEGUNDA_AMARILLA:
                            cards.append(incident.find_element(By.CLASS_NAME, "smv__incident").text.replace("\n", "")
                                         .replace("'", '-') + "-yellow")
                            cards.append(incident.find_element(By.CLASS_NAME, "smv__incident").text.replace("\n", "")
                                         .replace("'", '-') + "-red")
                        elif svg == ROJA:
                            cards.append(incident.find_element(By.CLASS_NAME, "smv__incident").text.replace("\n", "")
                                         .replace("'", '-') + "-red")
                        elif svg == GOL:
                            goals.append(incident.find_element(By.CLASS_NAME, "smv__incident")
                                         .text.replace("\n", "").replace("'", '-'))
                        else:
                            pass
                    except NoSuchElementException:
                        pass
            except NoSuchElementException:
                pass
        # Con Resumen, Estadisticas pero vacio
        # time.sleep(2)
        match["Players_goal"] = goals
        match["Players_card"] = cards
        # Estadisticas - comprobar que tenga información disponible
    except:
        match["Score_1T"] = 'VACIO'
        match["Score_2T"] = 'VACIO'
        match["Players_goal"] = ''
        match["Players_card"] = ''

    # First_Time
    url = URL_CABECERA + match_id + URL_ESTADISCTICAS + '1'
    driver.get(url)

    try:
        stats = driver.find_elements(By.CLASS_NAME, "stat__row")
        first_time_stats = {stat[1]: [stat[0], stat[2]] for stat in [stat.text.replace('\n', ' - ').split(' - ')
                                                                     for stat in stats]}
    except NoSuchElementException:
        pass

    # time.sleep(2)
    # Second_Time
    url = URL_CABECERA + match_id + URL_ESTADISCTICAS + '2'
    driver.get(url)

    try:
        stats = driver.find_elements(By.CLASS_NAME, "stat__row")
        second_time_stats = {stat[1]: [stat[0], stat[2]] for stat in [stat.text.replace('\n', ' - ').split(' - ')
                                                                      for stat in stats]}
    except NoSuchElementException:
        pass
    if guardar_escudo == 'yes':
        match = save_team_images(driver, country, match)

    columns = ', '.join(str(x).replace('/', '_') for x in match.keys())
    values = ', '.join("'" + str(x).replace('[', '').replace(']', '').replace("'", '') + "'" for x in match.values())

    if first_time_stats != {}:
        columns = columns + ', ' + '_1T, '.join(
            str(x).replace(' ', '_').replace('Posesión_de_balón', 'Posesion_de_balon')
            .replace("Distancia_recorrida_(metros)", "Distancia_recorrida")
            for x in first_time_stats.keys()) + '_1T '
        values = values + ', ' + ', '.join(
            "'" + str(x).replace('[', '').replace(']', '').replace("'", '').replace('%', '')
            + "'" for x in first_time_stats.values())

    if second_time_stats != {}:
        columns = columns + ', ' + '_2T, '.join(str(x).replace(' ', '_').replace('Posesión_de_balón',
                                                                                 'Posesion_de_balon').replace(
            "Distancia_recorrida_(metros)", "Distancia_recorrida") for x in second_time_stats.keys()) + '_2T'
        values = values + ', ' + ', '.join(
            "'" + str(x).replace('[', '').replace(']', '').replace("'", '').replace('%', '') + "'" for x in
            second_time_stats.values())

    sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (stage_area, columns, values)
    cursor.execute(sql)
    cnxn.commit()


def only_resume(driver, match_id, year, country, cnxn, cursor, stage_area, guardar_escudo):
    incidentes = {
        "cards": [],
        "goals": [],
        "yellow_first_time": [0, 0],
        "yellow_second_time": [0, 0],
        "red_first_time": [0, 0],
        "red_second_time": [0, 0],
    }
    if year == "":
        year = YEAR
    match = init_match(driver, match_id, year)

    # Equipos
    list_teams = driver.find_elements(By.CLASS_NAME, "participant__overflow a")
    match["Teams"] = [team.text for team in list_teams]
    # time.sleep(1)

    # Info Adicicional
    try:
        adicional = [item.text.replace("\n", "") for item in driver.find_elements(By.CLASS_NAME, "mi__item")]
        match["Info"] = adicional
    except NoSuchElementException:
        pass

    incidentes = extract_incidents(driver, "home", incidentes)
    incidentes = extract_incidents(driver, "away", incidentes)

    # Players Goal & Card
    match["Players_goal"] = incidentes["goals"]
    match["Players_card"] = incidentes["cards"]

    # Statistics

    score = driver.find_elements(By.CLASS_NAME, "section__title")
    match["Score_1T"] = score[0].text.replace('1ER TIEMPO\n', '').split('-')
    try:
        match["Score_2T"] = score[1].text.replace('2º TIEMPO\n', '').split('-')
    except:
        match["Score_2T"] = 'RESULTADO FINAL'

    match["TARJETAS_AMARILLAS_1T"] = incidentes["yellow_first_time"]
    match["TARJETAS_AMARILLAS_2T"] = incidentes["yellow_second_time"]
    match["TARJETAS_ROJAS_1T"] = incidentes["red_first_time"]
    match["TARJETAS_ROJAS_2T"] = incidentes["red_second_time"]

    if guardar_escudo == 'yes':
        match = save_team_images(driver, country, match)

    columns = ', '.join(str(x).replace('/', '_') for x in match.keys())
    values = ', '.join("'" + str(x).replace('[', '').replace(']', '').replace("'", '') + "'" for x in match.values())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (stage_area, columns, values)
    cursor.execute(sql)
    cnxn.commit()


def extract_incidents(driver, homeaway, incidentes):
    if homeaway == "home":
        i = 0
    else:
        i = 1
    try:
        incidents = driver.find_elements(By.CLASS_NAME, "smv__" + homeaway + "Participant")
        for incident in incidents:
            try:
                svg = incident.find_element(By.TAG_NAME, "svg").get_attribute("class")
                if svg == AMARILLA:
                    card_time = incident.find_element(By.CLASS_NAME, "smv__timeBox").text.replace("'", "")
                    if card_time == '':
                        card_time = '0'
                    if "+" in card_time:
                        card_time = card_time.split("+")
                        card_time = int(card_time[0]) + int(card_time[1])
                        if card_time > 45:
                            incidentes["yellow_first_time"][i] += 1
                        else:
                            incidentes["yellow_first_time"][i] += 1
                    elif int(card_time) > 45:
                        incidentes["yellow_second_time"][i] += 1
                    else:
                        incidentes["yellow_first_time"][i] += 1
                    incidentes["cards"].append(incident.find_element(By.CLASS_NAME, "smv__incident").text + "-yellow")
                elif svg == SEGUNDA_AMARILLA:
                    card_time = incident.find_element(By.CLASS_NAME, "smv__timeBox").text.replace("'", "")
                    if card_time == '':
                        card_time = '0'
                    if "+" in card_time:
                        card_time = card_time.split("+")
                        card_time = int(card_time[0]) + int(card_time[1])
                        if card_time > 45:
                            incidentes["yellow_first_time"][i] += 1
                            incidentes["red_first_time"][i] += 1
                        else:
                            incidentes["yellow_first_time"][i] += 1
                            incidentes["red_first_time"][i] += 1
                    elif int(card_time) > 45:
                        incidentes["yellow_second_time"][i] += 1
                        incidentes["red_second_time"][i] += 1
                    else:
                        incidentes["yellow_first_time"][i] += 1
                        incidentes["red_first_time"][i] += 1
                    incidentes["cards"].append(incident.find_element(By.CLASS_NAME, "smv__incident").text + "-yellow")
                    incidentes["cards"].append(incident.find_element(By.CLASS_NAME, "smv__incident").text + "-red")
                elif svg == ROJA:
                    card_time = incident.find_element(By.CLASS_NAME, "smv__timeBox").text.replace("'", "")
                    if card_time == '':
                        card_time = '0'
                    if "+" in card_time:
                        card_time = card_time.split("+")
                        card_time = int(card_time[0]) + int(card_time[1])
                        if card_time > 45:
                            incidentes["red_first_time"][i] += 1
                        else:
                            incidentes["red_first_time"][i] += 1
                    elif int(card_time) > 45:
                        incidentes["red_second_time"][i] += 1
                    else:
                        incidentes["red_first_time"][i] += 1
                    incidentes["cards"].append(incident.find_element(By.CLASS_NAME, "smv__incident").
                                               text.replace("\n", "") + "-red ")
                elif svg == GOL:
                    incidentes["goals"].append(incident.find_element(By.CLASS_NAME, "smv__incident").
                                               text.replace("\n", "").replace("'", '-'))
                else:
                    pass
            except NoSuchElementException:
                pass
        return incidentes
    except NoSuchElementException:
        pass


def incident_match(driver, match_id, year, country, cnxn, cursor, stage_area, guardar_escudo, anulado):
    # Informacion General
    if year == "":
        year = YEAR
    match = init_match(driver, match_id, year)
    match["Info"] = anulado
    if guardar_escudo == 'yes':
        match = save_team_images(driver, country, match)

    columns = ', '.join(str(x).replace('/', '_') for x in match.keys())
    values = ', '.join("'" + str(x).replace('[', '').replace(']', '').replace("'", '') + "'" for x in match.values())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (stage_area, columns, values)
    cursor.execute(sql)
    cnxn.commit()


def only_score(driver, match_id, year, cnxn, country, cursor, stage_area, guardar_escudo):
    if year == "":
        year = YEAR

    match = init_match(driver, match_id, year)
    # Score
    try:
        score = driver.find_elements(By.CLASS_NAME, "section__title")
        if len(score) > 1:
            match["Score_1T"] = score[0].text.replace('1ER TIEMPO\n', '').split('-')
            match["Score_2T"] = score[1].text.replace('2º TIEMPO\n', '').split('-')
            try:
                adicional = [item.text.replace("\n", "") for item in driver.find_elements(By.CLASS_NAME, "mi__item")]
                match["Info"] = adicional
            except NoSuchElementException:
                pass
        else:
            match["Score_1T"] = score[0].text.split('-')
            match["Info"] = "RESULTADO FINAL"
    except NoSuchElementException:
        pass
    if guardar_escudo == 'yes':
        match = save_team_images(driver, country, match)

    columns = ', '.join(str(x).replace('/', '_') for x in match.keys())
    values = ', '.join("'" + str(x).replace('[', '').replace(']', '').replace("'", '') + "'" for x in match.values())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (stage_area, columns, values)
    cursor.execute(sql)
    cnxn.commit()


def calendario(driver, match_id, year, cnxn, cursor, stage_area, country, guardar_imagen):
    if year == "":
        year = YEAR

    if guardar_imagen == "no":
        match = init_match(driver, match_id, year)
        match["Info"] = [item.text.replace("\n", "") for item in driver.find_elements(By.CLASS_NAME, "mi__item")]

    if guardar_imagen == "yes":
        # Guardar el escudo y la posible url en github de la imagen
        folder = FOLDER_ESCUDOS + country + "\\"
        match = {"Country": country,
                 "Teams": [team.text for team in driver.find_elements(By.CLASS_NAME, "participant__overflow a")]}
        try:
            os.makedirs(folder)
        except:
            pass

        list_teams = driver.find_elements(By.CLASS_NAME, "participant__participantLink--team img")
        teams = []
        j = 0
        for team in list_teams:
            teams.append({"nombre": unicodedata.normalize("NFKD", team.get_attribute('alt'))
                         .encode("ascii", "ignore").decode("ascii"), "url": team.get_attribute('src')})
            try:
                urllib.request.urlretrieve(teams[j]["url"], folder + teams[j]["nombre"] + ".png")
            except:
                pass
            j = j + 1

        match["Escudo_Home"] = URL_GITHUB + teams[0]["nombre"] + ".png?raw=true"
        match["Escudo_Away"] = URL_GITHUB + teams[1]["nombre"] + ".png?raw=true"

    columns = ', '.join(str(x).replace('/', '_') for x in match.keys())
    values = ', '.join("'" + str(x).replace('[', '').replace(']', '').replace("'", '') + "'" for x in match.values())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % (stage_area, columns, values)
    cursor.execute(sql)
    cnxn.commit()


def save_team_images(driver, country, match):
    # Guardar el escudo y la posible url en github de la imagen
    folder = FOLDER_ESCUDOS + country + "\\"
    list_teams = driver.find_elements(By.CLASS_NAME, "participant__participantLink--team img")
    teams = []
    j = 0
    for team in list_teams:
        teams.append({"nombre": unicodedata.normalize("NFKD", team.get_attribute('alt'))
                     .encode("ascii", "ignore").decode("ascii"), "url": team.get_attribute('src')})
        try:
            urllib.request.urlretrieve(teams[j]["url"], folder + teams[j]["nombre"] + ".png")
        except:
            pass
        j = j + 1

    match["Escudo_Home"] = URL_GITHUB + teams[0]["nombre"] + ".png?raw=true"
    match["Escudo_Away"] = URL_GITHUB + teams[1]["nombre"] + ".png?raw=true"

    return match
