import discord
from discord.ext import commands
from discord import app_commands
import logging 
from dotenv import load_dotenv
import os

import new_api_handler as nah
import disc_buttons

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
filename = str(os.path.join("VLRBOT", "discord.log"))

handler = logging.FileHandler(filename=filename, encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# SERVER DE ALTERAÇÃO DE ARQUIVOS
GUILD_ID_JSON = discord.Object(id=477253210717814804)
# SERVER DE USO DE COMANDOS VISUAIS
GUILD_ID_INFO = discord.Object(id=1368770575098449951)
CREATOR_ID = 580541885555408899

Regiao = ''

times = [False, '', '']

composicoes = [False]

partida = [False]
mapas = [1]

md = 0

ppickban = [False]

campeonato = ""


# Loading
indice = nah.carregar_indice()
times = nah.get_dados(indice, "times")
players = nah.get_dados(indice, "players")
# Events

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

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
    
    answer = ""

    for i, team in enumerate(times):
        if (i % 12) == 0:
            answer += "\n"
        answer += f"{team.get('emoji')} {team.get('tag')}, "
    await interaction.response.send_message(f"Times disponíveis para info_time: {answer}", ephemeral=False)

@bot.tree.command(name="info_time", description="Informação sobre um time", guild=GUILD_ID_INFO)
async def printer(interaction: discord.Interaction, time: str):
    # Creating the embed

    await interaction.response.defer(ephemeral=False)

    if not times:
        await interaction.edit_original_response("Erro ao carregar o time.", ephemeral=True)
        return
    
    for team in times:
        if time.lower() in [team.get("nome").lower(), team.get("tag").lower()]:
            time = team
            break
    
    if type(time) == dict:
        embedIndex = 0
        embedList = []

        #   CRIANDO EMBED PÁGINA 1
        # Definindo descrição
        descricao = ""
        descricao += team.get("regiao") + ": top " + str(team.get("posicao")) + "\n"
        
        embed = discord.Embed(title=time.get("tag"),
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))

        for player in players:
            player_descript = " __Ranks:__ㅤㅤㅤㅤ\n"
            if player.get("time") == time.get("TIME_ID"):
                for key in player.get("rank"):   
                    player_descript += f"{key}: {player['rank'][key]}\n"

                embed.add_field(name=f"{player.get('nome')}", value=f"{player_descript}")

        embed.set_thumbnail(url=time.get("img"))

        partidas = time.get("partidas")[-5:]
        matches = nah.get_dados(indice, "partidas")
        matches_decript = ""


        for match in partidas:
            timeAB = matches[match - 1].get('timeA/B')[:]
            a = 0
            b = 0
            for team in times:
                if team.get('TIME_ID') == timeAB[0]:
                    timeAB[0] = team.get("emoji")
                elif team.get('TIME_ID') == timeAB[1]:
                    timeAB[1] = team.get("emoji")

            for mapa in matches[match - 1].get("mapas"):
                if mapa.get("win") == "A":
                    a += 1
                else:
                    b += 1

            matches_decript += matches[match - 1].get("camp") + ":  " + timeAB[0] + f" {a}X{b} " + timeAB[1] + "\n"

        embed.add_field(name="Partidas", value=f"{matches_decript}", inline=False)

        # Setting the footer
        embed.set_footer(text="Informações tiradas do VLR.")
        
        #   CRIANDO EMBED PÁGINA 2 
        all_matches = time.get("partidas")[:]
        all_mapas = nah.get_dados(indice, "mapas")
        pool = indice.get("mapas").get("pool")

        agentes = nah.get_dados(indice, "agents")
 
        for mapa in all_mapas:
            mapa["composicoes"] = []    # [0, 0, 0, 0, 0]
            mapa["atk_def/rounds"] = []        # "9_4_12_4" -> 9 no ataque, 4 na defesa, 12 no ataque, 4 rounds na defesa
            mapa["Win/game"] = []       # "5/10" -> 5 vitórias de 10 jogadas

        for match in all_matches:
            i = matches[match - 1]["timeA/B"].index(time.get("TIME_ID"))

            for mapa in matches[match - 1].get("mapas"):
                if i == 0:
                    ab = "A"
                else:
                    ab = "B"

                if mapa.get("atk") == ab:
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

                if mapa.get('composicoes')[i] not in all_mapas[mapa.get('id') - 1]["composicoes"]:
                    all_mapas[mapa.get("id") - 1]["composicoes"].append(mapa.get("composicoes")[i])
                    all_mapas[mapa.get("id") - 1]["atk_def/rounds"].append(atk_def)

                    if mapa.get("win") == ["A", "B"][i]:
                        all_mapas[mapa.get("id") - 1]["Win/game"].append(f'1/1')
                    else:
                        all_mapas[mapa.get("id") - 1]["Win/game"].append(f'0/1')
                
                else:
                    index = all_mapas[mapa.get('id') - 1]["composicoes"].index(mapa.get('composicoes')[i])

                    result = [int(a) for a in all_mapas[mapa.get("id") - 1]["atk_def/rounds"][index].split("_")]
                    atk_def_numbers = atk_def.split("_")

                    all_mapas[mapa.get("id") - 1]["atk_def/rounds"][index] = f"{result[0] + int(atk_def_numbers[0])}_{result[1] + int(atk_def_numbers[1])}_{result[2] + int(atk_def_numbers[2])}_{result[3] + int(atk_def_numbers[3])}"

                    result = [int(a) for a in all_mapas[mapa.get("id") - 1]["Win/game"][index].split("/")]

                    if mapa.get("win") == ["A", "B"][i]:
                        all_mapas[mapa.get("id") - 1]["Win/game"][index] = f"{result[0] + 1}/{result[1] + 1}"
                    else:
                        all_mapas[mapa.get("id") - 1]["Win/game"][index] = f"{result[0]}/{result[1] + 1}"


        embed2 = discord.Embed(title=time.get("tag") + "- Mapas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))

        time_mapas = []
        for map in pool:
            time_mapas.append(all_mapas[map-1])
        for mapa in time_mapas:
            descricaoMapa = ""
            if mapa.get("composicoes") == []:
                descricaoMapa += "Sem composições registradas."
            else:
                for counter, composicao in enumerate(mapa.get("composicoes")):
                    for agent in composicao:
                        descricaoMapa += f"{agentes[agent - 1].get('img')} "
                    
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