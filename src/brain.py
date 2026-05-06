from dotenv import load_dotenv
import pandas as pd
import asyncio
import psycopg
import json
import os

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

async def get_conn():
    return await psycopg.AsyncConnection.connect(DB_URL)

async def load_id_times(cur):
    await cur.execute("SELECT id, tag, emoji, regiao, nome, img_url FROM times WHERE id != 0 ORDER BY regiao, tag")
    rows = await cur.fetchall()
    return [{"id": int(id), "tag": tag, "emoji": emoji, "regiao": regiao, "nome": nome, "img_url": img_url} for id, tag, emoji, regiao, nome, img_url in rows]

async def load_id_maps(cur):
    await cur.execute("SELECT id, nome, in_pool FROM mapas_lista")
    rows = await cur.fetchall()
    return {int(id): {"nome": nome, "in_pool": in_pool} for id, nome, in_pool in rows}
        
async def load_id_agents(cur):
    await cur.execute("SELECT id, nome, emoji_discord FROM agentes")
    rows = await cur.fetchall()
    return {int(id): {"nome": nome, "emoji": emoji} for id, nome, emoji in rows}

async def load_id_comps(cur):
    await cur.execute("SELECT id, agente1, agente2, agente3, agente4, agente5 FROM composicoes")
    rows = await cur.fetchall()
    return {int(id): [int(agent1), int(agent2), int(agent3), int(agent4), int(agent5)] for id, agent1, agent2, agent3, agent4, agent5 in rows}
        
async def load_id_camps(cur):
    await cur.execute("SELECT id, nome FROM campeonatos")
    rows = await cur.fetchall()
    return {int(id): nome for id, nome in rows}

async def load_id_partidas(cur, camps_dict):
    await cur.execute("SELECT id, camp_id, timea_id, timeb_id, vencedor_time_letra, pickban_log FROM partidas")
    rows = await cur.fetchall()
    partidas_cache = [
        {"id": r[0], "camp_id": camps_dict.get(r[1]), "timeA/B": [r[2], r[3]], "vencedor_time_letra": r[4], "pickban": json.loads(r[5])} 
        for r in rows
    ] 
    return partidas_cache

async def load_id_mapas_jogados(cur, maps_dict, comps_dict):
    await cur.execute("SELECT id, partida_id, mapa_id, vencedor_mapa, rounds_string, atk_start, compa_id, compb_id FROM mapas_jogados")
    rows = await cur.fetchall()
    mapas_jogados_cache = [
        {
            "id": r[0], "partida_id": r[1],"id_mapa": r[2], "nome": maps_dict[r[2]]["nome"], 
            "win": r[3], "rounds": r[4], "atk_start": r[5],
            "comps": [comps_dict.get(r[6]), comps_dict.get(r[7])]
        }
        for r in rows
    ]
    return mapas_jogados_cache

class Brain:
    def __init__(self, times, maps, agents, comps, camps, partidas, mapas_jogados):
        self.times = times
        self.maps = maps
        self.agents = agents
        self.comps = comps
        self.camps = camps
        self.partidas = partidas
        self.mapas_jogados = mapas_jogados
        self.players = {}

    def update_data(self, cache):
        self.times = cache[0]           # times
        self.maps = cache[1]            # maps
        self.agents = cache[2]          # agents
        self.comps = cache[3]           # comps
        self.camps = cache[4]           # camps
        self.partidas = cache[5]        # partidas
        self.mapas_jogados = cache[6]   # mapas_jogados
        self.players = {}

    async def info_time(self, time_tag):
        # If the times list is empty, we return a specific error code (1)
        if not self.times:
            return 1
        
        # Searching for the team in the 'times' list
        time = None
        for team in self.times:
            if time_tag.lower() in [team["tag"].lower(), team["nome"].lower()]:
                time = team
                break
        
        # if the team is not found, we return a specific error code (2)
        if not time:
            return 2
        
        else:
            #       Embed1          - Creating the description for the embed with the last 5 matches of the team
            time_id = time.get("id")

            # 1. Get all matches of the team
            all_matches = [ p for p in self.partidas if time_id in p["timeA/B"] ]

            # Ordering them by ID to get the most recent ones
            all_matches.sort(key=lambda x: x["id"])

            team_partidas5 = all_matches[-5:]

            # id list for next filtering step
            ids_partidas_filtradas = {p["id"] for p in all_matches}
            ids_ultimas_5 = {p["id"] for p in team_partidas5}

            # 3. getting maps from the last 5 matches and from all matches for the second embed
            all_mapas = []
            mapas_5 = {}
            for m in self.mapas_jogados:
                p_id = m["partida_id"]
                # this map belongs to one of the matches of the team?
                if p_id in ids_partidas_filtradas:
                    all_mapas.append(m)

                    # this map belongs to one of the last 5 matches of the team?
                    if p_id in ids_ultimas_5:
                        if p_id not in mapas_5:
                            mapas_5[p_id] = []
                        mapas_5[p_id].append({"win": m["win"]})

            matches_descript = ""

            emoji_map = {t['id']: t['emoji'] for t in self.times}

            # 4. Creating the description for the embed with the last 5 matches of the team
                # camp_name: emote_teamA [A wins] X [B wins] emote_teamB
            for match in team_partidas5:
                timeAB = match["timeA/B"][:]
                a = 0
                b = 0
                emoji_a = emoji_map.get(timeAB[0], "❓") 
                emoji_b = emoji_map.get(timeAB[1], "❓")

                mapas_da_partida = mapas_5.get(match["id"], [])
        
                # counting wins for team A and B
                vitorias_lista = [m["win"] for m in mapas_da_partida]
                a = vitorias_lista.count("A")
                b = vitorias_lista.count("B")

                matches_descript += f"- {match['camp_id']}: {emoji_a} {a}X{b} {emoji_b}\n"

            #       Embed2          - Creating the description for the embed with the maps in the pool, with win rates for each map and composition of the team

            pool = [{"id": mapa, "nome": self.maps[mapa]["nome"]} for mapa in self.maps if self.maps[mapa]["in_pool"]]
            team_maps = {
                m_id: {
                    **m_info,
                    "comps": [],                # [0, 0, 0, 0, 0]
                    "atk_def/rounds": [],       # "9_4_12_4" -> 9 in attack, 4 in defense, 12 in attack, 4 rounds in defense
                    "Win/game": []              # "5/10" -> 5 wins out of 10 games
                }
                for m_id, m_info in self.maps.items()
            }
            # atk_def/rounds: Clarifying the logic:
                # in 9_4_12_4:
                # 9 rounds won in attack out of 12 rounds played in attack
                # 4 rounds won in defense out of 4 rounds played in defense

            # map of the team's role in each match (A or B) to facilitate the calculation of stats for the second embed
                # A means the team is timeA in that match, B means the team is timeB
                # timeA
            papel_na_partida = {m["id"]: ("A" if m["timeA/B"][0] == time.get("id") else "B") for m in all_matches}

            # for each map played by the team, we will fill the team_maps dict with the compositions used, 
                # the atk/def rounds and the win/game ratio for that composition in that map
            for mapa in all_mapas:
                p_id = mapa["partida_id"]

                ab = papel_na_partida[p_id]
                i = 0 if ab == "A" else 1

                # mapa.get("rounds"): example: AAAAAAAAAAAAXBBBBBBBBBBBBXAA
                    # Team A won 12 rounds in the first half, team B 12 rounds in the second half,
                    # team A closed the match by winning 2 rounds in overtime, 
                    # becoming "TeamB + 2" rounds in rounds won
                starts = "atk" if mapa["atk_start"] == ab else "def"
                total_rounds = mapa.get("rounds")
                partes = total_rounds.split("X")

                half1, half2 = partes[0], partes[1]
                ot = partes[2] if len(partes) > 2 else ""


                otATK, otDEF = 0, 0
                if ot:
                    for j, c in enumerate(ot):
                        if c == ab:
                            # Team played OT first on attack or in defense? Calculating OT rounds won for each side accordingly
                            if (j % 2 == 0 and starts == "atk") or (j % 2 != 0 and starts == "def"):
                                otATK += 1
                            else:
                                otDEF += 1

                # String mentioned before, with format X_Y_Z_W, where each letter is a number
                    # more information above
                if starts == "atk":
                    atk_def = f"{half1.count(ab) + otATK}_{half2.count(ab) + otDEF}_{len(half1) + len(ot)//2}_{len(half2) + len(ot)//2}"
                else:
                    atk_def = f"{half2.count(ab) + otATK}_{half1.count(ab) + otDEF}_{len(half2) + len(ot)//2}_{len(half1) + len(ot)//2}"

                # Getting stats of each composition for the map of this match to fill the team_maps dict
                m_id = mapa["id_mapa"] # Numeric id of map (Ex: 1 for Bind)
                target = team_maps[m_id]
                comp_val = mapa["comps"][i]
                
                # First time seeing this composition?
                if comp_val not in target["comps"]:
                    target["comps"].append(comp_val)
                    target["atk_def/rounds"].append(atk_def)
                    win_val = "1/1" if mapa.get("win") == ab else "0/1"
                    target["Win/game"].append(win_val)
                
                else:
                    index = target["comps"].index(comp_val)

                    # Atk_Def rounds sum
                    result = [int(x) for x in target["atk_def/rounds"][index].split("_")]
                    atk_def_numbers = atk_def.split("_")
                    target["atk_def/rounds"][index] = f"{result[0] + int(atk_def_numbers[0])}_{result[1] + int(atk_def_numbers[1])}_{result[2] + int(atk_def_numbers[2])}_{result[3] + int(atk_def_numbers[3])}"

                    # win/match sum
                    v, g = [int(x) for x in target["Win/game"][index].split("/")]
                    v += 1 if mapa.get("win") == ab else 0
                    target["Win/game"][index] = f"{v}/{g+1}"

            # Putting descriptions together for each map in the pool, with the compositions used by the team and their respective stats
            time_mapas = []
            for map in pool:
                time_mapas.append(team_maps[map["id"]])
            for mapa in time_mapas:
                descricaoMapa = ""
                if mapa.get("comps") == []:
                    descricaoMapa += "Sem composições registradas."
                else:
                    for counter, composicao in enumerate(mapa.get("comps")):
                        for agent in composicao:
                            descricaoMapa += f"{self.agents[agent].get('emoji')} "
                        
                        info1 = [int(a) for a in mapa.get("atk_def/rounds")[counter].split("_")]
                        info2 = [int(a) for a in mapa.get("Win/game")[counter].split("/")]
                        descricaoMapa += f" ATK W% = {(info1[0] / info1[2] if info1[2] > 0 else 0) * 100:.2f}% \|\| DEF W% = {info1[1] / info1[3] * 100:.2f}% \|\| MAP W% = {info2[0] / info2[1] * 100:.2f}%"
                        
                        descricaoMapa += "\n"
                mapa['descricao'] = descricaoMapa
            #      EMBED 3 and 4        - Team Stats last tournament
            # If we don't have the players stats of this team in RAM yet, we load them from the database and store them in RAM for future use. If we already have them in RAM, we just use them.
            if self.players.get(time_id) is None:
                async with await get_conn() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("""
                        SELECT id_player, id_time, id_camp, rating, acs, kd, kast, adr, kpr, apr, fkpr, fdpr, hs, cl 
                        FROM stats_players 
                        WHERE id_time = %s 
                        ORDER by id_camp DESC
                        """, (time["id"],))
                        stats_players = await cur.fetchall()
                
                colunas = ["Player", "Time", "Camp", "Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS", "CL"]

                stats_table = pd.DataFrame(stats_players, columns=colunas)

                # Treating the CL column to separate clutches won and clutches played into different columns, 
                    # converting them to numeric values and dropping the original CL column
                cl_split = stats_table["CL"].str.split("/", expand=True)

                if cl_split.shape[1] == 2:
                    stats_table["CLw"] = pd.to_numeric(cl_split[0], errors='coerce')
                    stats_table["CLp"] = pd.to_numeric(cl_split[1], errors='coerce')
                else:
                    stats_table["CLw"] = 0
                    stats_table["CLp"] = 0

                stats_table = stats_table.drop(columns=["CL"])

                stats_table["KAST"] = pd.to_numeric(stats_table["KAST"], errors='coerce')

                self.players[time_id] = stats_table
            
            # if we already have the stats of this team in RAM, we just use them without querying the database again
            # else:
            #     stats_table = self.players[time_id]

            agg_rules = {
                "Rating": "mean",
                "ACS": "mean",
                "KD": "mean",
                "KAST": "mean",
                "ADR": "mean",
                "KPR": "mean",
                "APR": "mean",
                "FKPR": "mean",
                "FDPR": "mean",
                "HS": "mean",
                "CLw": "sum",
                "CLp": "sum"
            }

            df_time = self.players[time_id].groupby("Camp").agg(agg_rules).reset_index()

            return time, matches_descript, time_mapas, df_time

    async def get(self, var):
        if var == "times":
            return self.times
        elif var == "maps":
            return self.maps
        elif var == "agents":
            return self.agents
        elif var == "comps":
            return self.comps
        elif var == "camps":
            return self.camps
        elif var == "partidas":    
            return self.partidas
        elif var == "mapas_jogados":
            return self.mapas_jogados
        elif var == "players":
            return self.players

async def perform_global_reload(brain : Brain):
    '''
    ## Reloading all data from the database into RAM

    :return: list of dicts (times), dict of dicts (mapas_lista), dict of dicts (agentes), dict of lists (composicoes), dict (campeonatos), list of dicts (partidas), list of dicts (mapas_jogados)
    '''
    try:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                _times = await load_id_times(cur)
                _maps = await load_id_maps(cur)
                _agents = await load_id_agents(cur)
                _comps = await load_id_comps(cur)
                _camps = await load_id_camps(cur)
                _partidas = await load_id_partidas(cur, _camps)
                _mapas_jogados = await load_id_mapas_jogados(cur, _maps, _comps)
        
        brain.update_data((_times, _maps, _agents, _comps, _camps, _partidas, _mapas_jogados))
        return 1
    
    except Exception as e:
        print(f"Erro ao recarregar dados: {e}")
        return 0

if __name__ == "__main__":
    pass