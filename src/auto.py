import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import psycopg
import os
from dotenv import load_dotenv

team_dict ={
    # Americas
    'G2 Esports': 'G2',
    'KRÜ Esports': 'KRÜ',
    'MIBR': 'MIBR',
    '100 Thieves': '100T',
    'Sentinels': 'SEN',
    'Evil Geniuses': 'EG',
    'NRG': 'NRG',
    'Cloud9': 'C9',
    'LEVIATÁN': 'LEV',
    'LOUD': 'LOUD',
    'FURIA': 'FUR',
    'ENVY': 'ENVY',
    
    # EMEA
    'FNATIC': 'FNC',
    'Natus Vincere': "NAVI",
    'Karmine Corp': "KC",
    'FUT Esports': 'FUT',
    'Gentle Mates': "M8",
    "PCIFIC Esports": "PCF",
    "BBL Esports": "BBL",
    "ULF Esports": "ULF",
    "Team Vitality": "VIT",
    "Team Heretics": "TH",
    "GIANTX": "GX",
    "Team Liquid": "TL",
    "Eternal Fire": "EF",
    
    # China
    "Trace Esports": "TE",
    "Wolves Esports": "WOL",
    "FunPlus Phoenix": "FPX",
    "TYLOO": "TYL",
    "All Gamers": "AG",
    "Nova Esports": "NOVA",
    "JD Mall JDG Esports\n(JDG Esports)": "JDG",
    "Wuxi Titan Esports Club\n(Titan Esports Club)": "TEC",
    "Xi Lai Gaming": "XLG",
    "EDward Gaming": "EDG",
    "Guangzhou Huadu Bilibili Gaming\n(Bilibili Gaming)": "BLG",
    "Dragon Ranger Gaming": "DRG",

    # APAC
    "Nongshim RedForce": "NS",
    "Team Secret": "TS",
    "ZETA DIVISION": "ZETA",
    "FULL SENSE": "FS",
    "VARREL": "VL",
    "Global Esports": "GE",
    "DetonatioN FocusMe": "DFM",
    "Gen.G": "GEN",
    "T1": "T1",
    "KIWOOM DRX": "DRX",
    "Paper Rex": "PRX",
    "Rex Regum Qeon": "RRQ"
}

def abrir_site(link=None):
    '''
    ## Functions that opens the browser and a match game
    
    :param link: vlr.gg link for the match
    :return: browser object
    '''
    chrome_options = Options()
    # Em vez de apenas "--headless", use:
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    navegador = webdriver.Chrome(options=chrome_options)
    if link:
        navegador.get(link)

    return navegador

def get_camp(navegador):
    '''
    ## return camp name in string
    
    :param navegador: vlr's browser of the match
    :return camp: string with camp name
    '''
    return navegador.find_element(By.CLASS_NAME, 'wf-title').text

def get_times(navegador):
    '''
    ## Function that returns team A and team B of a match
    
    :param navegador: vlr's browser of the match
    :return TeamA: team A str name
    :return TeamB:  team B str name
    '''
    times = navegador.find_elements(By.CLASS_NAME, 'wf-title-med')
    times = [time.text.split("\n")[0] for time in times]
    return times

def get_placar(navegador):
    '''
    ## Returns scoreboard
    
    :param navegador: vlr's browser of the match
    :return placar: string with scoreboard, if game started. Otherwise, empty string
    '''
    # Buscando placar:
    placar = navegador.find_elements(By.CLASS_NAME, 'js-spoiler')
    try:
        placar = placar[0].text
    except: 
        placar = ""

    return placar
    
def get_pickban(navegador):
    '''
    ## Returns bans and picks
    
    :param navegador: vlr's browser of the match
    :return bans: list of tuples (ex: [(team, map)]) of banned maps
    :return picks: list of tuples (ex: [(team, map)]) of picked maps + decider ('', map)
    '''
    pickban = navegador.find_elements(By.CLASS_NAME, 'match-header-note')
    if len(pickban) == 2:
        pickban = pickban[1].text
    else:
        pickban = pickban[0].text
    new_pb = pickban.split('; ')
    lista_maps = []
    lista_bans = []

    for item in new_pb:
        if "pick" in item:
            item = item.split(" ")
            lista_maps.append((item[0], item[2]))
        elif 'ban' in item:
            item = item.split(" ")
            lista_bans.append((item[0], item[2]))
        else:
            item = item.split(" ")
            lista_maps.append(('', item[0]))
    
    return lista_bans, lista_maps

def get_map_objects(navegador, picks):
    '''
    ## Return an dictionary that allows you to access the maps in the browser
    
    :param navegador: vlr's browser of the match
    :param picks: list of tuples (ex: [(team, map)]) of picked maps + decider ('', map)
    :return map_pointer: integer. Always 0
    :return dict_maps: dict_maps[picks[map_pointer]].click() ---> access map
    '''
    mapas = navegador.find_elements(By.CLASS_NAME, 'js-map-switch')
    mapas = [mapa.get_attribute('data-game-id') for mapa in mapas]
    dict_maps = {}
    for i, item in enumerate(picks):
        dict_maps[item[1]] = mapas[i+1]

    return 0, dict_maps

def next_map(navegador, dict_maps, picks, map_pointer, current_url):
    '''
    ## Change the map to the indexed at map_pointer
    
    :param dict_maps: dictionary with map names as keys and map objects as values
    :param picks: list of maps piccked
    :param map_pointer: integer
    '''
    id = dict_maps[picks[map_pointer][1]]
    navegador.get(f"{current_url}/?game={id}&tab=overview")

def get_agents_completed(navegador):
    '''
    ## To discover the agents picked in each map of a completted match
    
    :param navegador: vlr's browser of the match

    :return compositions: list of tuples with two lists of five string elements (names of agents).
    Each tuple is for the corresponding map in map_pointer (integer), and each list of the tuple means respectively comp of team A and comp of team B
    '''
    maps = navegador.find_elements(By.CLASS_NAME, 'vm-stats-game')
    compositions = []
    for map in maps:
        # Ignoring section "all maps"
        if map.get_attribute('class').split(' ')[1] != '':
            continue
        
        # Getting all the agents
        agentes = map.find_elements(By.CLASS_NAME, 'mod-agents')
        compositionA = []
        compositionB = []
        
        # Organizing them
        for i, agente in enumerate(agentes):
            linha = agente.find_elements(By.TAG_NAME, 'img')
            try:
                if i < 5:
                    compositionA.append(linha[0].get_attribute('title'))
                else:
                    compositionB.append(linha[0].get_attribute('title'))
            except:
                break
        
        compositions.append([compositionA, compositionB])

    return compositions

def map_treatment(navegador, map):
    '''
    ## Discover who starts attacking, and which is the round sequence of the match at the moment
    
    :param navegador: vlr's browser of the match
    :param map: map where you want to find this information

    :return atq: which team (A or B) is attacking
    :return round_sequence: string of A's, B's and X's. A means round won by team A, B means round won by team B, X mean time change (halftime or going to OT).
    In incomplete matches, it can also means absence of result (winner)
    '''
    # Buscando rounds:                                  Searching rounds
    maps_headers = navegador.find_elements(By.CLASS_NAME, 'vm-stats-game')
    rounds = []
    for header in maps_headers:
        if header.find_elements(By.CLASS_NAME, 'map') == []:
            continue
        if header.find_element(By.CLASS_NAME, 'map').find_element(By.TAG_NAME, 'span').text.split("\n")[0] == map:
            rounds = header.find_elements(By.CLASS_NAME, 'vlr-rounds-row-col')
            break

    # Desconbrindo quem começa atacando                 Discovering who's attacking first
    try:
        first = rounds[1]
        if first.get_attribute('title') == '0-1':
            if first.find_element(By.CLASS_NAME, 'mod-win').get_attribute("class").split(" ")[2] == 'mod-t':
                atq = 'B'
            else:
                atq = 'A'
        else:
            if first.find_element(By.CLASS_NAME, 'mod-win').get_attribute("class").split(" ")[2] == 'mod-t':
                atq = 'A'
            else:
                atq = 'B'
    except:
        atq = ''

    # Monta o round_sequence                            Writting sequence of rounds
    start = ['0', '0']
    round_sequence = ''
    stop = True
    OT = False
    for round in rounds[1:]:
        round = round.get_attribute('title').split('-')
        if round == ['']:
            round_sequence += 'X'
        elif start[0] != round[0]:
            round_sequence += "A"
            start[0] = round[0]
        elif start[1] != round[1]:
            round_sequence += "B"
            start[1] = round[1]
        
        if '13' in start and stop:
            break
        elif abs(int(start[0]) - int(start[1])) == 2 and OT:
            break
        elif start == ['12', '12']:
            OT = True
            stop = False

    return atq, round_sequence

class vlr_stealer():
    '''
    Used to get information from vlr.gg (essentially matches)

    :ivar browser: webdriver.Chrome() object (from selenium, used to access vlr.gg)
    :ivar team: dictionary to translate teams names into teams tags
    :ivar main_win: window where the tournament were open with (matches are opened in an secondary window)
    :ivar camp: string with tournament name
    :ivar matches: list with each tournament's match link

    :param link: string with a vlr.gg tournament page link
    :param team_dict: (optional - one is already loadded) dictionary used to translate teams names into teams tags
    '''
    def __init__(self, link=None, team_dict=team_dict):
        self.browser = abrir_site(link)
        self.teams = team_dict
        self.camp = ''
        self.matches = []
        self.current_url = ""

    def process_camp(self, link=None):
        '''
        processing tournament information
        
        :param link: optional parameter: change tournament
        '''
        if link:
            self.browser.get(link)
        self.camp = get_camp(self.browser)
        self.matches = self.__get_games()
        self.matches.reverse()
        return self.__game_catalog()

    def process_camps(self):
        '''
        getting incompleted tournaments then processing their information
        
        '''
        
        load_dotenv()
        DB_URL = os.getenv("DATABASE_URL")

        def get_conn():
            return psycopg.connect(DB_URL)
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT url, id FROM campeonatos WHERE completo = FALSE")
                camps = cur.fetchall()
                matches = []
                for camp in camps:
                    completed = self.__is_completed(camp[0])
                    self.camp = camp[1]
                    self.matches = self.__get_games()
                    self.matches.reverse()
                    matches.extend(self.__game_catalog())

                    
                    if completed:
                        cur.execute("UPDATE campeonatos SET completo = TRUE WHERE id = %s", (self.camp,))
                        conn.commit()      
                
                return matches

    def __is_completed(self, url):
        '''
        process the tournament page to check if it is completed or not. It is completed if there are no upcoming matches in the tournament page.
        :param url: tournament page link
        :return: boolean. True if there are no upcoming matches, False otherwise
        '''
        self.browser.get(url)
        nav_itens = self.browser.find_elements(By.CLASS_NAME, 'wf-nav-item')
        for item in nav_itens:
            if 'matches' in item.get_attribute("href"):
                self.browser.get(item.get_attribute("href"))
                break

        if len(self.browser.find_element(By.CLASS_NAME, 'wf-subnav') \
                .find_elements(By.PARTIAL_LINK_TEXT, 'All')):
            # Stage category identified, changing the option of it to "All"
            self.browser.get(self.browser.find_element(By.PARTIAL_LINK_TEXT, 'All').get_attribute('href'))

        # Status is "All" by default (in the website). We are changing it to Upcoming
        self.browser.get(self.browser.find_element(By.PARTIAL_LINK_TEXT, 'Upcoming').get_attribute('href'))

        ongoing = self.browser.find_elements(By.CLASS_NAME, 'match-item')
        self.browser.get(url)
        return len(ongoing) == 0

    def match_info(self):
        '''
        processing match information
        
        :param link: optional parameter: change match.
        '''
        
        # Getting the match scoreboard
        placar = get_placar(self.browser).split(' : ')

        # Getting the teams
        times = get_times(self.browser)

        # Trying to catch showmatches;
            # It will ignore games of teams not registered
        for time in times:
            if not (self.teams.get(time)):
                return

        # Getting the pick/ban
        bans, picks = get_pickban(self.browser)
        pickban = self.__gen_pickban(bans, picks, times)

        # To iterate between maps in a single match
        map_pointer, maps_btns = get_map_objects(self.browser, picks)

        # Getting all the compositions
        compositions = get_agents_completed(self.browser)
        map_infos = []

        # Garanting it won't access maps that weren't played
        end = int(placar[0]) + int(placar[1])
        for i, map in enumerate(picks[:end]):
            # Oppening map inside the page
            next_map(self.browser, maps_btns, picks, map_pointer, self.current_url)
            map_pointer += 1
            atk, rnd_sqc = map_treatment(self.browser, map[1])
            # Info of each mpa in a match
            map_infos.append(
                {
                    "id": map[1].lower(),
                    "atk": atk,
                    "composicoes": compositions[i],
                    "rounds": rnd_sqc,
                    "win": rnd_sqc[-1]
                }
            )

        id = self.__get_id()

        # Dict formatted to be stored
        return {
            'id': int(id),
            'camp': self.camp,
            'times': [self.teams[times[0]], self.teams[times[1]]],
            'mapas': map_infos[:],
            'pickban': pickban,
            'winner': "A" if placar[0] > placar[1] else "B"
        }

    def __get_id(self, link=None):
        if link:
            self.browser.get(link)

        url = self.browser.current_url
        return url.split('/')[3]
    
    def last_match_info(self, link=None, quantity=1):
        '''
        processing "recently" match information
        
        :param link: optional parameter: change match.
        :param quantity: optional parameter: define how much matches will you process. By default, just the last, 
        but you can process the three most recently completed matches of the tournament, for example
        '''
        # if optional link is given, change the page to it
        if link:
            self.browser.get(link)
        
        self.camp = get_camp(self.browser)

        # accessing tournament completed matches page and
            # getting all the matches, (from the most recently completed to the least)
        self.matches = self.__get_games()[:quantity]
        self.matches.reverse()
        return self.__game_catalog()

    def __get_games(self):
        '''
        :return matches: list of "match elements" -> .click() = window with match info
        '''
        # Finding and opening the page with the tournament's match history
        nav_itens = self.browser.find_elements(By.CLASS_NAME, 'wf-nav-item')
        for item in nav_itens:
            if 'matches' in item.get_attribute("href"):
                self.browser.get(item.get_attribute("href"))
                break
        
        # All the tournament matches pages have Status category. Some have Stage.
            # When they have both, it will be 1, else 0 
            # (If it has "Stage" but "All" is selected, we don't have to treat this section, 
            # and it will ignore the stage category)
        if len(self.browser.find_element(By.CLASS_NAME, 'wf-subnav') \
                           .find_elements(By.PARTIAL_LINK_TEXT, 'All')):
            # Stage category identified, changing the option of it to "All"
            self.browser.get(self.browser.find_element(By.PARTIAL_LINK_TEXT, 'All').get_attribute('href'))

        # Status is "All" by default (in the website). We are changing it to completed
        self.browser.get(self.browser.find_element(By.PARTIAL_LINK_TEXT, 'Completed').get_attribute('href'))

        load_dotenv()
        DB_URL = os.getenv("DATABASE_URL")

        def get_conn():
            return psycopg.connect(DB_URL)

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM partidas WHERE camp_id = %s", (self.camp,))
                registered_matches = [str(r[0]) for r in cur.fetchall()]
                matches = []
                for match in self.browser.find_elements(By.CLASS_NAME, 'match-item'):
                    if match.get_attribute("href").split('/')[3] in registered_matches:
                        continue
                    matches.append(match.get_attribute("href"))
                
                return matches
    
    def __game_catalog(self):
        '''
        :return catalog: list of dict items with formatted match info
        '''
        games = []
        pbar = tqdm(total=len(self.matches), position=0, leave=True)

        for match in self.matches:
            # Progress bar
            pbar.update()

            self.browser.get(match)

            self.current_url = self.browser.current_url

            info = self.match_info()

            # If teams not registered, match_info returns Null, and that game is not considered
            if info:
                games.append(info)
        
        return games

    def __gen_pickban(self, bans, picks, times):
        '''
        :param bans: list of tuples (ex: [(team, map)]) of banned maps
        :param picks: list of tuples (ex: [(team, map)]) of picked maps + decider ('', map)
        :param times: tuple of both the team names

        :return pickban: dictionary with 4 lists and one string: Abans, Bbans, Apicks, Bpicks and decider

        :ivar Abans: list that contains strings with the names of maps banned by team A
        :ivar Bbans: list that contains strings with the names of maps banned by team B
        :ivar Apicks: list that contains strings with the names of maps picked by team A
        :ivar Bpicks: list that contains strings with the names of maps picked by team B
        :iva decider: string that contais the name of the final map
        '''
        # Pre loading variables retuned
        Abans = []
        Bbans = []
        Apicks = []
        Bpicks = []
        decider = ""

        # Checking which team banned each banned map
        for ban in bans:
            if ban[0] == self.teams[times[0]]:
                Abans.append(ban[1])
            elif ban[0] == self.teams[times[1]]:
                Bbans.append(ban[1])
            else:
                print(f"Erro ban: {ban}")
            
        # Checking which team picked each picked map (+ which map is the decider)
        for pick in picks:
            if pick == picks[-1]:
                decider = pick[1]
            elif pick[0] == self.teams[times[0]]:
                Apicks.append(pick[1])
            elif pick[0] == self.teams[times[1]]:
                Bpicks.append(pick[1])
            else:
                print(f"Erro pick: {pick}")
        
        # Associating before adding in the dictionary
        pickban = {
            "Abans": Abans, 
            "Bbans": Bbans, 
            "Apicks": Apicks, 
            "Bpicks": Bpicks, 
            "decider": decider
        }
        
        return pickban
    
    def stats_table(self):
        '''
        Getting the parameters for creating an pandas table of players' stats

        :return table: matrix with all the values for each row of stats
        :return columns: Array with strings containing the columns' names
        '''
        # Finding and opening the page with the tournament's stats info
        nav_itens = self.browser.find_elements(By.CLASS_NAME, 'wf-nav-item')
        for item in nav_itens:
            if 'stats' in item.get_attribute('href'):
                self.browser.get(item.get_attribute('href'))
                break
        
        # Creating an array with all the columns names
        stats_table = self.browser.find_element(By.TAG_NAME, "table")
        columns = stats_table.find_element(By.TAG_NAME, "thead") \
                             .find_elements(By.TAG_NAME, "th")
        columns = [column.text for column in columns]

        # Creating a matrix with all the rows of stats
        rows = stats_table.find_element(By.TAG_NAME, "tbody") \
                          .find_elements(By.TAG_NAME, "tr")
        table = []
        for row in rows:
            stats = row.find_elements(By.TAG_NAME, "td")
            stats = [stat.text for stat in stats]
            table.append(stats)

        return table, columns

def creating_table(param):
    '''
    Given the return of vlr_stealer.stats_table(), it returns a pandas table


    :param param: return of vlr_stealer.stats_table()
    :return table: pd.DataFrame object
    '''
    linhas, colunas = param
    return pd.DataFrame(linhas, columns=colunas)

def fixing_info(table):
    '''
    removing useless info, adding additional info, fixing columns names, fixing value types

    :param table: pd.DataFrame object
    :return table: pd.DataFrame object with reorganized and fixed values
    '''
    # Removing useless info
    useless_info = ["AGENTS", "RND", "KMAX", "K", "D", "A", "FK", "FD", "CL%"]
    table = table.drop(columns=useless_info)

    # Inserting new column
    table.insert(1, "TEAM", "N/A")

    # Fixing columns names
    new_columns = {"R2.0": "RATING", "K:D": "K/D"}
    table = table.rename(columns=new_columns)

    # Fixing value types
    colunas_numericas = ["RATING", "ACS", "K/D", "ADR", "KPR", "APR", "FKPR", "FDPR"]
    colunas_porcentagem = ["KAST", "HS%"]
    table[colunas_numericas] = table[colunas_numericas].astype(float)
    for coluna in colunas_porcentagem:
        table[coluna] = table[coluna].str.replace("%", "").astype(float) / 100

    return table

def sep_team_player(table):
    '''
    separatting the info of "PLAYER" (previusly player+team) into PLAYER and TEAM

    :param table: pd.DataFrame object
    :return table: pd.DataFrame object
    '''
    for linha in table.index:
        player, time = table.loc[linha, "PLAYER"].split("\n")
        table.loc[linha, "PLAYER"] = player
        table.loc[linha, "TEAM"] = time
    
    return table

class stats_manager():
    def __init__(self, param):
        self.table = self.__pre_processing_table(param)

    def display(self):
        print(self.table.head(), self.table.info())

    def save(self):
        #TODO
        pass

    def __pre_processing_table(self, param):
        table = creating_table(param)
        table = fixing_info(table)
        return sep_team_player(table)

if __name__ == "__main__":
    linkAM = 'https://www.vlr.gg/event/2682/vct-2026-americas-kickoff'
    linkEM = 'https://www.vlr.gg/event/2684/vct-2026-emea-kickoff'
    linkCH = 'https://www.vlr.gg/event/2685/vct-2026-china-kickoff'
    linkAP = 'https://www.vlr.gg/event/2683/vct-2026-pacific-kickoff'
    linkMA = 'https://www.vlr.gg/event/2760/valorant-masters-santiago-2026'
    mtc_gtr = vlr_stealer()
    
    # for camp in [linkAM, linkEM, linkCH, linkAP, linkMA]:
    #     json = mtc_gtr.process_camp(camp)
    #     api_handler = nah.handler(json)
    #     api_handler.add_partidas()

    json = mtc_gtr.process_camps()
    print(json)
    # api_handler = nah.handler(json)
    # api_handler.add_partidas()
    
    
    
    
    
    
    
    
    #print("\n\n\n")
    #print(mtc_gtr.match_info('https://www.vlr.gg/598922/jdg-esports-vs-titan-esports-club-vct-2026-china-kickoff-ur1'))
    #print("\n\n\n")
    #print(mtc_gtr.last_match_info('https://www.vlr.gg/event/2283/valorant-champions-2025', quantity=5))
    #print("\n\n\n")
    #print(mtc_gtr.last_match_info(quantity=0))
    #tabela = stats_manager(mtc_gtr.stats_table())
    #print(tabela.display())