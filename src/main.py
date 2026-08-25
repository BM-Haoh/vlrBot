from datetime import time, timezone
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import tasks
import disc_buttons as disB
from typing import Optional
import pandas as pd
import asyncio
import discord
import logging 
import brain
import sys
import os

# alterando a política do loop de eventos
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
filename = str(os.path.join("discord.log"))

handler = logging.FileHandler(filename=filename, encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# SERVER DE TESTES + COMANDOS EXCLUSIVOS
GUILD_ID_INFO = discord.Object(id=int(os.getenv('GUILD_ID')))
CREATOR_ID = int(os.getenv('CREATOR_ID'))

# auto_reload roda diariamente às 7:30 UTC (4:30 em Brasília) e às 19:30 UTC (16:30 em Brasília), pós web scraping no github actions
target_time = [
    time(hour=7, minute=30, tzinfo=timezone.utc),
    time(hour=19, minute=30, tzinfo=timezone.utc)
    ]

# Inicializando globais
logic = brain.Brain([], {}, {}, {}, {}, [], [])

# Função de reload
async def perform_global_reload(logic : brain.Brain):
    print("Recarregando dados do banco para a RAM...")

    if (await brain.perform_global_reload(logic)):
        print("Dados recarregados com sucesso!")
        return 1
    else:
        print(f"Erro durante o reload.")
        return 0


# Inicialização do bot
@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    await perform_global_reload(logic) # Carrega os dados do banco para a RAM quando o bot inicia

    try:
        # Sincronizando comandos de testes:
        guild = GUILD_ID_INFO

        if not auto_reload_cache.is_running():
            auto_reload_cache.start()

        guild_synced = await bot.tree.sync(guild=guild)
        print(f'Synced {len(guild_synced)} commands to guild {guild.id}.')

        # Sincronizando comandos globais:
        global_synced = await bot.tree.sync()
        print(f'Synced {len(global_synced)} commands to global.')

    except Exception as e:
        print(f'Error syncing commands: {e}')


# COMANDOS
'''
                                            INFO_LOADERS 
'''



'''
                                            COMANDO            #0 
'''
@bot.tree.command(name="update_cache", description="Força o reload dos dados", guild=GUILD_ID_INFO) # Comando exclusivo do dono, por isso exclusivo do server de testes tbm
@app_commands.check(lambda inst: inst.user.id == CREATOR_ID)
async def update_cache(interaction: discord.Interaction):
    '''
    Command that forces the reload of the data from the database to the RAM. Useful for testing. Restrict to the creator.
    '''
    
    await interaction.response.defer(ephemeral=True)

    if (await perform_global_reload(logic)):
        await interaction.followup.send(content="Cache atualizado com sucesso!", ephemeral=True)
    else:
        await interaction.followup.send(content="Erro ao atualizar o cache.", ephemeral=True)

@tasks.loop(time=target_time)
async def auto_reload_cache():
    '''
    Automatic reload scheduled for 7:30 UTC daily.
    '''
    print("Executando reload agendado pós-GitHub Actions...")

    if (await perform_global_reload(logic)):
        print("Banco recarregado automaticamente após atualização do GitHub.")
    else:
        print("Falha no reload agendado.")

'''
                                            CRIAÇÃO DE INFORMAÇÃO 
'''
'''
                                            COMANDO            #1
'''
@bot.tree.command(name="help_times", description="Tags de pesquisa de time")

async def auxilio(interaction: discord.Interaction):
    '''
    command that lists the tags of the teams for search, separated by region, and with the respective emojis.
    useful for the user to know how to write the team tag when asked for it in other commands.
    '''
    times = await logic.get_value("times")

    if not times:
        await interaction.response.send_message("Erro ao carregar os times.", ephemeral=False)
        return
    
    await interaction.response.defer(ephemeral=False)
    
    answer = discord.Embed(title="Tags de Pesquisa de Time", 
                           description="Comandos que pedem entrada de times aceitam:\n - Nome completo do time\n - Tag do time (como as a seguir)", 
                           color=discord.Colour(0x1ABC9C))

    temp_answer = ""
    pre_region = times[0]["regiao"] # inicializa com a região do primeiro time para evitar erro de comparação no primeiro loop
    field_count = 0  

    for team in times:
        if team["regiao"] != pre_region:
            if field_count == 2:
                answer.add_field(name="\u200b", value="\u200b", inline=False) # field vazio para espaçamento e separação
            answer.add_field(name=f"**__{pre_region}__**", value=temp_answer, inline=True)
            field_count += 1
            temp_answer = ""
        temp_answer += f"{team['emoji']} {team['tag']}\n"
        pre_region = team["regiao"]    

    answer.add_field(name=f"**__{pre_region}__**", value=temp_answer, inline=True) # ultima região

    await interaction.edit_original_response(embed=answer)
async def team_query_autocomplete(
        interaction: discord.Interaction,
        current: str
) -> list[app_commands.Choice[str]]:
    opcoes = [] # tags
    opcoes2 = [] # nomes
    for time in logic.times:
        tag, nome = time["tag"], time["nome"]
        opcoes2.append((tag, tag))
        if tag != nome:
            opcoes2.append((nome, tag))
    opcoes.extend(opcoes2) # tags na frente de nomes
    opcoes_filtradas = [
        opcao for opcao in opcoes
        if current.lower() in opcao[0].lower()
    ][:15]
    return [
        app_commands.Choice(name=nome, value=str(valor))
        for nome, valor in opcoes_filtradas
    ]
'''
                                            COMANDO            #2
'''
@bot.tree.command(name="info_time", description="Informação sobre um time")
@app_commands.describe(
    team_query="Nome/Tag do time que deseja ver as informações sobre.",
)
@app_commands.autocomplete(team_query=team_query_autocomplete)
async def info_time(interaction: discord.Interaction, time_query: str):
    '''
    command that provides information about a team.
    '''
    await interaction.response.defer(ephemeral=False)
    
    # Devido poucos casos de acentuação nos nomes/tags dos times, hardocode para resolução
    if time_query.lower() in ["kru esports", "kru"]:
        time_query = "krü"
    elif time_query.lower() in ["leviatan"]:
        time_query = "leviatán"

    res = await logic.info_time(time_query)

    if res == 1:
        await interaction.edit_original_response("Erro ao carregar o time.", ephemeral=True)
        return
    
    if res == 2:
        await interaction.edit_original_response("Time não encontrado. Use /help_times para ver as tags de pesquisa.", ephemeral=True)
        return
    

    time, matches_decript, time_mapas, time_stats, time_map_stats, time_ratings = res

    if type(time) == dict:
        embedList = []

        # EMBED 0 - Glossário

        embed0 = discord.Embed(title=f"{time['tag']} Embed Book",
                            description=f"# Escolha uma página para visualizar",
                            color=discord.Colour(0x1ABC9C))
        
        embed0.set_thumbnail(url=time['img_url'])

        embed0.add_field(name="Página 1: Overview",
                         value="Informações gerais do time, contendo:\n- Estatísticas do último campeonato\n- Win rates gerais\n- Últimas 5 partidas do time",
                         inline=True)
        embed0.add_field(name="Páginas de 2 a 8: Mapas",
                         value="Informações sobre o time em cada mapa, contendo:\n- Composições do time\n- Taxa de vitória no ataque\n- Taxa de vitória da defesa\n- Taxa de vitória no mapa",
                         inline=True)
        embed0.add_field(name="Página 9: Estatísticas",
                         value="Estatísticas do time historicamente, contendo:\n- Média das tabelas de estatísticas de cada campeonato do VCT para o time.",
                         inline=True)
        
        embed0.set_footer(text='Glossário do "Livro" de Embeds')

        # Descricao Geral dos embeds:
        trophies = "\n"
        Trophies = "\n━━━━━━━━━━━━━━━━━━━━━━\n### :trophy: \n"
        count = 0
        for camp in logic.camps.keys():
            if logic.camps[camp].get("winner") is not None:
                if logic.camps[camp]["winner"] == time["id"]:
                    count += 1
                    Trophies += f"{logic.camps[camp]['nome']}\n"

        Trophies = Trophies if count else trophies

        numbers = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
        top_spots = ["0", ":first_place:", ':second_place:', ":third_place:"]

        regiao = f"{time['regiao']}'s team" if time['regiao'] != '?' else "Team from Unknown region"
        
        # Stats do Embed 1
        colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKFD", "HS"]
        idx_mais_recente = time_stats["Camp"].idxmax()
        stats_recente = time_stats.loc[idx_mais_recente]
        mapas_jogados_geral = 0
        Atk_geral = [0, 0] # [vitórias, total]
        Def_geral = [0, 0] # [vitórias, total]
        Map_geral = [0, 0] # [vitórias, total]
  
        pistol_geral  = [0, 0]
        pWp_geral     = [0, 0]
        pLp_geral     = [0, 0]

        win = "\u2588\u200a"
        lose = "\u2591\u200a"

        # EMBED 2->8 - Mapas
        pool = []
        for mapa in time_mapas:
            pool.append(mapa["nome"])

            mapas_jogados_geral += mapa["info"]["played"]
            Atk_geral[0] += mapa['info']['atk_'][0]
            Atk_geral[1] += mapa['info']['atk_'][1]
            Def_geral[0] += mapa['info']['def_'][0]
            Def_geral[1] += mapa['info']['def_'][1]
            Map_geral[0] += mapa['info']['map_'][0]
            Map_geral[1] += mapa['info']['map_'][1]

            pistol_geral[0] += mapa['info']["pistol"][0]
            pistol_geral[1] += mapa['info']["pistol"][1]
            pWp_geral[0]    += mapa['info']["post_W_pistol"][0]
            pWp_geral[1]    += mapa['info']["post_W_pistol"][1]
            pLp_geral[0]    += mapa['info']["post_L_pistol"][0]
            pLp_geral[1]    += mapa['info']["post_L_pistol"][1]

            
            mapa_jogado = mapa["info"]["played"]
            Atk = mapa['info']['atk_'][0] / mapa['info']['atk_'][1] if mapa['info']['atk_'][1] > 0 else 0
            Def = mapa['info']['def_'][0] / mapa['info']['def_'][1] if mapa['info']['def_'][1] > 0 else 0
            Map = mapa['info']['map_'][0] / mapa['info']['map_'][1] if mapa['info']['map_'][1] > 0 else 0
            Atk_emoji = win * int(Atk * 10) + lose * (10 - int(Atk * 10))
            Def_emoji = win * int(Def * 10) + lose * (10 - int(Def * 10))
            Map_emoji = win * int(Map * 10) + lose * (10 - int(Map * 10))

            pistol = mapa['info']["pistol"][0] / mapa['info']["pistol"][1] if mapa['info']["pistol"][1] > 0 else 0
            pWp    = mapa['info']["post_W_pistol"][0] / mapa['info']["post_W_pistol"][1] if mapa['info']["post_W_pistol"][1] > 0 else 0
            pLp    = mapa['info']["post_L_pistol"][0] / mapa['info']["post_L_pistol"][1] if mapa['info']["post_L_pistol"][1] > 0 else 0
            pistol_emoji   = win * int(pistol * 10) + lose * (10 - int(pistol * 10))
            pWp_emoji      = win * int(pWp * 10) + lose * (10 - int(pWp * 10))
            pLp_emoji      = win * int(pLp * 10) + lose * (10 - int(pLp * 10))

            # Descrição - MAPAS
            rating_geral = time_ratings.get(mapa["id"])
            str_rating_geral = str(rating_geral.get('rating'))
            rating_pos = rating_geral.get("pos")
            
            rating_number = ""
            for c in str_rating_geral:
                rating_number += numbers[int(c)]
    
            leadearboard_pos = top_spots[rating_pos] if rating_pos < 4 else f"{rating_pos}º"
    
            descricao = f"{regiao}\n## Rating do Mapa: \n### {leadearboard_pos}: {rating_number}"
            
            embedMapa = discord.Embed(title=f"{time.get('tag')} - {mapa['nome']}",
                            description=f"{descricao}",
                            color=discord.Colour(0x1ABC9C))

            embedMapa.set_thumbnail(url=time['img_url'])

            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", 
                                value=f"**__Stats do Mapa:__**", 
                                inline=False)

            stats_mapa = time_map_stats[time_map_stats["Map"] == mapa["id"]]

            if not stats_mapa.empty:
                fk = 0
                fd = 0
                for coluna, valor in stats_mapa.iloc[0].items():
                    if coluna == "Map":
                        continue
                    if coluna in ["KAST", "HS"]:
                        embedMapa.add_field(name=coluna, value=f"{valor*100:.2f}%", inline=True)
                    elif coluna == "FK":
                        fk = valor
                    elif coluna == "FD" and fk != 0:
                        fd = valor
                        if fd != 0:
                            value = fk / fd
                            embedMapa.add_field(name="FKFD", value=f"{value:.2f}", inline=True)
                    else:
                        embedMapa.add_field(name=coluna, value=f"{valor:.2f}", inline=True)
            else:
                embedMapa.add_field(name="Sem estatísticas", value=f"---", inline=False)


            value = f"Mapa jogado {mapa_jogado} vezes\n- Taxa de vitória no ataque: {Atk * 100:.2f}%\n  - {Atk_emoji}\n- Taxa de vitória na defesa: {Def * 100:.2f}%\n  - {Def_emoji}\n- Taxa de vitória geral no mapa: {Map * 100:.2f}%\n  - {Map_emoji}\n- Taxa de vitória de pistols: {pistol * 100:.2f}%\n  - {pistol_emoji}\n- Taxa de vitória pós-vitória no pistol: {pWp * 100:.2f}%\n  - {pWp_emoji}\n- Taxa de vitória pós-derrota no pistol: {pLp * 100:.2f}%\n  - {pLp_emoji}"
            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", 
                                value=f"**__Informações Gerais:__**\n{value}", 
                                inline=False)

            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                                value=f"**__Composições:__**", 
                                inline=False)

            composicoes = mapa["descricao"][:-1].split("\n") # [:-1] para remover a última quebra de linha
            for comp in composicoes[:3]:
                infos = comp.split("|")
                name = infos[0]
                value = ""
                if len(infos) > 1:
                    value += f"{infos[1]}\n"
                    for info in infos[2:]:
                        value += f"- {info}\n"
                else:
                    name = comp
                    value = "\u200b"
                    
                embedMapa.add_field(name=name, value=value, inline=True)

            embedMapa.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")
            embedList.append(embedMapa)

        # Descrição - EMBEDS 1 e 9
        rating_geral = time_ratings.get(0)
        str_rating_geral = str(rating_geral.get('rating'))
        rating_pos = rating_geral.get("pos")
        
        rating_number = ""
        for c in str_rating_geral:
            rating_number += numbers[int(c)]

        leadearboard_pos = top_spots[rating_pos] if rating_pos < 4 else f"{rating_pos}º"

        descricao = f"{regiao}\n## Rating Geral: \n### {leadearboard_pos}: {rating_number}{Trophies}"

        # EMBED 1 - Overview
        embed1 = discord.Embed(title=f"{time['tag']}",
                            description=f"{descricao}",
                            color=discord.Colour(0x1ABC9C))

        embed1.set_thumbnail(url=time['img_url'])

        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", 
                         value=f"**__Stats do último Campeonato:__**", 
                         inline=False)

        # Stats último camp
        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                embed1.add_field(name=coluna, value=f"{stats_recente[coluna]*100:.2f}%", inline=True)
            else:
                embed1.add_field(name=coluna, value=f"{stats_recente[coluna]:.2f}", inline=True)
        embed1.add_field(name="Clutches", value=f"{stats_recente['CLw']}/{stats_recente['CLp']}", inline=True)


        # Infos gerais de win rate
        value = f"Mapas jogados: {mapas_jogados_geral}\n"
        Atk_ = Atk_geral[0]/Atk_geral[1] if Atk_geral[1] > 0 else 0
        Atk_emoji = win * int(Atk_ * 10) + lose * (10 - int(Atk_ * 10))
        Def_ = Def_geral[0]/Def_geral[1] if Def_geral[1] > 0 else 0
        Def_emoji = win * int(Def_ * 10) + lose * (10 - int(Def_ * 10))
        Map_ = Map_geral[0]/Map_geral[1] if Map_geral[1] > 0 else 0
        Map_emoji = win * int(Map_ * 10) + lose * (10 - int(Map_ * 10))

        pistol_ = pistol_geral[0]/pistol_geral[1] if pistol_geral[1] > 0 else 0
        pistol_emoji = win * int(pistol_ * 10) + lose * (10 - int(pistol_ * 10))
        pWp_ = pWp_geral[0]/pWp_geral[1] if pWp_geral[1] > 0 else 0
        pWp_emoji = win * int(pWp_ * 10) + lose * (10 - int(pWp_ * 10))
        pLp_ = pLp_geral[0]/pLp_geral[1] if pLp_geral[1] > 0 else 0
        pLp_emoji = win * int(pLp_ * 10) + lose * (10 - int(pLp_ * 10))
        
        value += f"- ATK W%: ({Atk_*100:.2f}%)\n{Atk_emoji}\n- DEF W%: ({Def_*100:.2f}%)\n{Def_emoji}\n- MAP W%: ({Map_*100:.2f}%)\n{Map_emoji}\n- Pistol W% ({pistol_*100:.2f}%)\n{pistol_emoji}\n- PostWin Pistol W% ({pWp_*100:.2f}%)\n{pWp_emoji}\n- PostLoss Pistol W% ({pLp_*100:.2f}%)\n{pLp_emoji}"
        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", 
                         value=f"**__Informações Gerais:__**\n{value}", 
                         inline=False)

        # Partidas recentes
        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", 
                         value=f"**__Últimas Partidas:__**\n{matches_decript}", 
                         inline=False)

        embed1.set_footer(text="Informações tiradas do VLR.")

       

        # Embed 9 - Estatísticas históricas
        embed3 = discord.Embed(title=time.get("tag") + " - Estatísticas Históricas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))

        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                embed3.add_field(name=coluna, value=f"{time_stats[coluna].mean()*100:.2f}%", inline=True)
            else:
                embed3.add_field(name=coluna, value=f"{time_stats[coluna].mean():.2f}", inline=True)
        embed3.add_field(name="Clutches", value=f"{time_stats['CLw'].sum()}/{time_stats['CLp'].sum()}", inline=True)

        embed3.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")

        embedList.insert(0, embed1)
        embedList.append(embed3)

        await interaction.edit_original_response(embed=embed0, view=disB.MenuView(embedList, pool))
    else:
        await interaction.followup.send("Erro ao carregar o time.", ephemeral=True)

'''
                                            COMANDO            #3
'''
@bot.tree.command(name="times_vs", description="Comparações diretas entre dois times (Este comando costuma demorar um pouco.)")
@app_commands.describe(
    team_query_1="Nome/Tag do time que você deseja ver as informações sobre.",
    team_query_2="Nome/Tag do time que você deseja comparar com o primeiro."
)
@app_commands.autocomplete(team_query_1=team_query_autocomplete, team_query_2=team_query_autocomplete)
async def times_vs(interaction: discord.Interaction, time_query_1: str, time_query_2: str):
    '''
    command that provides information about a team.
    '''
    await interaction.response.defer(ephemeral=False)

    # Devido poucos casos de acentuação nos nomes/tags dos times, hardocode para resolução
    if time_query_1.lower() in ["kru esports", "kru"]:
        time_query_1 = "krü"
    elif time_query_1.lower() in ["leviatan"]:
        time_query_1 = "leviatán"

    if time_query_2.lower() in ["kru esports", "kru"]:
        time_query_2 = "krü"
    elif time_query_2.lower() in ["leviatan"]:
        time_query_2 = "leviatán"

    res1 = await logic.info_time(time_query_1)
    res2 = await logic.info_time(time_query_2)

    if res1 == 1 or res2 == 1:
        await interaction.edit_original_response("Erro ao carregar um dos times.", ephemeral=True)
        return
    
    if res1 == 2:
        await interaction.edit_original_response("O primeiro time não foi encontrado. Use /help_times para ver as tags de pesquisa.", ephemeral=True)
        return
    if res2 == 2:
        await interaction.edit_original_response("O segundo time não foi encontrado. Use /help_times para ver as tags de pesquisa.", ephemeral=True)
        return
    

    time1, matches_decript1, time_mapas1, time_stats1, time_map_stats1, time_ratings1 = res1
    time2, matches_decript2, time_mapas2, time_stats2, time_map_stats2, time_ratings2 = res2

    if type(time1) == dict and type(time2) == dict:
        embedList = []

        # MENSAGEM INICIAL - INSTRUÇÃO
        mensagem = f"Times {time1.get('emoji')} ({time1.get('tag')}) e {time2.get('emoji')} ({time2.get('tag')}) selecionados.\nEscolha a map pool para comparação:"
        descricao = f"{time1['regiao']} x {time2['regiao']}\n"

        # EMBED 0 - Glossário

        embed0 = discord.Embed(title=f"Versus Embed Book: {time1.get('tag')} x {time2.get('tag')}",
                            description=f"# Escolha uma página para visualizar",
                            color=discord.Colour(0x1ABC9C))

        embed0.add_field(name="Primeira página: Overview",
                         value="Informações gerais dos times, contendo:\n- Estatísticas do último campeonato\n- Win rates gerais",
                         inline=True)
        embed0.add_field(name="Páginas intermediárias: Mapas",
                         value="Informações sobre os times em cada mapa, contendo:\n- Última composição utilizada\n- Taxa de vitória no ataque\n- Taxa de vitória da defesa\n- Taxa de vitória no mapa",
                         inline=True)
        embed0.add_field(name="Última página: Estatísticas",
                         value="Estatísticas dos times historicamente, contendo:\n- Média das tabelas de estatísticas de cada campeonato do VCT para cada time.",
                         inline=True)
        
        embed0.set_footer(text='Glossário do "Livro" de Embeds')

        # Descricao Geral dos embeds:
        Trophies_count1 = 0
        Trophies_count2 = 0
        for camp in logic.camps.keys():
            if logic.camps[camp].get("winner") is not None:
                if logic.camps[camp]["winner"] == time1["id"]:
                    Trophies_count1 += 1
                elif logic.camps[camp]["winner"] == time2["id"]:
                    Trophies_count2 += 1

        numbers = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
        top_spots = ["0", ":first_place:", ':second_place:', ":third_place:"]
        
        # Stats do Embed 1
        colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKFD", "HS"]

        # Informações para criação do embed: Sessão time 1
        idx_mais_recente1 = time_stats1["Camp"].idxmax()
        stats_recente1 = time_stats1.loc[idx_mais_recente1]
        mapas_jogados_geral1 = 0
        Atk_geral1 = [0, 0] # [vitórias, total]
        Def_geral1 = [0, 0] # [vitórias, total]
        Map_geral1 = [0, 0] # [vitórias, total]

        pistol_geral1  = [0, 0]
        pWp_geral1     = [0, 0]
        pLp_geral1     = [0, 0]

        # Informações para criação do embed: Sessão time 2
        idx_mais_recente2 = time_stats2["Camp"].idxmax()
        stats_recente2 = time_stats2.loc[idx_mais_recente2]
        mapas_jogados_geral2 = 0
        Atk_geral2 = [0, 0]
        Def_geral2 = [0, 0]
        Map_geral2 = [0, 0]

        pistol_geral2  = [0, 0]
        pWp_geral2     = [0, 0]
        pLp_geral2     = [0, 0]

        win = "\u2588\u200a"
        lose = "\u2591\u200a"

        # EMBED 2->8 - Mapas
        pool = []
        for mapa1, mapa2 in zip(time_mapas1, time_mapas2):
            pool.append(mapa1["nome"])

            # Sessão time 1
            mapas_jogados_geral1 += mapa1["info"]["played"]
            Atk_geral1[0] += mapa1['info']['atk_'][0]
            Atk_geral1[1] += mapa1['info']['atk_'][1]
            Def_geral1[0] += mapa1['info']['def_'][0]
            Def_geral1[1] += mapa1['info']['def_'][1]
            Map_geral1[0] += mapa1['info']['map_'][0]
            Map_geral1[1] += mapa1['info']['map_'][1]

            pistol_geral1[0] += mapa1['info']["pistol"][0]
            pistol_geral1[1] += mapa1['info']["pistol"][1]
            pWp_geral1[0]    += mapa1['info']["post_W_pistol"][0]
            pWp_geral1[1]    += mapa1['info']["post_W_pistol"][1]
            pLp_geral1[0]    += mapa1['info']["post_L_pistol"][0]
            pLp_geral1[1]    += mapa1['info']["post_L_pistol"][1]

            # Sessão time 2
            mapas_jogados_geral2 += mapa2["info"]["played"]
            Atk_geral2[0] += mapa2['info']['atk_'][0]
            Atk_geral2[1] += mapa2['info']['atk_'][1]
            Def_geral2[0] += mapa2['info']['def_'][0]
            Def_geral2[1] += mapa2['info']['def_'][1]
            Map_geral2[0] += mapa2['info']['map_'][0]
            Map_geral2[1] += mapa2['info']['map_'][1]

            pistol_geral2[0] += mapa2['info']["pistol"][0]
            pistol_geral2[1] += mapa2['info']["pistol"][1]
            pWp_geral2[0]    += mapa2['info']["post_W_pistol"][0]
            pWp_geral2[1]    += mapa2['info']["post_W_pistol"][1]
            pLp_geral2[0]    += mapa2['info']["post_L_pistol"][0]
            pLp_geral2[1]    += mapa2['info']["post_L_pistol"][1]

            # Sessão time 1
            mapa_jogado1 = mapa1["info"]["played"]
            Atk1 = mapa1['info']['atk_'][0] / mapa1['info']['atk_'][1] if mapa1['info']['atk_'][1] > 0 else 0
            Def1 = mapa1['info']['def_'][0] / mapa1['info']['def_'][1] if mapa1['info']['def_'][1] > 0 else 0
            Map1 = mapa1['info']['map_'][0] / mapa1['info']['map_'][1] if mapa1['info']['map_'][1] > 0 else 0
            Atk_emoji1 = win * int(Atk1 * 10) + lose * (10 - int(Atk1 * 10))
            Def_emoji1 = win * int(Def1 * 10) + lose * (10 - int(Def1 * 10))
            Map_emoji1 = win * int(Map1 * 10) + lose * (10 - int(Map1 * 10))

            pistol1 = mapa1['info']["pistol"][0] / mapa1['info']["pistol"][1] if mapa1['info']["pistol"][1] > 0 else 0
            pWp1    = mapa1['info']["post_W_pistol"][0] / mapa1['info']["post_W_pistol"][1] if mapa1['info']["post_W_pistol"][1] > 0 else 0
            pLp1    = mapa1['info']["post_L_pistol"][0] / mapa1['info']["post_L_pistol"][1] if mapa1['info']["post_L_pistol"][1] > 0 else 0
            pistol_emoji1   = win * int(pistol1 * 10) + lose * (10 - int(pistol1 * 10))
            pWp_emoji1      = win * int(pWp1 * 10) + lose * (10 - int(pWp1 * 10))
            pLp_emoji1      = win * int(pLp1 * 10) + lose * (10 - int(pLp1 * 10))


            # Sessão time 2
            mapa_jogado2 = mapa2["info"]["played"]
            Atk2 = mapa2['info']['atk_'][0] / mapa2['info']['atk_'][1] if mapa2['info']['atk_'][1] > 0 else 0
            Def2 = mapa2['info']['def_'][0] / mapa2['info']['def_'][1] if mapa2['info']['def_'][1] > 0 else 0
            Map2 = mapa2['info']['map_'][0] / mapa2['info']['map_'][1] if mapa2['info']['map_'][1] > 0 else 0
            Atk_emoji2 = win * int(Atk2 * 10) + lose * (10 - int(Atk2 * 10))
            Def_emoji2 = win * int(Def2 * 10) + lose * (10 - int(Def2 * 10))
            Map_emoji2 = win * int(Map2 * 10) + lose * (10 - int(Map2 * 10))

            pistol2 = mapa2['info']["pistol"][0] / mapa2['info']["pistol"][1] if mapa2['info']["pistol"][1] > 0 else 0
            pWp2    = mapa2['info']["post_W_pistol"][0] / mapa2['info']["post_W_pistol"][1] if mapa2['info']["post_W_pistol"][1] > 0 else 0
            pLp2    = mapa2['info']["post_L_pistol"][0] / mapa2['info']["post_L_pistol"][1] if mapa2['info']["post_L_pistol"][1] > 0 else 0
            pistol_emoji2   = win * int(pistol2 * 10) + lose * (10 - int(pistol2 * 10))
            pWp_emoji2      = win * int(pWp2 * 10) + lose * (10 - int(pWp2 * 10))
            pLp_emoji2      = win * int(pLp2 * 10) + lose * (10 - int(pLp2 * 10))

            # Descrição - MAPAS
            # Sessão time 1
            rating_geral = time_ratings1.get(mapa1["id"])
            str_rating_geral = str(rating_geral.get('rating'))
            rating_pos = rating_geral.get("pos")
            
            rating_number = ""
            for c in str_rating_geral:
                rating_number += numbers[int(c)]
    
            leadearboard_pos1 = top_spots[rating_pos] if rating_pos < 4 else f"{rating_pos}º"

            # Sessão time 2
            rating_geral = time_ratings2.get(mapa2["id"])
            str_rating_geral = str(rating_geral.get('rating'))
            rating_pos = rating_geral.get("pos")
            
            rating_number = ""
            for c in str_rating_geral:
                rating_number += numbers[int(c)]
    
            leadearboard_pos2 = top_spots[rating_pos] if rating_pos < 4 else f"{rating_pos}º"

            # Sessão geral
            embedMapa = discord.Embed(title=f"{time1.get('tag')} Vs. {time2.get('tag')} - {mapa1['nome']}",
                            description=f"{descricao}",
                            color=discord.Colour(0x1ABC9C))

            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                                value=f"**__Ratings & Trophies:__**", 
                                inline=False)

            embedMapa.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')}):", 
                                value=f"- **Rating:** {leadearboard_pos1}\n- :trophy: **━** {Trophies_count1}", 
                                inline=True)

            embedMapa.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')}):", 
                                value=f"- **Rating:** {leadearboard_pos2}\n- :trophy: **━** {Trophies_count2}", 
                                inline=True)
            
            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                                value=f"**__Stats do Mapa:__**", 
                                inline=False)

            # Stats do mapa
            stats_mapa1 = time_map_stats1[time_map_stats1["Map"] == mapa1["id"]]
            stats_mapa2 = time_map_stats2[time_map_stats2["Map"] == mapa2["id"]]

            if stats_mapa1.empty and stats_mapa2.empty:
                str_stats1 = "Sem Estatísticas"
                str_stats2 = "Sem Estatísticas"
                str_label = "---"
            elif not stats_mapa1.empty and not stats_mapa2.empty:
                fk1, fk2 = 0, 0
                fd1, fd2 = 0, 0
                str_stats1, str_stats2 = "", ""
                str_label = ""
                for col_tuple1, col_tuple2 in zip(stats_mapa1.iloc[0].items(), stats_mapa2.iloc[0].items()):
                    if col_tuple1[0] == "Map":
                        continue
                    if col_tuple1[0] in ["KAST", "HS"]:
                        str_stats1 += f"{col_tuple1[1]*100:.2f}%\n"
                        str_stats2 += f"{col_tuple2[1]*100:.2f}%\n"
                        str_label += f"{col_tuple1[0]}\n"
                    elif col_tuple1[0] == "FK":
                        fk1 = col_tuple1[1]
                        fk2 = col_tuple2[1]
                    elif col_tuple1[0] == "FD":
                        fd1 = col_tuple1[1]
                        fd2 = col_tuple2[1]
                        if fd1 != 0 and fd2 != 0:
                            value1 = fk1/fd1
                            value2 = fk2/fd2
                            str_stats1 += f"{value1:.2f}"
                            str_stats2 += f"{value2:.2f}"
                            str_label += f"FKFD"
                    else:
                        str_stats1 += f"{col_tuple1[1]:.2f}\n"
                        str_stats2 += f"{col_tuple2[1]:.2f}\n"
                        str_label += f"{col_tuple1[0]}\n"
            else:
                stats_mapa = stats_mapa1 if stats_mapa2.empty else stats_mapa2

                fk = 0
                fd = 0
                str_stats = ""
                str_label = ""

                for coluna, valor in stats_mapa.iloc[0].items():
                    if coluna == "Map":
                        continue
                    if coluna in ["KAST", "HS"]:
                        str_stats +=f"{valor*100:.2f}%\n"
                        str_label += f"{coluna}\n"
                    elif coluna == "FK":
                        fk = valor
                    elif coluna == "FD" and fk != 0:
                        fd = valor
                        if fd != 0:
                            value = fk / fd
                            str_stats +=f"{value:.2f}"
                            str_label += f"{coluna}"
                    else:
                        str_stats +=f"{valor:.2f}\n"
                        str_label += f"{coluna}\n"

                if stats_mapa1.empty:
                    str_stats1 = "Sem Estatísticas"
                    str_stats2 = str_stats
                else:
                    str_stats1 = str_stats
                    str_stats2 = "Sem Estatísticas"

            # Legenda
            embedMapa.add_field(name="Stat:",
                                value=str_label,
                                inline=True)
            # Time 1
            embedMapa.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')}):",
                                value=str_stats1,
                                inline=True)
            # Time 2
            embedMapa.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')}):",
                                value=str_stats2,
                                inline=True)

            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                                value=f"**__Informações Gerais:__**", 
                                inline=False)

            # sessão time 1
            value1 = f"Mapa jogado {mapa_jogado1} vezes\n- ATK w%: {Atk1 * 100:.2f}%\n  - {Atk_emoji1}\n- DEF w%: {Def1 * 100:.2f}%\n  - {Def_emoji1}\n- MAP W%: {Map1 * 100:.2f}%\n  - {Map_emoji1}\n- Pistol W% ({pistol1*100:.2f}%)\n  - {pistol_emoji1}\n- PostWin Pistol W% ({pWp1*100:.2f}%)\n  - {pWp_emoji1}\n- PostLoss Pistol W% ({pLp1*100:.2f}%)\n  - {pLp_emoji1}"
            embedMapa.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')}):", value=value1, inline=True)

            # Sessão time 2
            value2 = f"Mapa jogado {mapa_jogado2} vezes\n- ATK w%: {Atk2 * 100:.2f}%\n  - {Atk_emoji2}\n- DEF w%: {Def2 * 100:.2f}%\n  - {Def_emoji2}\n- MAP W%: {Map2 * 100:.2f}%\n  - {Map_emoji2}\n- Pistol W% ({pistol2*100:.2f}%)\n  - {pistol_emoji2}\n- PostWin Pistol W% ({pWp2*100:.2f}%)\n  - {pWp_emoji2}\n- PostLoss Pistol W% ({pLp2*100:.2f}%)\n  - {pLp_emoji2}"
            embedMapa.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')}):", value=value2, inline=True)
            
            
            # Sessão geral comps
            embedMapa.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                                value=f"**__Composições mais recentes:__**\n", 
                                inline=False)
            
            # Sessão comp time 1
            comp = mapa1["descricao"][:-1].split("\n")[0] # [:-1] para remover a última quebra de linha
            infos = comp.split("|")
            name = infos[0]
            value = ""
            if len(infos) > 1:
                value += f"{infos[1]}\n"
                for info in infos[2:]:
                    value += f"- {info}\n"
            else:
                name = comp
                value = "\u200b"
            embedMapa.add_field(name=f"{time1.get('emoji')}: {name}", value=value, inline=True)

            # Sessão comp time 2
            comp = mapa2["descricao"][:-1].split("\n")[0] # [:-1] para remover a última quebra de linha
            infos = comp.split("|")
            name = infos[0]
            value = ""
            if len(infos) > 1:
                value += f"{infos[1]}\n"
                for info in infos[2:]:
                    value += f"- {info}\n"
            else:
                name = comp
                value = "\u200b"
            embedMapa.add_field(name=f"{time2.get('emoji')}: {name}", value=value, inline=True)

            embedMapa.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")
            embedList.append(embedMapa)

        # EMBED 1 - Overview

        embed1 = discord.Embed(title=f"{time1['tag']} Vs. {time2['tag']}",
                            description=f"{descricao}",
                            color=discord.Colour(0x1ABC9C))

        # Descrição - Geral
        # Sessão time 1
        rating_geral = time_ratings1.get(0)
        str_rating_geral = str(rating_geral.get('rating'))
        rating_pos = rating_geral.get("pos")
        
        rating_number = ""
        for c in str_rating_geral:
            rating_number += numbers[int(c)]

        leadearboard_pos1 = top_spots[rating_pos] if rating_pos < 4 else f"{rating_pos}º"

        # Sessão time 2
        rating_geral = time_ratings2.get(0)
        str_rating_geral = str(rating_geral.get('rating'))
        rating_pos = rating_geral.get("pos")
        
        rating_number = ""
        for c in str_rating_geral:
            rating_number += numbers[int(c)]

        leadearboard_pos2 = top_spots[rating_pos] if rating_pos < 4 else f"{rating_pos}º"

        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                         value=f"**__Ratings & Trophies:__**", 
                         inline=False)

        embed1.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')}):", 
                         value=f"- **Rating:** {leadearboard_pos1}\n- :trophy: **━** {Trophies_count1}", 
                         inline=True)

        embed1.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')}):", 
                         value=f"- **Rating:** {leadearboard_pos2}\n- :trophy: **━** {Trophies_count2}", 
                         inline=True)

        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                         value=f"**__Stats Último Campeonato:__**\n",
                         inline=False)

        # Stats último camp
        # Sessão Geral:
        value = ""
        for coluna in colunas:
            value += f"{coluna}\n"
        value += "Clutches"
        embed1.add_field(name="Stat:",
                         value=value,
                         inline=True)

        # Sessão Time 1
        value = ""
        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                value += f"{stats_recente1[coluna]*100:.2f}%\n"
            else:
                value += f"{stats_recente1[coluna]:.2f}\n"
        value += f"{stats_recente1['CLw']}/{stats_recente1['CLp']}"
        embed1.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')}):",
                         value=value,
                         inline=True)

        # Sessão Time 2
        value = ""
        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                value += f"{stats_recente2[coluna]*100:.2f}%\n"
            else:
                value += f"{stats_recente2[coluna]:.2f}\n"
        value += f"{stats_recente2['CLw']}/{stats_recente2['CLp']}"
        embed1.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')}):",
                         value=value,
                         inline=True)

        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                         value=f"**__Comparação Geral:__**\n",
                         inline=False)

        # Infos gerais de win rate
        # Sessão time 1
        value = f"Mapas jogados: {mapas_jogados_geral1}\n"
        Atk_ = Atk_geral1[0]/Atk_geral1[1] if Atk_geral1[1] > 0 else 0
        Atk_emoji = win * int(Atk_ * 10) + lose * (10 - int(Atk_ * 10))
        Def_ = Def_geral1[0]/Def_geral1[1] if Def_geral1[1] > 0 else 0
        Def_emoji = win * int(Def_ * 10) + lose * (10 - int(Def_ * 10))
        Map_ = Map_geral1[0]/Map_geral1[1] if Map_geral1[1] > 0 else 0
        Map_emoji = win * int(Map_ * 10) + lose * (10 - int(Map_ * 10))

        pistol_ = pistol_geral1[0]/pistol_geral1[1] if pistol_geral1[1] > 0 else 0
        pistol_emoji = win * int(pistol_ * 10) + lose * (10 - int(pistol_ * 10))
        pWp_ = pWp_geral1[0]/pWp_geral1[1] if pWp_geral1[1] > 0 else 0
        pWp_emoji = win * int(pWp_ * 10) + lose * (10 - int(pWp_ * 10))
        pLp_ = pLp_geral1[0]/pLp_geral1[1] if pLp_geral1[1] > 0 else 0
        pLp_emoji = win * int(pLp_ * 10) + lose * (10 - int(pLp_ * 10))
        
        
        value += f"- ATK W%: ({Atk_*100:.2f}%)\n{Atk_emoji}\n- DEF W%: ({Def_*100:.2f}%)\n{Def_emoji}\n- MAP W%: ({Map_*100:.2f}%)\n{Map_emoji}\n- Pistol W% ({pistol_*100:.2f}%)\n{pistol_emoji}\n- PostWin Pistol W% ({pWp_*100:.2f}%)\n{pWp_emoji}\n- PostLoss Pistol W% ({pLp_*100:.2f}%)\n{pLp_emoji}"
        embed1.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')}):", 
                         value=f"{value}", 
                         inline=True)
        
        # Sessão time 2
        value = f"Mapas jogados: {mapas_jogados_geral2}\n"
        Atk_ = Atk_geral2[0]/Atk_geral2[1] if Atk_geral2[1] > 0 else 0
        Atk_emoji = win * int(Atk_ * 10) + lose * (10 - int(Atk_ * 10))
        Def_ = Def_geral2[0]/Def_geral2[1] if Def_geral2[1] > 0 else 0
        Def_emoji = win * int(Def_ * 10) + lose * (10 - int(Def_ * 10))
        Map_ = Map_geral2[0]/Map_geral2[1] if Map_geral2[1] > 0 else 0
        Map_emoji = win * int(Map_ * 10) + lose * (10 - int(Map_ * 10))

        pistol_ = pistol_geral2[0]/pistol_geral2[1] if pistol_geral2[1] > 0 else 0
        pistol_emoji = win * int(pistol_ * 10) + lose * (10 - int(pistol_ * 10))
        pWp_ = pWp_geral2[0]/pWp_geral2[1] if pWp_geral2[1] > 0 else 0
        pWp_emoji = win * int(pWp_ * 10) + lose * (10 - int(pWp_ * 10))
        pLp_ = pLp_geral2[0]/pLp_geral2[1] if pLp_geral2[1] > 0 else 0
        pLp_emoji = win * int(pLp_ * 10) + lose * (10 - int(pLp_ * 10))


        value += f"- ATK W%: ({Atk_*100:.2f}%)\n{Atk_emoji}\n- DEF W%: ({Def_*100:.2f}%)\n{Def_emoji}\n- MAP W%: ({Map_*100:.2f}%)\n{Map_emoji}\n- Pistol W% ({pistol_*100:.2f}%)\n{pistol_emoji}\n- PostWin Pistol W% ({pWp_*100:.2f}%)\n{pWp_emoji}\n- PostLoss Pistol W% ({pLp_*100:.2f}%)\n{pLp_emoji}"
        embed1.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')}):", 
                         value=f"{value}", 
                         inline=True)

        # Partidas recentes
        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", 
                         value=f"**__Últimas Partidas:__**", 
                         inline=False)
        
        # Sessão time 1
        matches_descript = matches_decript1[:-1].split("\n")
        value = ""
        for match in matches_descript:
            info = match.split(": ")[-1]
            value += f"- {info}\n"
        embed1.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')})", value=value[:-1], inline=True)

        # Sessão time 2
        matches_descript = matches_decript2[:-1].split("\n")
        value = ""
        for match in matches_descript:
            info = match.split(": ")[-1]
            value += f"- {info}\n"
        embed1.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')})", value=value[:-1], inline=True)

        embed1.set_footer(text="Informações tiradas do VLR.")


        # Embed 9 - Estatísticas históricas
        embed3 = discord.Embed(title=f"{time1.get('tag')} Vs. {time2.get('tag')} - Estatísticas Históricas",
                            description=f"{descricao}",
                            color=discord.Colour(0x1ABC9C))
        
        embed3.add_field(name="━━━━━━━━━━━━━━━━━━━━━━",
                         value=" ",
                         inline=False)

        # Stats históricos
        # Sessão Geral:
        value = ""
        for coluna in colunas:
            value += f"{coluna}\n"
        value += "Clutches"
        embed3.add_field(name="Stat:",
                         value=value,
                         inline=True)
        
        # Sessão Time 1
        value = ""
        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                value += f"{time_stats1[coluna].mean()*100:.2f}%\n"
            else:
                value += f"{time_stats1[coluna].mean():.2f}\n"
        value += f"{time_stats1['CLw'].sum()}/{time_stats1['CLp'].sum()}"
        embed3.add_field(name=f"{time1.get('emoji')} ({time1.get('tag')})",
                         value=value,
                         inline=True)
        
        # Sessão Time 2
        value = ""
        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                value += f"{time_stats2[coluna].mean()*100:.2f}%\n"
            else:
                value += f"{time_stats2[coluna].mean():.2f}\n"
        value += f"{time_stats2['CLw'].sum()}/{time_stats2['CLp'].sum()}"
        embed3.add_field(name=f"{time2.get('emoji')} ({time2.get('tag')})",
                         value=value,
                         inline=True)
        

        embed3.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")

        embedList.insert(0, embed1)
        embedList.insert(0, embed0)
        embedList.append(embed3)

        await interaction.edit_original_response(content=mensagem, view=disB.MenuView(embedList, pool, tipo=1))
    else:
        await interaction.followup.send("Erro ao carregar um dos times.", ephemeral=True)

'''
                                            COMANDO            #4
'''
async def map_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    mapas_disponiveis = [(mapa["nome"], mapa_id) for mapa_id, mapa in logic.maps.items()]
    mapas_filtrados = [
        item for item in mapas_disponiveis
        if current.lower() in item[0].lower()
    ][:15]
    return [
        app_commands.Choice(name=mapa[0], value=str(mapa[1]))
        for mapa in mapas_filtrados
    ]

async def condition_autocomplete(
        interaction: discord.Interaction,
        current: str
) -> list[app_commands.Choice[str]]:
    opcoes1 = [] # tags
    opcoes2 = [] # nomes
    opcoes = [("Americas", "Americas"), ("China", "China"), ("EMEA", "EMEA"), ("Pacific", "Pacific")] # regioes
    for time in logic.times:
        tag, nome, id = time["tag"], time["nome"], time["id"]
        opcoes1.append((tag, id))
        if tag != nome:
            opcoes2.append((nome, id))
    opcoes1.extend(opcoes2) # tags na frente de nomes
    opcoes.extend(opcoes1) # regioes na frente dos times
    opcoes_filtradas = [
        opcao for opcao in opcoes
        if current.lower() in opcao[0].lower()
    ][:15]
    return [
        app_commands.Choice(name=nome, value=str(valor))
        for nome, valor in opcoes_filtradas
    ]

@bot.tree.command(name="leaderboard", description="Diferente tabelas de ratings dos times")
@app_commands.describe(
    map_query="Nome do mapa desejado. Deixe em brano para o Ranking Geral.",
    condition="Digite a TAG/nome de um time (para incluí-lo) OU o nome da Região (ex: Americas, EMEA...)."
)
@app_commands.autocomplete(map_query=map_autocomplete, condition=condition_autocomplete)
async def leaderboard(interaction: discord.Interaction, map_query: Optional[str] = "0", condition: Optional[str] = None):

    await interaction.response.defer()

    opcoes1 = {str(time["id"]):(time["tag"], time["emoji"]) for time in logic.times} # times
    opcoes_cond = ["Americas", "China", "EMEA", "Pacific"] # regioes
    opcoes_cond.extend(opcoes1.keys()) # regioes na frente dos times

    mapas_disponiveis = {str(mapa_id): mapa.get("nome") for mapa_id, mapa in logic.maps.items()}


    mensagem = ""

    if map_query == "0":
        map_query = 0
    elif map_query not in mapas_disponiveis.keys():
        mensagem += "Mapa fora das opções disponíveis. Rodando leaderboard geral\n"
        map_query = 0
    else:
        map_query = int(map_query)

    if condition is None:
        condition = None
    elif condition not in opcoes_cond:
        mensagem += "Condição fora das opções disponíveis. Leaderboard padrão selecionado automaticamente\n"
        condition = None
    elif condition not in ["Americas", "China", "EMEA", "Pacific"]:
        condition = int(condition)
    elif condition == "Americas":
        condition = "Amer"
    
    lb = await logic.get_leaderboard(int(map_query), condition)

    if lb is None:
        mensagem += "...\nErro: Leaderboard retornou vazia."
        await interaction.edit_original_response(content=mensagem)
    else:
        if map_query == 0:
            lb_escopo = "Geral"
        else:
            map_query = str(map_query)
            lb_escopo = f"da {mapas_disponiveis[map_query]}"
        if str(condition) in opcoes1.keys():
            if len(lb) == 10:
                str_tipo = ""
            lb_tipo = opcoes1[str(condition)]
            str_tipo = f"+ {lb_tipo[1]} ({lb_tipo[0]})"
        elif condition is None:
            str_tipo = ""
        else:
            str_tipo = f"- {condition}"

  
        mensagem += f'# :first_place: ({lb[0]["posicao"]}º)\n{lb[0]["emoji"]} ({lb[0]["tag"]} - {lb[0]["regiao"]}) **━** {lb[0]["rating"]}\n'
        mensagem += f'## :second_place: ({lb[1]["posicao"]}º)\n{lb[1]["emoji"]} ({lb[1]["tag"]} - {lb[1]["regiao"]}) **━** {lb[1]["rating"]}\n'
        mensagem += f'### :third_place: ({lb[2]["posicao"]}º)\n{lb[2]["emoji"]} ({lb[2]["tag"]} - {lb[2]["regiao"]}) **━** {lb[2]["rating"]}'

        answer = discord.Embed(
            title=f"Leaderboard {lb_escopo} {str_tipo}",
            description=mensagem,
            color=discord.Colour(0x1ABC9C)
        )

        answer.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━", 
            value="",
            inline=False
        )

        for i, value in enumerate(lb):
            if i in [0, 1, 2]:
                continue
            else:
                answer.add_field(
                    name=f'**{i+1}º ({value["posicao"]}º) ━ lugar**',
                    value=f'{value["emoji"]} ({value["tag"]} - {value["regiao"]})\n{value["rating"]}',
                    inline=True
                )

        await interaction.edit_original_response(embed=answer)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)