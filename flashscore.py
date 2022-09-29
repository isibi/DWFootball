import json
import time
import urllib
from datetime import datetime
import os
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Flashscore:
    URL = "https://www.flashscore.es/futbol/"
    PATH = "D:/Business Intelligence/DWFutbol/ETL/LOG/"

    def __init__(self):
        self.__date = datetime.now().strftime('%Y%m%d%H%M%S')
        self.__log_path = self.PATH

        try:
            os.makedirs(self.__log_path)
        except:
            pass

    def scrap_countries(self):
        pass

    def scrap_yesterday(self, driver):
        driver.get(self.URL)
        time.sleep(1)

        # Rechazar Cookies
        try:
            driver.find_element(By.ID, "onetrust-reject-all-handler").click()
            time.sleep(1)
        except NoSuchElementException:
            pass
        # Ir a la version +18 con cuotas de apuestas
        try:
            driver.find_element(By.CLASS_NAME, "lac__button").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Boton SI version con cuotas
        try:
            driver.find_element(By.CLASS_NAME, "lacModal__confirmationButtonActive").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Desabilitar el alert de actualizaciones de marcadores. Sale hasta 3 veces
        for i in range(3):
            try:
                alert_obj = driver.switch_to.alert
                alert_obj.accept()
                time.sleep(1)
            except NoAlertPresentException:
                pass

        # Boton Ayer
        try:
            driver.find_element(By.CLASS_NAME, "calendar__navigation--yesterday").click()
            # time.sleep(1)
        except NoAlertPresentException:
            pass
        # Desplegar todos los partidos
        time.sleep(1)
        btn_matches = driver.find_elements(By.CLASS_NAME, "event__header")
        for btn_match in btn_matches:
            try:
                title = btn_match.find_element(By.CLASS_NAME, "event__expanderBlock").get_attribute("title")
                if title == "Mostrar todos los partidos de esta liga":
                    btn_match.find_element(By.CLASS_NAME, "event__expanderBlock").click()
            except NoSuchElementException:
                pass

            # Buscar los Id de los partidos
            matches_id = driver.find_elements(By.CLASS_NAME, "event__match--twoLine")
            matches_id = [div.get_attribute('id') for div in matches_id]
            matches_id = list(map(lambda match_id: match_id.replace("g_1_", ""), matches_id))

        self.save_collected_ids('', '', '', matches_id)
        return matches_id

    def scrap_today(self, driver):
        driver.get(self.URL)
        time.sleep(1)

        # Rechazar Cookies
        try:
            driver.find_element(By.ID, "onetrust-reject-all-handler").click()
            time.sleep(1)
        except NoSuchElementException:
            pass
        # Ir a la version +18 con cuotas de apuestas
        try:
            driver.find_element(By.CLASS_NAME, "lac__button").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Boton SI version con cuotas
        try:
            driver.find_element(By.CLASS_NAME, "lacModal__confirmationButtonActive").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Desabilitar el alert de actualizaciones de marcadores. Sale hasta 3 veces
        for i in range(3):
            try:
                alert_obj = driver.switch_to.alert
                alert_obj.accept()
                time.sleep(1)
            except NoAlertPresentException:
                pass
        time.sleep(1)
        btn_matches = driver.find_elements(By.CLASS_NAME, "event__expanderBlock")
        for btn_match in btn_matches:
            if btn_match.get_attribute("title") == "Mostrar todos los partidos de esta liga":
                try:
                    btn_match.find_element(By.CLASS_NAME, "event__expander--close").click()
                except NoSuchElementException:
                    pass
        # Buscar los Id de los partidos
        matches_id = driver.find_elements(By.CLASS_NAME, "event__match--twoLine")
        matches_id = [div.get_attribute('id') for div in matches_id]
        matches_id = list(map(lambda match_id: match_id.replace("g_1_", ""), matches_id))

        self.save_collected_ids('', '', '', matches_id)
        return matches_id

    def scrap_competition(self, country, championship, year, s_url, tipo_scrap, n_partidos):
        driver = webdriver.Chrome()
        driver.minimize_window()
        if year == '':
            url = self.URL + country + '/' + championship + s_url
        else:
            url = self.URL + country + '/' + championship + '-' + year + s_url

        driver.get(url)

        start = datetime.now()
        print('[' + country.upper() + ' ' + championship.upper() + ' ' + str(year) + ' '
              + start.strftime('%m/%d/%Y %H:%M:%S') + ']')

        if tipo_scrap == "competition":
            while True:
                try:
                    time.sleep(1)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    driver.find_element(By.CSS_SELECTOR, 'a.event__more.event__more--static').click()
                except NoSuchElementException:
                    break

            # Buscar los Id de los partidos
            matches_id = driver.find_elements(By.CLASS_NAME, "event__match--twoLine")
            matches_id = [div.get_attribute('id') for div in matches_id]
            matches_id = list(map(lambda match_id: match_id.replace("g_1_", ""), matches_id))

        else:
            ids = []
            matches_id = driver.find_elements(By.CLASS_NAME, "event__match--twoLine")
            for index, div in enumerate(matches_id):
                ids.append(div.get_attribute('id'))
                if index + 1 == n_partidos:
                    break
            ids = list(map(lambda ids: ids.replace("g_1_", ""), ids))
            matches_id = ids

        if not matches_id:
            print('ERROR: ' + country.upper() + ' ' + championship.upper() + ' ' + str(year) + ' NOT FOUND')
            return []

        self.save_collected_ids(country, championship, year, matches_id)
        return matches_id

    def save_collected_ids(self, country, championship, year, matches_id):
        file = 'ids-' + self.__date + '.txt'

        with open(self.__log_path + file, 'a+', encoding='utf-8') as outfile:
            outfile.write(datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ' ' + country + ' ' + championship + ' ' + str(
                year) + '\n')
            outfile.write(str(matches_id) + '\n\n')

        print(' MATCHES ID COLLECTED: ' + str(len(matches_id)))

    def save_log_error(self, country, championship, year, match_id, match_type, e):
        file = 'error-' + country + '_' + championship + '_' + year + '.txt'
        with open(self.__log_path + file, 'a+', encoding='utf-8') as outfile:
            outfile.write(country + ' ' + championship + ' ' + str(year) + ' ' + match_id + ' ' + match_type + '-'
                          + str(e) + '\n')
        print('❌[ERROR WHILE COLLECT MATCH: ' + str(match_id))

    def recorrer_pagina(self, driver):

        driver.get(self.URL)
        time.sleep(1)

        # Rechazar Cookies
        try:
            driver.find_element(By.ID, "onetrust-reject-all-handler").click()
            time.sleep(1)
        except NoSuchElementException:
            pass
        # Ir a la version +18 con cuotas de apuestas
        try:
            driver.find_element(By.CLASS_NAME, "lac__button").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Boton SI version con cuotas
        try:
            driver.find_element(By.CLASS_NAME, "lacModal__confirmationButtonActive").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # Desabilitar el alert de actualizaciones de marcadores. Sale hasta 3 veces
        for i in range(3):
            try:
                alert_obj = driver.switch_to.alert
                alert_obj.accept()
                time.sleep(1)
            except NoAlertPresentException:
                pass
        time.sleep(1)
        btn_matches = driver.find_elements(By.CLASS_NAME, "event__expanderBlock")
        for btn_match in btn_matches:
            if btn_match.get_attribute("title") == "Mostrar todos los partidos de esta liga":
                try:
                    btn_match.find_element(By.CLASS_NAME, "event__expander--close").click()
                except NoSuchElementException:
                    pass
        # Buscar los Id de los partidos
        matches_id = driver.find_elements(By.CLASS_NAME, "event__match--twoLine")
        matches_id = [div.get_attribute('id') for div in matches_id]
        matches_id = list(map(lambda match_id: match_id.replace("g_1_", ""), matches_id))

        self.save_collected_ids('', '', '', matches_id)
        return matches_id
