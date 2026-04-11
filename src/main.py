from datetime import time, timezone
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import tasks
import disc_buttons
import asyncio
import psycopg
import discord
import logging 
import os
import json

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
filename = str(os.path.join("discord.log"))

handler = logging.FileHandler(filename=filename, encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# SERVER DE USO DE COMANDOS VISUAIS
GUILD_ID_INFO = discord.Object(id=int(os.getenv('GUILD_ID')))
CREATOR_ID = int(os.getenv('CREATOR_ID'))
DB_URL = os.getenv("DATABASE_URL")

# setting auto_reload time to 6:10 UTC, which is 3:10 in Brazil, right after the VLR updates their database with the new matches of the day
target_time = time(hour=6, minute=10, tzinfo=timezone.utc)

# Inicializando globais
times = []
maps = {}
agents = {}
comps = {}
camps = {}
partidas = []
mapas_jogados = []

players = {} # unused

# DB functions
def get_conn():
        return psycopg.connect(DB_URL)

def load_id_times():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tag, emoji, regiao, nome, img_url FROM times WHERE id != 0 ORDER BY regiao, tag")
            return [{"id": int(id), "tag": tag, "emoji": emoji, "regiao": regiao, "nome": nome, "img_url": img_url} for id, tag, emoji, regiao, nome, img_url in cur.fetchall()]

def load_id_maps():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome, in_pool FROM mapas_lista")
            return {int(id): {"nome": nome, "in_pool": in_pool} for id, nome, in_pool in cur.fetchall()}
        
def load_id_agents():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome, emoji_discord FROM agentes")
            return {int(id): {"nome": nome, "emoji": emoji} for id, nome, emoji in cur.fetchall()}

def load_id_comps():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, agente1, agente2, agente3, agente4, agente5 FROM composicoes")
            return {int(id): [int(agent1), int(agent2), int(agent3), int(agent4), int(agent5)] for id, agent1, agent2, agent3, agent4, agent5 in cur.fetchall()}
        
def load_id_camps():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome FROM campeonatos")
            return {int(id): nome for id, nome in cur.fetchall()}

def load_id_partidas():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, camp_id, timea_id, timeb_id, vencedor_time_letra, pickban_log FROM partidas")
            partidas_cache = [
                {"id": r[0], "camp_id": camps.get(r[1]), "timeA/B": [r[2], r[3]], "vencedor_time_letra": r[4], "pickban": json.loads(r[5])} 
                for r in cur.fetchall()
            ] 
    return partidas_cache

def load_id_mapas_jogados():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, partida_id, mapa_id, vencedor_mapa, rounds_string, atk_start, compa_id, compb_id FROM mapas_jogados")
            mapas_jogados_cache = [
                {
                    "id": r[0], "partida_id": r[1],"id_mapa": r[2], "nome": maps[r[2]]["nome"], 
                    "win": r[3], "rounds": r[4], "atk_start": r[5],
                    "comps": [comps.get(r[6]), comps.get(r[7])]
                }
                for r in cur.fetchall()
            ]
    return mapas_jogados_cache

def perform_global_reload():
    print("Recarregando dados do banco para a RAM...")
    global times, maps, agents, comps, camps, partidas, mapas_jogados
    times = load_id_times()
    maps = load_id_maps()
    agents = load_id_agents()
    comps = load_id_comps()
    camps = load_id_camps()
    partidas = load_id_partidas()
    mapas_jogados = load_id_mapas_jogados()    
    print("Dados recarregados com sucesso!")

# Events
@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    perform_global_reload() # Carrega os dados do banco para a RAM quando o bot inicia

    try:

        guild = GUILD_ID_INFO
        synced = await bot.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands to guild {guild.id}')

    except Exception as e:
        print(f'Error syncing commands: {e}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

# COMANDOS
'''
                                            INFO_LOADERS 
'''

@bot.tree.command(name="update_cache", description="Força o reload dos dados", guild=GUILD_ID_INFO)
async def update_cache(interaction: discord.Interaction):
    if interaction.user.id != CREATOR_ID:
        return await interaction.response.send_message("Apenas o desenvolvedor pode usar isso.", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True) # Resposta visível só para você
    
    perform_global_reload()
    
    await interaction.edit_original_response(content="Cache atualizado com sucesso!", ephemeral=True)

@tasks.loop(time=target_time)
async def auto_reload_db():
    print("Executando reload agendado pós-GitHub Actions...")
    await asyncio.to_thread(perform_global_reload)


    print("Banco recarregado automaticamente após atualização do GitHub.")

'''
                                            CRIAÇÃO DE INFORMAÇÃO 
'''
@bot.tree.command(name="help_times", description="Tags de pesquisa de time", guild=GUILD_ID_INFO)
async def auxilio(interaction: discord.Interaction):

    if not times:
        await interaction.response.send_message("Erro ao carregar os times.", ephemeral=False)
        return
    
    answer = "\n"

    pre_region = ""
    for team in times:
        if team["regiao"] != pre_region:
            answer += "\n" 
        answer += f"{team['emoji']} {team['tag']}, "
        pre_region = team["regiao"]    
    await interaction.response.send_message(f"Times disponíveis para info_time: {answer}", ephemeral=False)

@bot.tree.command(name="info_time", description="Informação sobre um time", guild=GUILD_ID_INFO)
async def printer(interaction: discord.Interaction, time_query: str):
    # Creating the embed

    await interaction.response.defer(ephemeral=False)

    if not times:
        await interaction.edit_original_response("Erro ao carregar o time.", ephemeral=True)
        return
    
    for team in times:
        if time_query.lower() in [team["tag"].lower(), team["nome"].lower()]:
            time = team
            break

    if type(time) == dict:
        embedIndex = 0
        embedList = []

        #   CRIANDO EMBED PÁGINA 1
        # Definindo descrição
        descricao = f"Time da: {time.get('regiao')} \n"
        
        embed = discord.Embed(title=time.get("tag"),
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))

        for player in players:
            player_descript = " __Ranks:__ㅤㅤㅤㅤ\n"
            if player.get("time") == time.get("TIME_ID"):
                for key in player.get("rank"):   
                    player_descript += f"{key}: {player['rank'][key]}\n"

                embed.add_field(name=f"{player.get('nome')}", value=f"{player_descript}")

        embed.set_thumbnail(url=time.get("img_url"))

        # Pegamos o ID do time que você já encontrou na busca por nome/tag
        time_id = time.get("id")

        # Filtramos a lista 'partidas' (que já está na RAM) 
        # Substitui o SELECT ... WHERE timea_id = %s OR timeb_id = %s
        all_matches = [ p for p in partidas if time_id in p["timeA/B"] ]

        # (Opcional) Como o SQL tinha um ORDER BY id, garantimos que a lista esteja ordenada
        all_matches.sort(key=lambda x: x["id"])

        team_partidas5 = all_matches[-5:]

        # 2. Cria a lista de IDs para o próximo filtro
        # (Dica: usamos 'set' aqui para a busca ser instantânea no próximo passo)
        ids_partidas_filtradas = {p["id"] for p in all_matches}
        ids_ultimas_5 = {p["id"] for p in team_partidas5}

        # 3. Filtra os mapas dessas partidas (o "Funil" nível 2)
        # Em vez de ir no banco, ele varre a lista que já está na RAM
        all_mapas = []
        mapas_5 = {}
        for m in mapas_jogados:
            p_id = m["partida_id"]
            if p_id in ids_partidas_filtradas:
                all_mapas.append(m)
            if p_id in ids_ultimas_5:
                if p_id not in mapas_5:
                    mapas_5[p_id] = []
                mapas_5[p_id].append({"win": m["win"]})

        matches_decript = ""

        emoji_map = {t['id']: t['emoji'] for t in times}

        for match in team_partidas5:
            timeAB = match["timeA/B"][:]
            a = 0
            b = 0
            emoji_a = emoji_map.get(timeAB[0], "❓") 
            emoji_b = emoji_map.get(timeAB[1], "❓")

            mapas_da_partida = mapas_5.get(match["id"], [])
    
            # Conta vitórias de A e B de forma elegante
            vitorias_lista = [m["win"] for m in mapas_da_partida]
            a = vitorias_lista.count("A")
            b = vitorias_lista.count("B")

            matches_decript += f"{match['camp_id']}: {emoji_a} {a}X{b} {emoji_b}\n"

        embed.add_field(name="Partidas", value=f"{matches_decript}", inline=False)

        # Setting the footer
        embed.set_footer(text="Informações tiradas do VLR.")

        #   CRIANDO EMBED PÁGINA 2 
                
        pool = [{"id": mapa, "nome": maps[mapa]["nome"]} for mapa in maps if maps[mapa]["in_pool"]]
        team_maps = {
            m_id: {
                **m_info,
                "comps": [],                # [0, 0, 0, 0, 0]
                "atk_def/rounds": [],       # "9_4_12_4" -> 9 no ataque, 4 na defesa, 12 no ataque, 4 rounds na defesa
                "Win/game": []              # "5/10" -> 5 vitórias de 10 jogadas
            }
            for m_id, m_info in maps.items()
        }

        papel_na_partida = {m["id"]: ("A" if m["timeA/B"][0] == time.get("id") else "B") for m in all_matches}

        for mapa in all_mapas:
            p_id = mapa["partida_id"]

            ab = papel_na_partida[p_id]
            i = 0 if ab == "A" else 1

            starts = "atk" if mapa["atk_start"] == ab else "def"
            total_rounds = mapa.get("rounds")
            partes = total_rounds.split("X")

            half1, half2 = partes[0], partes[1]
            ot = partes[2] if len(partes) > 2 else ""

            otATK, otDEF = 0, 0
            if ot:
                for j, c in enumerate(ot):
                    if c == ab:
                        # Lógica de inversão de lados no OT
                        if (j % 2 == 0 and starts == "atk") or (j % 2 != 0 and starts == "def"):
                            otATK += 1
                        else:
                            otDEF += 1

            if starts == "atk":
                atk_def = f"{half1.count(ab) + otATK}_{half2.count(ab) + otDEF}_{len(half1) + len(ot)//2}_{len(half2) + len(ot)//2}"
            else:
                atk_def = f"{half2.count(ab) + otATK}_{half1.count(ab) + otDEF}_{len(half2) + len(ot)//2}_{len(half1) + len(ot)//2}"

            # salvando no team_maps para usar na construção do embed depois
            m_id = mapa["id_mapa"] # ID numérico do mapa (Ex: 1 para Bind)
            target = team_maps[m_id]
            minha_comp = mapa["comps"][i]

            
            if minha_comp not in target["comps"]:
                target["comps"].append(minha_comp)
                target["atk_def/rounds"].append(atk_def)
                win_val = "1/1" if mapa.get("win") == ab else "0/1"
                target["Win/game"].append(win_val)
            
            else:
                index = target["comps"].index(minha_comp)

                # Soma rounds Atk_Def
                result = [int(x) for x in target["atk_def/rounds"][index].split("_")]
                atk_def_numbers = atk_def.split("_")
                target["atk_def/rounds"][index] = f"{result[0] + int(atk_def_numbers[0])}_{result[1] + int(atk_def_numbers[1])}_{result[2] + int(atk_def_numbers[2])}_{result[3] + int(atk_def_numbers[3])}"

                # Soma vitórias/jogos
                v, g = [int(x) for x in target["Win/game"][index].split("/")]
                v += 1 if mapa.get("win") == ab else 0
                target["Win/game"][index] = f"{v}/{g+1}"


        embed2 = discord.Embed(title=time.get("tag") + "- Mapas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))

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
                        descricaoMapa += f"{agents[agent].get('emoji')} "
                    
                    info1 = [int(a) for a in mapa.get("atk_def/rounds")[counter].split("_")]
                    info2 = [int(a) for a in mapa.get("Win/game")[counter].split("/")]
                    descricaoMapa += f" ATK W% = {(info1[0] / info1[2]) * 100:.2f}% \|\| DEF W% = {info1[1] / info1[3] * 100:.2f}% \|\| MAP W% = {info2[0] / info2[1] * 100:.2f}%"
                    
                    descricaoMapa += "\n"
            
            embed2.add_field(name=f"{mapa['nome']}", value=descricaoMapa, inline=False)

        embedList.append(embed)
        embedList.append(embed2)

        await interaction.edit_original_response(embed=embedList[embedIndex], view=disc_buttons.EmbedChangePage(embedList, embedIndex))
    else:
        await interaction.followup.send("Erro ao carregar o time.", ephemeral=True)







bot.run(token, log_handler=handler, log_level=logging.DEBUG)