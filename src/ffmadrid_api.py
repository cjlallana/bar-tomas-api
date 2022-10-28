from datetime import datetime
from urllib.parse import parse_qs

import requests

from bs4 import BeautifulSoup

BASE_URL = 'http://aranjuez.ffmadrid.es/nfg/'

def _save_to_datastore():
    from google.cloud import datastore
    # Create, populate and persist an entity with keyID=1234
    client = datastore.Client()

    key = client.key('EntityKind', 1234)
    entity = datastore.Entity(key=key)
    entity.update({
        'foo': u'bar',
        'baz': 1337,
        'qux': False,
    })
    client.put(entity)
    # Then get by key for this entity
    result = client.get(key)
    print(result)

def _get_session():
    """
    Common requests regarding login and related cookies/session
    """

    headers = {
        'User-Agent': 'My User Agent 1.0',
        'Accept': '*/*',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Method': 'POST /nfg/NLogin HTTP/1.1',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': 'http://aranjuez.ffmadrid.es',
        'Connection': 'keep-alive',
        'Referer': 'http://aranjuez.ffmadrid.es/nfg/',
    }

    s = requests.Session()

    # Prepare the login request
    form_data = {'NUser': 'B7529',
                'NPass': 'Miguel11',
                'LoginAjax': 1,
                'N_Ajax': 1}

    # Login request
    #s.post(BASE_URL + 'NLogin', data=form_data, headers=headers)
    s.post(BASE_URL + 'NLogin', data=form_data)

    return s

def _get_table_primera():

    s = _get_session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Referer': 'http://aranjuez.ffmadrid.es/nfg/NPcd/NFG_CmpJornada?cod_primaria=1000128',
        'Upgrade-Insecure-Requests': '1',
    }

    # Prepare the params for the classification table request
    payload = { 'cod_primaria': '1000128',
                'codjornada': '99',
                'codcompeticion': '1004152',
                'codgrupo': '1004160'}

    # Classification table request
    r = s.get(BASE_URL + 'NPcd/NFG_VisClasificacion', params=payload, headers=headers)

    standings = []

    # Starting the parsing process
    soup = BeautifulSoup(r.text, 'html.parser')

    # To retrieve the current jornada, we need to parse the URL for "Ver Calendario"
    str_href = soup.find_all("a", string="Ver Calendario")[0]['href']
    current_jornada = int(parse_qs(str_href).get('CodJornada')[0])

    # The word 'Sancion' appears in two tables, and we want the second one,
    # which is the "Tabla resumida"
    table = soup.find_all("span", string="Sanción")[1].findParents('table')[0]

    # Now, we get the <tr>s related to each team
    tr_teams = table.find_all("tr", {"bgcolor" : "#FFFFFF"})

    # For each <tr>, we need to extract the parameters
    for tr in tr_teams:

        # Create a dict for the team
        team = {}

        # Each <td> is a parameter
        td_params = tr.find_all('td')

        team.update({'position': td_params[1].get_text().strip()})
        team.update({'name': td_params[2].get_text().strip().title()})
        team.update({'points': td_params[3].get_text().strip()})
        team.update({'m_played': td_params[4].get_text().strip()})
        team.update({'m_won': td_params[5].get_text().strip()})
        team.update({'m_drawn': td_params[6].get_text().strip()})
        team.update({'m_lost': td_params[7].get_text().strip()})
        team.update({'goals_scored': td_params[8].get_text().strip()})
        team.update({'goals_conceded': td_params[9].get_text().strip()})
        team.update({'last_games': td_params[10].get_text().split()})
        team.update({'sanction_points': td_params[11].get_text().strip()})

        standings.append(team)
    
    return standings, current_jornada


def _get_table_segunda():

    s = _get_session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Referer': 'http://aranjuez.ffmadrid.es/nfg/NPcd/NFG_CmpJornada?cod_primaria=1000128',
        'Upgrade-Insecure-Requests': '1',
    }

    # Prepare the params for the classification table request
    payload = { 'cod_primaria': '1000128',
                'codjornada': '99',
                'codcompeticion': '1004152',
                'codgrupo': '1004160'}

    # Classification table request
    r = s.get(BASE_URL + 'NPcd/NFG_VisClasificacion', params=payload, headers=headers)

    standings = []

    # Starting the parsing process
    soup = BeautifulSoup(r.text, 'html.parser')

    # There are many <table>s in the html. We want the 10th, which is the "Tabla resumida"
    table = soup.find_all('table')[9]

    # Now, we get the <tr>s related to each team
    tr_teams = table.find_all("tr", {"bgcolor" : "#FFFFFF"})

    # For each <tr>, we need to extract the parameters
    for tr in tr_teams:

        # Create a dict for the team
        team = {}

        # Each <td> is a parameter
        td_params = tr.find_all('td')

        team.update({'position': td_params[1].get_text().strip()})
        team.update({'name': td_params[2].get_text().strip().title()})
        team.update({'points': td_params[3].get_text().strip()})
        team.update({'m_played': td_params[4].get_text().strip()})
        team.update({'m_won': td_params[5].get_text().strip()})
        team.update({'m_drawn': td_params[6].get_text().strip()})
        team.update({'m_lost': td_params[7].get_text().strip()})
        team.update({'goals_scored': td_params[8].get_text().strip()})
        team.update({'goals_conceded': td_params[9].get_text().strip()})
        team.update({'last_games': td_params[10].get_text().split()})
        team.update({'sanction_points': td_params[11].get_text().strip()})

        standings.append(team)
    
    return standings


def _get_matches():
    '''
    Solo listado de partidos no jugados:
    añadir &Sch_Partidos_Jugados=2
    '''

    s = _get_session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Referer': 'http://aranjuez.ffmadrid.es/nfg/NPcd/NFG_CmpJornada?cod_primaria=1000128',
        'Upgrade-Insecure-Requests': '1',
    }

    # Prepare the params for the classification table request
    payload = {
        'cod_primaria': '1000139',
        'Consulta': '1',
        'Sch_Cod_Temporada': '18',
        'Sch_Clave_Acceso_Club': '1022',
        'Club': '1022',
        'NPcd_PageLines': '40'
    }

    # Classification table request
    #r = s.get(BASE_URL + 'NPcd/NFG_LstPartidos', params=payload, headers=headers)
    r = s.get(BASE_URL + 'NPcd/NFG_LstPartidos', params=payload)

    # Starting the parsing process
    soup = BeautifulSoup(r.text, 'html.parser')

    # We want the specific table containing all the matches
    table = soup.find("table", {"class":"table table-striped table-hover table-bordered"})

    # The only way to retrieve each match info is by looking for the spans
    # that contains the little jersey logo, and start from there
    spans = table.find_all("span", {"title" : "Ver equipaciones"})

    matches_info = []

    for s in spans:
        onclick = s['onclick']
        onclick_params = onclick[onclick.find('(')+1:onclick.find(')')].split(',')
        team_home_code = onclick_params[0]
        team_away_code = onclick_params[2]

        td_teams = s.parent
        team_home_name, team_away_name = [x.strip().title() for x in td_teams.text.split('\xa0 - \xa0')]

        #td_date = td_teams.find_previous('td', {'style' : 'border:0px;    background-color: white;'})
        td_date = td_teams.parent.find_previous('tr').find_previous('tr').find_previous('tr')
        full_str_date = " ".join(td_date.text.split())
        date_str, weekday = [x.strip() for x in full_str_date.split(',')]
        date = datetime.strptime(date_str, '%d-%m-%Y')
        weekday = weekday.replace('(', '').replace(')', '')

        td_code = td_teams.find_previous('td')
        code = " ".join(td_code.text.split())

        td_field = td_teams.find_next('td').find_next('td').find_next('td')
        field = " ".join(td_field.text.split())

        td_time = td_field.find_next('td')
        time = " ".join(td_time.text.split())

        td_jornada = td_time.find_next('td')
        jornada = " ".join(td_jornada.text.split())

        td_result = td_jornada.find_next('td').find_next('td')
        result = " ".join(td_result.text.split())
        team_home_goals = td_result.text.split()[0] if result != '-' else '-'
        team_away_goals = td_result.text.split()[2] if result != '-' else '-'

        matches_info.append({
            'team_home_code':team_home_code,
            'team_away_code': team_away_code,
            'team_home_name': team_home_name,
            'team_away_name': team_away_name,
            'code': code,
            'field': field,
            'date': date,
            'time': time,
            'weekday': weekday,
            'jornada': jornada,
            'result': result,
            'team_home_goals': team_home_goals,
            'team_away_goals': team_away_goals
        })

    return matches_info

    '''
    Ver listado de partidos
    http://aranjuez.ffmadrid.es/nfg/NPcd/NFG_LstPartidos?cod_primaria=1000139&Consulta=1&Sch_Fecha_Desde=&Sch_Fecha_Hasta=&Sch_Cod_Temporada=15&Sch_Clave_Acceso_Club=1022&NPcd_PageLines=26

    Solo listado de partidos no jugados:
    añadir &Sch_Partidos_Jugados=2
    '''


def _get_matches2():

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': '*/*',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Method': 'POST /nfg/NLogin HTTP/1.1',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': 'http://aranjuez.ffmadrid.es',
        'Connection': 'keep-alive',
        'Referer': 'http://aranjuez.ffmadrid.es/nfg/',
    }

    BASE_URL = 'http://aranjuez.ffmadrid.es/nfg/'

    s = requests.Session()

    # Prepare the login request
    form_data = {'NUser': 'B7529',
                'NPass': 'Miguel11',
                'LoginAjax': 1,
                'N_Ajax': 1}

    # Login request
    s.post(BASE_URL + 'NLogin', data=form_data, headers=headers)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Referer': 'https://aranjuez.ffmadrid.es/nfg/NPcd/NFG_LstPartidos?cod_primaria=1000139&Consulta=1&Sch_Cod_Temporada=17&Sch_Clave_Acceso_Club=1022&Club=1022&NPcd_PageLines=20',
        'Upgrade-Insecure-Requests': '1',
    }

    # Prepare the params for the classification table request
    payload = {
        'cod_primaria': '1000139',
        'codacta': '2289'
    }

    # Classification table request
    r = s.get(BASE_URL + 'NPcd/NFG_LstPartidosHist', params=payload, headers=headers)

    print(r.text)
    '''
    # Starting the parsing process
    soup = BeautifulSoup(r.text, 'html.parser')

    # We want the specific table containing all the matches
    table = soup.find("table", {"class":"table table-striped table-hover table-bordered"})

    # Now, we get the <tr>s related to each team
    spans = table.find_all("span", {"title" : "Ver equipaciones"})

    teams_against = []

    for s in spans:
        td = s.parent

        teams_names = " ".join(td.text.split())

        teams_against.append(teams_names)

    print(teams_against)

    #print(r.text)
    '''