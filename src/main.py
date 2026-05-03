from datetime import time, timezone
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import tasks
import pandas as pd
import disc_buttons
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

# SERVER DE USO DE COMANDOS VISUAIS
GUILD_ID_INFO = discord.Object(id=int(os.getenv('GUILD_ID')))
CREATOR_ID = int(os.getenv('CREATOR_ID'))

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
logic = brain.Brain(times, maps, agents, comps, camps, partidas, mapas_jogados)

async def perform_global_reload():
    print("Recarregando dados do banco para a RAM...")
    res = await brain.perform_global_reload()

    if not isinstance(res, Exception):
        global times, maps, agents, comps, camps, partidas, mapas_jogados
        times, maps, agents, comps, camps, partidas, mapas_jogados = res
        
        print("Dados recarregados com sucesso!")
        return 1
    
    else:
        print(f"Erro durante o reload: {res}")
        return 0

# Events
@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    await perform_global_reload() # Carrega os dados do banco para a RAM quando o bot inicia

    logic.update_data(times, maps, agents, comps, camps, partidas, mapas_jogados)

    try:

        guild = GUILD_ID_INFO
        synced = await bot.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands to guild {guild.id}')

    except Exception as e:
        print(f'Error syncing commands: {e}')


# COMANDOS
'''
                                            INFO_LOADERS 
'''

@bot.tree.command(name="update_cache", description="Força o reload dos dados", guild=GUILD_ID_INFO) # Comando exclusivo do dono, por isso exclusivo do server de testes tbm
@app_commands.check(lambda inst: inst.user.id == CREATOR_ID)
async def update_cache(interaction: discord.Interaction):
    # if interaction.user.id != CREATOR_ID:
    #     return await interaction.response.send_message("Apenas o desenvolvedor pode usar isso.", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True) # Resposta visível só para você

    if (await perform_global_reload()):
        logic.update_data(times, maps, agents, comps, camps, partidas, mapas_jogados)
        await interaction.followup.send(content="Cache atualizado com sucesso!", ephemeral=True)
    else:
        await interaction.followup.send(content="Erro ao atualizar o cache.", ephemeral=True)

@tasks.loop(time=target_time)
async def auto_reload_db():
    print("Executando reload agendado pós-GitHub Actions...")

    sucesso = await perform_global_reload()

    if sucesso:
        logic.update_data(times, maps, agents, comps, camps, partidas, mapas_jogados)
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
                answer.add_field(name="\u200b", value="\u200b", inline=False) # empty field for spacing
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
    # Creating the embed

    await interaction.response.defer(ephemeral=False)
    
    # since we have just two case of team name/tag that contains Diacritics, we are treating it alone
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
        embedIndex = 0
        embedList = []

        # Stats for embed1
        colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS"]
        idx_mais_recente = time_stats["Camp"].idxmax()
        stats_recente = time_stats.loc[idx_mais_recente]

        #   CRIANDO EMBED PÁGINA 1
        # Definindo descrição
        descricao = f"{time.get('regiao')}'s team\n"
        
        embed = discord.Embed(title=f"{time.get('tag')}",
                            description=f"{descricao}### Stats do último campeonato:",
                            color=discord.Colour(0x1ABC9C))

        embed.set_thumbnail(url=time.get("img_url"))

        # Stats último camp
        for coluna in colunas:
            if coluna in ["KAST", "HS"]:
                embed.add_field(name=coluna, value=f"{stats_recente[coluna]*100:.2f}%", inline=True)
            else:
                embed.add_field(name=coluna, value=f"{stats_recente[coluna]:.2f}", inline=True)
        embed.add_field(name="Clutches", value=f"{stats_recente['CLw']}/{stats_recente['CLp']}", inline=True)

        # Partidas recentes
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", value="\u200b", inline=False) # empty field for spacing
        embed.add_field(name="**__Últimas Partidas:__**", value=f"{matches_decript}", inline=False)

        embed.set_footer(text="Informações tiradas do VLR.")

        #   CRIANDO EMBED PÁGINA 2 
        embed2 = discord.Embed(title=time.get("tag") + "- Mapas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))
        
        for mapa in time_mapas:
            embed2.add_field(name=f"{mapa['nome']}", value=mapa['descricao'], inline=False)

        embed2.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")

        #   CRIANDO EMBED PÁGINA 4 
        embed3 = discord.Embed(title=time.get("tag") + " - Estatísticas Históricas",
                            description=descricao,
                            color=discord.Colour(0x1ABC9C))
        for coluna in colunas:
            embed3.add_field(name=coluna, value=f"{time_stats[coluna].mean():.2f}", inline=True)
        embed3.add_field(name="Clutches", value=f"{time_stats['CLw'].sum()}/{time_stats['CLp'].sum()}", inline=True)

        embed3.set_footer(text="Base de dados: VLR.gg — Inteligência e análise de dados autoral.")

        embedList.append(embed)
        embedList.append(embed2)
        embedList.append(embed3)

        await interaction.edit_original_response(embed=embedList[embedIndex], view=disc_buttons.EmbedChangePage(embedList, embedIndex))
    else:
        await interaction.followup.send("Erro ao carregar o time.", ephemeral=True)







bot.run(token, log_handler=handler, log_level=logging.DEBUG)