from datetime import datetime, timezone, timedelta
from math import ceil
import pandas as pd
import numpy as np
import asyncio
import psycopg
import json
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass
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
    return {int(id): {"id": id, "nome": nome, "in_pool": in_pool} for id, nome, in_pool in rows}
        
async def load_id_agents(cur):
    await cur.execute("SELECT id, nome, emoji_discord FROM agentes")
    rows = await cur.fetchall()
    return {int(id): {"nome": nome, "emoji": emoji} for id, nome, emoji in rows}

async def load_id_comps(cur):
    await cur.execute("SELECT id, agente1, agente2, agente3, agente4, agente5 FROM composicoes")
    rows = await cur.fetchall()
    return {int(id): [int(agent1), int(agent2), int(agent3), int(agent4), int(agent5)] for id, agent1, agent2, agent3, agent4, agent5 in rows}
        
async def load_id_camps(cur):
    await cur.execute("SELECT id, nome, winner, rated FROM campeonatos ORDER BY id ASC")
    rows = await cur.fetchall()

    camps = {}
    toRate_camps = []

    for id, nome, winner, rated in rows:
        camps[int(id)] = {"nome": nome, "winner": winner}

        if rated is not None:
            if (not rated) and (winner is not None):
                toRate_camps.append(int(id))

    return camps, toRate_camps

async def load_id_partidas(cur, camps_dict, unrated_camps=[]):
    await cur.execute("SELECT id, camp_id, timea_id, timeb_id, vencedor_time_letra, pickban_log, rated, seq_num FROM partidas ORDER BY seq_num DESC")
    rows = await cur.fetchall()
    partidas_cache = []
    toRate_matches = []
    toRate_campMatches = []

    for r in rows:
        if not r[6]:
            toRate_matches.append(r[0])

        if r[1] in unrated_camps:
            toRate_campMatches.append(r[0])

        partidas_cache.append(
            {
                "id": r[0], 
                "camp_id": camps_dict.get(r[1])["nome"], 
                "timeA/B": [r[2], r[3]], 
                "vencedor_time_letra": r[4], 
                "pickban": json.loads(r[5])
            } 
        )

    toRate_matches.reverse()

    return partidas_cache, toRate_matches, toRate_campMatches

async def load_id_mapas_jogados(cur, maps_dict, comps_dict):
    await cur.execute("SELECT id, partida_id, mapa_id, vencedor_mapa, rounds_string, atk_start, compa_id, compb_id FROM mapas_jogados ORDER BY id DESC")
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

async def load_team_table(id_time):
    async with await get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
            SELECT id_player, id_time, id_camp, rating, acs, kd, kast, adr, kpr, apr, fkfd, hs, cl 
            FROM stats_players 
            WHERE id_time = %s 
            ORDER by id_camp DESC
            """, (id_time, ))
            stats_players = await cur.fetchall()
    
    colunas = ["Player", "Time", "Camp", "Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKFD", "HS", "CL"]

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

    return stats_table

async def load_player_map_stats(id_time, pool):
    async with await get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT 
                    pms.player_id, pms.team_id, pms.match_id, pms.map_id, pms.rating, 
                    pms.acs, pms.adr, pms.kast, pms.hs, pms.kd, pms.kda, pms.fk, pms.fd,
                    p.seq_num
                FROM players_map_stats pms
                JOIN partidas p on p.id = pms.match_id
                WHERE pms.team_id = %s
                AND pms.map_id = ANY(%s)
                ORDER by p.seq_num DESC
                """, 
                (id_time, pool)
            )
            stats_players = await cur.fetchall()

    colunas = ["Player", "Team", "Match", "Map", "Rating", "ACS", "ADR", "KAST", "HS", "KD", "KDA", "FK", "FD", "seq_num"]

    stats_table = pd.DataFrame(stats_players, columns=colunas)

    stats_table["KAST"] = pd.to_numeric(stats_table["KAST"], errors='coerce')

    return stats_table

async def load_team_ratings(id_time, curr=None):
    if curr is None:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    WITH ranked_ratings AS (
                        SELECT 
                            team_id,
                            map_id,
                            rating,
                            pickpoints,
                            ROW_NUMBER() OVER (
                                PARTITION BY map_id 
                                ORDER BY rating DESC
                            ) AS rank_pos
                        FROM team_ratings
                    )
                    SELECT 
                        team_id, 
                        map_id, 
                        rating, 
                        pickpoints, 
                        rank_pos
                    FROM ranked_ratings
                    WHERE team_id = %s
                    ORDER BY map_id DESC;
                    """, (id_time, )
                )
                T_ratings = await cur.fetchall()
    else:
        await curr.execute("""
            WITH ranked_ratings AS (
                SELECT 
                    team_id,
                    map_id,
                    rating,
                    pickpoints,
                    ROW_NUMBER() OVER (
                        PARTITION BY map_id 
                        ORDER BY rating DESC
                    ) AS rank_pos
                FROM team_ratings
            )
            SELECT 
                team_id, 
                map_id, 
                rating, 
                pickpoints, 
                rank_pos
            FROM ranked_ratings
            WHERE team_id = %s
            ORDER BY map_id DESC;
            """, (id_time, )
        )
        T_ratings = await curr.fetchall()

    Ratings = {map_id: {"rating": rating, "pickpoints": pickpoints, "pos": rank_pos} for t_id, map_id, rating, pickpoints, rank_pos in T_ratings}

    return Ratings

async def load_leaderboard(map_id, condition):
    if condition is None:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    WITH ranked_leaderboard AS (
                        SELECT 
                            t.tag,
                            t.nome,
                            t.emoji,
                            t.regiao,
                            tr.rating,
                            ROW_NUMBER() OVER (ORDER BY tr.rating DESC) AS posicao
                        FROM team_ratings tr
                        JOIN times t on t.id = tr.team_id
                        WHERE tr.map_id = %s
                    )
                    SELECT posicao, tag, nome, emoji, regiao, rating
                    FROM ranked_leaderboard
                    WHERE posicao <= 10
                    ORDER BY posicao ASC;
                    """, 
                    (map_id, )
                )

                leaderboard = await cur.fetchall()
    elif condition in ["Americas", "China", "EMEA", "APAC"]:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    WITH ranked_leaderboard AS (
                        SELECT 
                            t.tag,
                            t.nome,
                            t.emoji,
                            t.regiao,
                            tr.rating,
                            ROW_NUMBER() OVER (ORDER BY tr.rating DESC) AS posicao
                        FROM team_ratings tr
                        JOIN times t on t.id = tr.team_id
                        WHERE tr.map_id = %s
                    )
                    SELECT posicao, tag, nome, emoji, regiao, rating
                    FROM ranked_leaderboard
                    WHERE LOWER(regiao) = LOWER(%s)
                    ORDER BY posicao ASC;
                    """, 
                    (map_id, condition)
                )
                leaderboard = await cur.fetchall()
    else:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    WITH ranked_leaderboard AS (
                        SELECT
                            t.id AS team_id,
                            t.tag,
                            t.nome,
                            t.emoji,
                            t.regiao,
                            tr.rating,
                            ROW_NUMBER() OVER (ORDER BY tr.rating DESC) AS posicao
                        FROM team_ratings tr
                        JOIN times t on t.id = tr.team_id
                        WHERE tr.map_id = %s
                    )
                    SELECT posicao, tag, nome, emoji, regiao, rating
                    FROM ranked_leaderboard
                    WHERE posicao <= 10
                        OR team_id = %s
                    ORDER BY posicao ASC;
                    """, 
                    (map_id, condition)
                )
                leaderboard = await cur.fetchall()

    LB = [{"posicao": posicao, "tag": tag, "nome": nome, "emoji": emoji, "regiao": regiao, "rating": rating} for posicao, tag, nome, emoji, regiao, rating in leaderboard]

    return LB

def rodar_sync(coroutine):
    """Transform async corroutine in a sync function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    values = loop.run_until_complete(coroutine)
    loop.close()
    return values

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
        self.team_ratings = {}
        self.map_stats = {}
        self.leaderboard = {}

    def update_data(self, cache):
        self.times = cache[0]           # times
        self.maps = cache[1]            # maps
        self.agents = cache[2]          # agents
        self.comps = cache[3]           # comps
        self.camps = cache[4]           # camps
        self.partidas = cache[5]        # partidas
        self.mapas_jogados = cache[6]   # mapas_jogados
        self.players = {}

    async def info_time(self, time_tag, preTable=None, preRating=None, preTeamStats=None):
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
            pool_ids = [map["id"] for map in pool]
            
            team_maps = {
                m_id: {
                    **m_info,
                    "comps": [],                # [0, 0, 0, 0, 0]
                    "atk_def/rounds": [],       # "9_4_12_4" -> 9 in attack, 4 in defense, 12 in attack, 4 rounds in defense
                    "Win/game": [],             # "5/10" -> 5 wins out of 10 games
                    "info": {
                        "atk_": [0, 0],
                        "def_": [0, 0],
                        "map_": [0, 0],
                        "pistol": [0, 0],
                        "post_W_pistol": [0, 0],
                        "post_L_pistol": [0, 0],
                        "played": 0
                    },
                    "comp_played": []
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

                # Calculating pistol related information
                # pistol, post win pistol, post lose pistol
                pistol, pWp, pLp = 0, 0, 0
                # count post wins, count post lose
                count_pW, count_pL = 0, 0

                if half1[0] == ab:
                    pistol += 1
                    count_pW += 1
                    if half1[1] == ab: 
                        pWp += 1
                else:
                    count_pL += 1
                    if half1[1] == ab:
                        pLp += 1
                if half2[0] == ab:
                    pistol += 1
                    if len(half2) != 1:
                        count_pW += 1
                        if half2[1] == ab:
                            pWp += 1
                else:
                    if len(half2) != 1:
                        count_pL += 1
                        if half2[1] == ab:
                            pLp += 1
                        
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
                    target["comp_played"].append(1)
                    target["info"]["played"] += 1
                
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
                    target["comp_played"][index] += 1
                    target["info"]["played"] += 1

                # Pistol related
                target["info"]["pistol"][0] += pistol
                target["info"]["post_W_pistol"][0] += pWp
                target["info"]["post_L_pistol"][0] += pLp

                target["info"]["pistol"][1] += 2
                target["info"]["post_W_pistol"][1] += count_pW
                target["info"]["post_L_pistol"][1] += count_pL

            # Putting descriptions together for each map in the pool, with the compositions used by the team and their respective stats
            time_mapas = []
            for map in pool_ids:
                time_mapas.append(team_maps[map])
            for mapa in time_mapas:
                descricaoMapa = ""

                if mapa.get("comps") == []:
                    descricaoMapa += "Sem composições registradas."
                else:
                    for counter, composicao in enumerate(mapa.get("comps")):
                        for agent in composicao:
                            descricaoMapa += f"{self.agents[agent].get('emoji')} "
                        descricaoMapa += "|"
                        info1 = [int(a) for a in mapa.get("atk_def/rounds")[counter].split("_")]
                        info2 = [int(a) for a in mapa.get("Win/game")[counter].split("/")]
                        
                        mapa['info']['atk_'][0] += info1[0]
                        mapa['info']['atk_'][1] += info1[2]
                        mapa['info']['def_'][0] += info1[1]
                        mapa['info']['def_'][1] += info1[3]
                        mapa['info']['map_'][0] += info2[0]
                        mapa['info']['map_'][1] += info2[1]

                        descricaoMapa += f"Jogado {mapa['comp_played'][counter]} vezes|ATK W% = {(info1[0] / info1[2] if info1[2] > 0 else 0) * 100:.2f}%|DEF W% = {info1[1] / info1[3] * 100:.2f}%|MAP W% = {info2[0] / info2[1] * 100:.2f}%"
                        
                        descricaoMapa += "\n"
                mapa['descricao'] = descricaoMapa

            #      EMBED 3 and 4        - Team Stats last tournament
            # If we don't have the players stats of this team in RAM yet, we load them from the database and store them in RAM for future use. If we already have them in RAM, we just use them.
            if self.players.get(time_id) is None:
                if preTable is not None and preTable is not pd.DataFrame.empty:
                    stats_table = preTable
                else:
                    stats_table = await load_team_table(time_id)

                self.players[time_id] = stats_table

            if self.team_ratings.get(time_id) is None:
                if preRating is not None:
                    ratings = preRating
                else:
                    ratings = await load_team_ratings(time_id)

                self.team_ratings[time_id] = ratings

            if self.map_stats.get(time_id) is None:
                if preTeamStats is not None and preTeamStats is not pd.DataFrame.empty:
                    map_stats = preTeamStats
                else:
                    map_stats = await load_player_map_stats(time_id, pool_ids)

                self.map_stats[time_id] = map_stats

            # if we already have the stats of this team in RAM, we just use them without querying the database again

            agg_rules_table = {
                "Rating": "mean",
                "ACS": "mean",
                "KD": "mean",
                "KAST": "mean",
                "ADR": "mean",
                "KPR": "mean",
                "APR": "mean",
                "FKFD": "mean",
                "HS": "mean",
                "CLw": "sum",
                "CLp": "sum"
            }

            df_time = self.players[time_id].groupby("Camp").agg(agg_rules_table).reset_index()

            # Using weighted_mean to have more accurate stats for each map:
            LAMBDA = 0.1 # how match past loses weight
            Stats_cols = ["Rating", "ACS", "ADR", "KAST", "HS", "KD", "KDA", "FK", "FD"]

            df_temp = self.map_stats[time_id].sort_values(by=["Map", "seq_num"], ascending=True)

            df_temp["games_ago"] = (
                df_temp.groupby("Map")["seq_num"]
                       .rank(method="dense", ascending=False) - 1
            )

            df_temp["weight"] = np.exp(-LAMBDA * df_temp["games_ago"])

            for col in Stats_cols:
                df_temp[col] = pd.to_numeric(df_temp[col], errors="coerce").fillna(0.0)

            weighted_df = df_temp[Stats_cols].multiply(df_temp["weight"], axis=0)

            weighted_df["Map"] = df_temp["Map"]
            weighted_df["weight"] = df_temp["weight"]

            grouped = weighted_df.groupby("Map").sum()


            df_maps = grouped[Stats_cols].divide(grouped["weight"], axis=0).reset_index()

            return time, matches_descript, time_mapas, df_time, df_maps, self.team_ratings[time_id]

    async def get_leaderboard(self, map, condition, preLB=None):
        if self.leaderboard.get((map, condition)) is None:
            if preLB is not None:
                lb = preLB
            else:
                lb = await load_leaderboard(map, condition)

            self.leaderboard[(map, condition)] = lb

        return self.leaderboard[(map, condition)]

    async def rate_camp(self, unrated_campMatches, unrated_camps):
        if not unrated_campMatches:
            print("Rate_camp: No matches found. Returning...")
            return
        matches = [p for p in self.partidas if p["id"] in unrated_campMatches]

        regioes = ["Americas", "EMEA", "China", "APAC"]
        regiao_wins = {regiao: 0 for regiao in regioes}
        top_3 = []

        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                for match in matches:
                    times = match["timeA/B"]
                    count = 0
                    for time in self.times:
                        if time["id"] in times:
                            times[times.index(time["id"])] = {"id": time["id"], "regiao": time["regiao"]}
                            count += 1
                            if count == 2:
                                break

                    vencedor = ["A", "B"].index(match["vencedor_time_letra"])

                    if times[0]["regiao"] != times[1]["regiao"]: # regional matches doesn't represent a region superiority
                        wins = regiao_wins.get(times[vencedor]["regiao"], 0)
                        regiao_wins[times[vencedor]["regiao"]] = wins + 1

                    pickban = match["pickban"]

                    lenAbans = len(pickban.get('Abans', []))
                    lenBbans = len(pickban.get('Bbans', []))
                    len_bans = lenAbans + lenBbans

                    md5 = True if len_bans == 2 else False # Best of 5

                    if md5:
                        if lenAbans in [0, 2]: # Grand Final
                            # Insert to make sure that the order will be correct no matter what
                            top_3.insert(0, times[vencedor]["id"]) # First place = index 0
                            top_3.insert(1, times[(vencedor + 1) % 2]["id"]) # Second place = index 1
                        else:
                            top_3.insert(2, times[(vencedor + 1) % 2]["id"]) # Third place = index 2

                posicoes_pts = [40, 10, -10, -40]

                reg_posicoes = sorted(regiao_wins.items(), key=lambda item: item[1], reverse=True)

                if reg_posicoes[0][1] == reg_posicoes[3][1]:
                    posicoes_pts = [0, 0, 0, 0]
                elif reg_posicoes[0][1] == reg_posicoes[2][1]:
                    posicoes_pts = [13, 13, 13, -40]
                elif reg_posicoes[1][1] == reg_posicoes[3][1]:
                    posicoes_pts = [40, -13, -13, -13]
                else:
                    for i in range(3):
                        if reg_posicoes[i][1] == reg_posicoes[i+1][1]:
                            valor = (posicoes_pts[i] + posicoes_pts[i+1]) // 2
                            posicoes_pts[i] = valor
                            posicoes_pts[i+1] = valor

                for i, (regiao, wins) in enumerate(reg_posicoes):
                    if posicoes_pts[i] != 0:
                        await cur.execute("""
                            UPDATE team_ratings AS tr
                            SET rating = tr.rating + %s
                            FROM times AS t
                            WHERE tr.team_id = t.id
                            AND t.regiao = %s
                            AND tr.map_id = 0;
                        """, (posicoes_pts[i], regiao))

                if len(top_3) == 3:
                    f_id, s_id, t_id = top_3

                    await cur.execute("""
                        UPDATE team_ratings AS tr
                        SET rating = tr.rating + v.bonus
                        FROM (VALUES
                            (%s::integer, 80),
                            (%s::integer, 40),
                            (%s::integer, 10)
                        ) AS v(team_id, bonus)
                        WHERE tr.team_id = v.team_id
                        AND tr.map_id = 0;
                    """, (f_id, s_id, t_id))
                else:
                    print(f"Aviso: Top 3 incompleto ou mal formado. Encontraos {len(top_3)} times.")

                await cur.execute("""
                    UPDATE campeonatos
                    SET rated = TRUE
                    WHERE id = ANY(%s)
                """, (unrated_camps, ))

                await conn.commit()

    async def rate_matches(self, unrated_matches):
        if not unrated_matches:
            print("rate_matches: No matches found. Returning...")
            return
        # FOR TESTS:
        #unrated_matches = unrated_matches[:1]
        matches = [p for p in self.partidas if p["id"] in unrated_matches]
        matches.reverse()

        mapas = {id: {} for id in unrated_matches}

        for m in self.mapas_jogados:
            if m["partida_id"] in unrated_matches:
                mapas[m["partida_id"]][m["id_mapa"]] = m

        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                for match in matches:
                    timeA, timeB = match["timeA/B"]
                    vencedor = match["vencedor_time_letra"]

                    pickban = match["pickban"]
                    starter = pickban["First"]
                    pickban.pop("First")

                    pickpts_updt = [] # What we need to change in pickpoints

                    lenAbans = len(pickban.get('Abans', []))
                    lenBbans = len(pickban.get('Bbans', []))
                    len_bans = lenAbans + lenBbans

                    md5 = True if len_bans == 2 else False # Is the match a BO5?
                    
                    if starter == "A":
                        ### BANS
                            # A Session
                        pickpts_updt.append((timeA, pickban['Abans'][0], -4))

                        if lenAbans == 2:
                            if md5:
                                pickpts_updt.append((timeA, pickban['Abans'][1], -3))
                            else:
                                pickpts_updt.append((timeA, pickban['Abans'][1], -2))
                                pickpts_updt.append((timeA, pickban["Bbans"][1], +1))
                                pickpts_updt.append((timeA, pickban['decider'], +1))

                            # B Session
                        if lenBbans == 2:
                            pickpts_updt.append((timeB, pickban['Bbans'][0], -3))
                            pickpts_updt.append((timeB, pickban['Bbans'][1], -1))
                            pickpts_updt.append((timeB, pickban['decider'], +1))
                        elif lenBbans == 1:
                            pickpts_updt.append((timeB, pickban['Bbans'][0], -3))

                        ### PICKS
                        pickpts_updt.append((timeA, pickban['Apicks'][0], +3))
                        pickpts_updt.append((timeB, pickban['Bpicks'][0], +2))

                        if md5:
                            pickpts_updt.append((timeA, pickban['Apicks'][1], +2))
                            pickpts_updt.append((timeB, pickban['Bpicks'][1], +1))

                    else:
                        ### BANS
                            # B Session
                        pickpts_updt.append((timeB, pickban['Bbans'][0], -4))

                        if lenBbans == 2:
                            if md5:
                                pickpts_updt.append((timeB, pickban['Bbans'][1], -3))
                            else:
                                pickpts_updt.append((timeB, pickban['Bbans'][1], -2))
                                pickpts_updt.append((timeB, pickban["Abans"][1], +1))
                                pickpts_updt.append((timeB, pickban['decider'], +1))

                            # A Session
                        if lenAbans == 2:
                            pickpts_updt.append((timeA, pickban['Abans'][0], -3))
                            pickpts_updt.append((timeA, pickban['Abans'][1], -1))
                            pickpts_updt.append((timeA, pickban['decider'], +1))
                        elif lenAbans == 1:
                            pickpts_updt.append((timeA, pickban['Abans'][0], -3))

                        ### PICKS
                        pickpts_updt.append((timeB, pickban['Bpicks'][0], +3))
                        pickpts_updt.append((timeA, pickban['Apicks'][0], +2))

                        if md5:
                            pickpts_updt.append((timeB, pickban['Bpicks'][1], +2))
                            pickpts_updt.append((timeA, pickban['Apicks'][1], +1))

                    ratings_A = await load_team_ratings(timeA, curr=cur)
                    ratings_B = await load_team_ratings(timeB, curr=cur)

                    match_maps = mapas[match["id"]]

                    rating_updt = []

                    qnt_mapas = len(match_maps)

                    for m_id in match_maps:
                        m_venc = match_maps[m_id]["win"]

                        rounds = match_maps[m_id]["rounds"]

                        rounds_a = rounds.count("A")
                        rounds_b = rounds.count("B")

                        rate_A = ratings_A.get(m_id, {"rating": 1000})
                        rate_B = ratings_B.get(m_id, {"rating": 1000})

                        if m_venc == "A":
                            venc = timeA
                            perd = timeB

                            R_winner = rate_A["rating"]
                            R_loser = rate_B["rating"]
                            rnd_winner = rounds_a
                            rnd_loser = rounds_b
                        else:
                            venc = timeB
                            perd = timeA

                            R_winner = rate_B["rating"]
                            R_loser = rate_A["rating"]
                            rnd_winner = rounds_b
                            rnd_loser = rounds_a
                        

                        rnd_diff = (rnd_winner-rnd_loser)
                        if rnd_diff < 5: # 0 -> 4 = 1.0x
                            rnd_mult = 1
                        elif rnd_diff < 11: # 5 -> 10 = 1.1x -> 1.3x
                            rnd_mult = 1 + (ceil((rnd_diff - 4)/2) * 0.1)
                        else: # 11 -> 13 = 1.5x
                            rnd_mult = 1.5

                        base_delta = max(5, 20 + 0.1 * (R_loser - R_winner))
                        delta = round(base_delta * rnd_mult)

                        if m_venc == "A":
                            ratings_A[m_id] = {"rating": (rate_A["rating"] +delta)}
                            ratings_B[m_id] = {"rating": (rate_B["rating"] -delta)}
                        else:
                            ratings_A[m_id] = {"rating": (rate_A["rating"] -delta)}
                            ratings_B[m_id] = {"rating": (rate_B["rating"] +delta)}

                        rating_updt.append((venc, m_id, R_winner+delta))
                        rating_updt.append((perd, m_id, R_loser-delta))

                    # General team Rating
                    rate_A = ratings_A.get(0, {"rating": 1000, "pickpoints": 0})
                    rate_B = ratings_B.get(0, {"rating": 1000, "pickpoints": 0})

                    if vencedor == "A":
                        venc = timeA
                        perd = timeB

                        R_winner = rate_A["rating"]
                        R_loser = rate_B["rating"]
                    else:
                        venc = timeB
                        perd = timeA

                        R_winner = rate_B["rating"]
                        R_loser = rate_A["rating"]

                    if md5:
                        if qnt_mapas >= 5:      # 3x2
                            match_mult = 1.2
                        elif qnt_mapas == 4:    # 3x1
                            match_mult = 1.35
                        else:                   # 3x0
                            match_mult = 1.5
                    else:
                        match_mult = 1.2 if (qnt_mapas == 3) else 1.5 # 2x1 vs 2x0

                    base_delta = max(5, 20 + 0.1 * (R_loser - R_winner))
                    delta = round(base_delta * match_mult)

                    if m_venc == "A":
                        ratings_A[0] = {"rating": (rate_A["rating"] +delta)}
                        ratings_B[0] = {"rating": (rate_B["rating"] -delta)}
                    else:
                        ratings_A[0] = {"rating": (rate_A["rating"] -delta)}
                        ratings_B[0] = {"rating": (rate_B["rating"] +delta)}

                    rating_updt.append((venc, 0, R_winner+delta))
                    rating_updt.append((perd, 0, R_loser-delta))

                    for updt in pickpts_updt:
                        await cur.execute("""
                            INSERT INTO team_ratings (team_id, map_id, pickpoints)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (team_id, map_id)
                            DO UPDATE SET
                                pickpoints = team_ratings.pickpoints + EXCLUDED.pickpoints
                        """, updt)

                    for updt in rating_updt:
                        await cur.execute("""
                            INSERT INTO team_ratings (team_id, map_id, rating)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (team_id, map_id)
                            DO UPDATE SET
                                rating = EXCLUDED.rating
                        """, updt)

                await cur.execute("""
                    UPDATE partidas
                    SET rated = TRUE
                    WHERE id = ANY(%s);
                """, (unrated_matches,))

        return

    async def get_value(self, var):
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
    ## Reloading all data from the database into RAM (saving into the brain instance)

    :return: 1 if successful, 0 if there was an error
    '''
    try:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                _times = await load_id_times(cur)
                _maps = await load_id_maps(cur)
                _agents = await load_id_agents(cur)
                _comps = await load_id_comps(cur)
                _camps, unrated_camps = await load_id_camps(cur)
                _partidas, unrated_matches, unrated_campMatches = await load_id_partidas(cur, _camps, unrated_camps)
                _mapas_jogados = await load_id_mapas_jogados(cur, _maps, _comps)
        
        brain.update_data((_times, _maps, _agents, _comps, _camps, _partidas, _mapas_jogados))

        await brain.rate_matches(unrated_matches)
        await brain.rate_camp(unrated_campMatches, unrated_camps)
        return 1
    
    except Exception as e:
        print(f"Erro ao recarregar dados: {e}")
        return 0
    
async def site_data_reload():
    '''
    ## Reloading all data from the database into RAM

    :return: tuple ( list of dicts (times), dict of dicts (mapas_lista), dict of dicts (agentes), dict of lists (composicoes), dict (campeonatos), list of dicts (partidas), list of dicts (mapas_jogados) )
    '''
    try:
        async with await get_conn() as conn:
            async with conn.cursor() as cur:
                _times = await load_id_times(cur)
                _maps = await load_id_maps(cur)
                _agents = await load_id_agents(cur)
                _comps = await load_id_comps(cur)
                _camps, unrated_camps = await load_id_camps(cur)
                _partidas, unrated_matches, unrated_campMatches = await load_id_partidas(cur, _camps)
                _mapas_jogados = await load_id_mapas_jogados(cur, _maps, _comps)
        
        return (_times, _maps, _agents, _comps, _camps, _partidas, _mapas_jogados)
    
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None
    
def discover_reload_site():
    """
    Generate a unique string for the current timestamp.
    String changes as 7:30 UTC and 19:30 UTC.
    """
    agora = datetime.now(timezone.utc)
    
    reset_1 = agora.replace(hour=7, minute=30, second=0, microsecond=0)
    reset_2 = agora.replace(hour=19, minute=30, second=0, microsecond=0)
    
    # Discovers the current time window
    if agora < reset_1:
        # Early morning: curent window started 19:30 UTC of yesterday.
        janela_origem = reset_2 - timedelta(days=1)
    elif agora < reset_2:
        # Morning/Afternoon: current window started 7:30 UTC of today
        janela_origem = reset_1
    else:
        # Night:curent window started 19:30 UTC of today.
        janela_origem = reset_2
        
    # Example of the string returned: "vlr_window_2026-07-02_07:30"
    return f"vlr_window_{janela_origem.strftime('%Y-%m-%d_%H:%M')}"

if __name__ == "__main__":
    pass
