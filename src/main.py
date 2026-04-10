from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import tasks
import disc_buttons
import datetime
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

# SERVER DE ALTERAÇÃO DE ARQUIVOS
GUILD_ID_JSON = discord.Object(id=int(os.getenv('GUILD_ID_JSON')))
# SERVER DE USO DE COMANDOS VISUAIS
GUILD_ID_INFO = discord.Object(id=int(os.getenv('GUILD_ID_INFO')))
CREATOR_ID = int(os.getenv('CREATOR_ID'))
DB_URL = os.getenv("DATABASE_URL")


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
            cur.execute("SELECT id, nome FROM times")
            return {int(id): nome for id, nome in cur.fetchall()}



# Loading
times = load_id_times()
maps = load_id_maps()
agents = load_id_agents()
comps = load_id_comps()
camps = load_id_camps()


players = {}
# Events       

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    auto_reload_db.start()

    try:
        guild = discord.Object(id=477253210717814804)
        synced = await bot.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands to guild {guild.id}')

        guild2 = discord.Object(id=1368770575098449951)
        synced = await bot.tree.sync(guild=guild2)
        print(f'Synced {len(synced)} commands to guild {guild2.id}')

    except Exception as e:
        print(f'Error syncing commands: {e}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

# COMANDOS
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

@bot.tree.command(name="update_cache", description="Recarrega o cache de times, mapas, agentes e composições")
async def update_cache(interaction: discord.Interaction):
    if interaction.user.id != CREATOR_ID:
        return await interaction.response.send_message("Sem permissão.")
    
    await interaction.response.defer()
    # Recarrega as globais
    global times, maps, agents, comps, camps
    times = load_id_times()
    maps = load_id_maps()
    agents = load_id_agents()
    comps = load_id_comps()
    camps = load_id_camps()

    await interaction.edit_original_response(content="Cache atualizado com sucesso!")

@tasks.loop(time=datetime.time(hour=3, minute=10))
async def auto_reload_db():
    global times, maps
    times = load_id_times()
    maps = load_id_maps()
    print("Banco recarregado automaticamente após atualização do GitHub.")

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

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, camp_id, timea_id, timeb_id, pickban_log, vencedor_time_letra FROM partidas WHERE timea_id = %s OR timeb_id = %s ORDER BY id",
                             (time.get("id"), time.get("id")))
                all_matches = [
                        {"id": id, 
                        "camp": camps.get(camp_id), 
                        "timeA/B": [timea_id, timeb_id], 
                        "pickban_log": pickban_log, 
                        "vencedor_time_letra": vencedor_time_letra
                        } for id, camp_id, timea_id, timeb_id, pickban_log, vencedor_time_letra in cur.fetchall()
                    ]

        partidas = all_matches[-5:]
        matches_decript = ""

        for match in partidas:
            timeAB = match.get("timeA/B")[:]
            a = 0
            b = 0
            for team in times:
                if team.get('id') == timeAB[0]:
                    timeAB[0] = team.get("emoji")
                elif team.get('id') == timeAB[1]:
                    timeAB[1] = team.get("emoji")

            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, vencedor_mapa FROM mapas_jogados WHERE partida_id = %s ORDER BY id", (match.get("id"),))
                    all_mapas = [
                            { 
                            "win": vencedor_mapa
                            } for id, vencedor_mapa in cur.fetchall()
                        ]

            for mapa in all_mapas:
                if mapa.get("win") == "A":
                    a += 1
                else:
                    b += 1

            matches_decript += match.get("camp") + ":  " + timeAB[0] + f" {a}X{b} " + timeAB[1] + "\n"

        embed.add_field(name="Partidas", value=f"{matches_decript}", inline=False)

        print("OLÁ")

        # Setting the footer
        embed.set_footer(text="Informações tiradas do VLR.")
        
        #   CRIANDO EMBED PÁGINA 2 
        with get_conn() as conn:
            with conn.cursor() as cur:  
                cur.execute("SELECT mapa_id, atk_start, compa_id, compb_id, rounds_string, vencedor_mapa FROM mapas_jogados WHERE timea_id = %s OR timeb_id = %s ORDER BY id",
                             (time.get("id"), time.get("id")))
                all_mapas = [
                        {"id": maps[mapa_id]["nome"], 
                         "atk_start": atk_start, 
                         "comps": [comps.get(compa_id), comps.get(compb_id)], 
                         "rounds": rounds_string, 
                         "vencedor_mapa": vencedor_mapa
                        } for mapa_id, atk_start, compa_id, compb_id, rounds_string, vencedor_mapa in cur.fetchall()
                    ]
                
        pool = [{id: mapa, "nome": maps[mapa]["nome"]} for mapa in maps if maps[mapa]["in_pool"]]
        team_maps = {
            m_id: {
                **m_info,
                "comps": [],                # [0, 0, 0, 0, 0]
                "atk_def/rounds": [],       # "9_4_12_4" -> 9 no ataque, 4 na defesa, 12 no ataque, 4 rounds na defesa
                "Win/game": []              # "5/10" -> 5 vitórias de 10 jogadas
            }
            for m_id, m_info in maps.items()
        }

        for match in all_matches:
            i = match["timeA/B"].index(time.get("id"))

            for mapa in all_mapas:
                if i == 0:
                    ab = "A"
                else:
                    ab = "B"

                if mapa.get("atk_start") == ab:
                    starts = "atk"
                else:
                    starts = "def"

                total_rounds = mapa.get("rounds")
                X_count = total_rounds.count("X")

                if X_count == 1:
                    half1, half2 = total_rounds.split("X")
                    ot = ""
                elif X_count == 2:
                    half1, half2, ot = total_rounds.split("X")

                otATK = 0
                otDEF = 0

                for j, c in enumerate(ot):
                    if c == ab:
                        if j % 2 == 0:
                            if starts == "atk":
                                otATK += 1
                            else:
                                otDEF += 1
                        else:
                            if starts == "atk":
                                otDEF += 1
                            else:
                                otATK += 1

                if starts == "atk":
                    atk_def = f"{half1.count(ab) + otATK}_{half2.count(ab) + otDEF}_{len(half1) + len(ot)//2}_{len(half2) + len(ot)//2}"
                else:
                    atk_def = f"{half2.count(ab) + otATK}_{half1.count(ab) + otDEF}_{len(half2) + len(ot)//2}_{len(half1) + len(ot)//2}"

                if mapa.get('comps')[i] not in team_maps[mapa["id"]]["comps"]:
                    team_maps[mapa.get("id")]["comps"].append(mapa.get("comps")[i])
                    team_maps[mapa.get("id")]["atk_def/rounds"].append(atk_def)

                    if mapa.get("win") == ["A", "B"][i]:
                        team_maps[mapa.get("id")]["Win/game"].append(f'1/1')
                    else:
                        team_maps[mapa.get("id")]["Win/game"].append(f'0/1')
                
                else:
                    index = team_maps[mapa.get('id')]["comps"].index(mapa.get('comps')[i])

                    result = [int(a) for a in team_maps[mapa.get("id")]["atk_def/rounds"][index].split("_")]
                    atk_def_numbers = atk_def.split("_")

                    team_maps[mapa.get("id")]["atk_def/rounds"][index] = f"{result[0] + int(atk_def_numbers[0])}_{result[1] + int(atk_def_numbers[1])}_{result[2] + int(atk_def_numbers[2])}_{result[3] + int(atk_def_numbers[3])}"

                    result = [int(a) for a in team_maps[mapa.get("id")]["Win/game"][index].split("/")]

                    if mapa.get("win") == ["A", "B"][i]:
                        team_maps[mapa.get("id")]["Win/game"][index] = f"{result[0] + 1}/{result[1] + 1}"
                    else:
                        team_maps[mapa.get("id")]["Win/game"][index] = f"{result[0]}/{result[1] + 1}"


        embed2 = discord.Embed(title=time.get("tag") + "- Mapas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))

        time_mapas = []
        for map in pool:
            time_mapas.append(team_maps[map["nome"]])
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
            
            embed2.add_field(name=f"{mapa.get('nome')}", value=descricaoMapa, inline=False)

        embedList.append(embed)
        embedList.append(embed2)

        await interaction.edit_original_response(embed=embedList[embedIndex], view=disc_buttons.EmbedChangePage(embedList, embedIndex))
    else:
        await interaction.followup.send("Erro ao carregar o time.", ephemeral=True)







bot.run(token, log_handler=handler, log_level=logging.DEBUG)