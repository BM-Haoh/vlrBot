from datetime import time, timezone
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import tasks
import disc_buttons as disB
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

# auto_reload roda diariamente às 6:10 UTC (3:10 em Brasília), pós web scraping no github actions
target_time = time(hour=6, minute=10, tzinfo=timezone.utc)

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
    Automatic reload scheduled for 6:10 UTC daily.
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
    times = await logic.get("times")

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



'''
                                            COMANDO            #2
'''
@bot.tree.command(name="info_time", description="Informação sobre um time")
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
    

    time, matches_decript, time_mapas, time_stats = res

    if type(time) == dict:
        embedList = []

        # EMBED 0 - Glossário

        embed0 = discord.Embed(title=f"{time['tag']} Embed Book",
                            description=f"# Escolha uma página para visualizar",
                            color=discord.Colour(0x1ABC9C))
        
        embed0.set_thumbnail(url=time['img_url'])

        embed0.add_field(name="Página 1: Overview",
                         value="Informações gerais do time, contendo:\n- Estatísticas do último campeonato\n- Últimas 5 partidas do time",
                         inline=True)
        embed0.add_field(name="Páginas de 2 a 8: Mapas",
                         value="Informações sobre o time em cada mapa, contendo:\n- Composições do time\n- Taxa de vitória no ataque\n- Taxa de vitória da defesa\n- Taxa de vitória no mapa",
                         inline=True)
        embed0.add_field(name="Página 9: Estatísticas",
                         value="Estatísticas do time historicamente, contendo:\n- Média das tabelas de estatísticas de cada campeonato do VCT para o time.",
                         inline=True)
        
        embed0.set_footer(text='Glossário do "Livro" de Embeds')
        
        
        # Stats do Embed 1
        colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS"]
        idx_mais_recente = time_stats["Camp"].idxmax()
        stats_recente = time_stats.loc[idx_mais_recente]
        mapas_jogados_geral = 0
        Atk_geral = [0, 0] # [vitórias, total]
        Def_geral = [0, 0] # [vitórias, total]
        Map_geral = [0, 0] # [vitórias, total]

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

            mapa_jogado = mapa["info"]["played"]
            Atk = mapa['info']['atk_'][0] / mapa['info']['atk_'][1] if mapa['info']['atk_'][1] > 0 else 0
            Def = mapa['info']['def_'][0] / mapa['info']['def_'][1] if mapa['info']['def_'][1] > 0 else 0
            Map = mapa['info']['map_'][0] / mapa['info']['map_'][1] if mapa['info']['map_'][1] > 0 else 0
            Atk_emoji = win * int(Atk * 10) + lose * (10 - int(Atk * 10))
            Def_emoji = win * int(Def * 10) + lose * (10 - int(Def * 10))
            Map_emoji = win * int(Map * 10) + lose * (10 - int(Map * 10))

            embedMapa = discord.Embed(title=f"{time.get('tag')} - {mapa['nome']}",
                            description=f"## Informações gerais do mapa:\nMapa jogado {mapa_jogado} vezes\n- Taxa de vitória no ataque: {Atk * 100:.2f}%\n  - {Atk_emoji}\n- Taxa de vitória na defesa: {Def * 100:.2f}%\n  - {Def_emoji}\n- Taxa de vitória geral no mapa: {Map * 100:.2f}%\n  - {Map_emoji}\n## Composições jogadas no mapa:",
                            color=discord.Colour(0x1ABC9C))
            
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

        # EMBED 1 - Overview
        descricao = f"{time['regiao']}'s team\n"

        embed1 = discord.Embed(title=f"{time['tag']}",
                            description=f"{descricao}### Stats do último campeonato:",
                            color=discord.Colour(0x1ABC9C))

        embed1.set_thumbnail(url=time['img_url'])

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
        
        value += f"- ATK W%: ({Atk_*100:.2f}%)\n{Atk_emoji}\n- DEF W%: ({Def_*100:.2f}%)\n{Def_emoji}\n- MAP W%: ({Map_*100:.2f}%)\n{Map_emoji}"
        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", 
                         value=f"**__Informações Gerais:__**\n{value}", 
                         inline=False)

        # Partidas recentes
        embed1.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", 
                         value=f"**__Últimas Partidas:__**\n{matches_decript}", 
                         inline=False)

        embed1.set_footer(text="Informações tiradas do VLR.")

       

        # Embed 9 - Estatísticas históricas
        embed3 = discord.Embed(title=time.get("tag") + " - Estatísticas Históricas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))
        for coluna in colunas:
            embed3.add_field(name=coluna, value=f"{time_stats[coluna].mean():.2f}", inline=True)
        embed3.add_field(name="Clutches", value=f"{time_stats['CLw'].sum()}/{time_stats['CLp'].sum()}", inline=True)

        embed3.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")

        embedList.insert(0, embed1)
        embedList.append(embed3)

        await interaction.edit_original_response(embed=embed0, view=disB.MenuView(embedList, pool))
    else:
        await interaction.followup.send("Erro ao carregar o time.", ephemeral=True)







bot.run(token, log_handler=handler, log_level=logging.DEBUG)