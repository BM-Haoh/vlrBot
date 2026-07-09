from website.data_loader import carregar_dados
from brain import Brain, discover_reload_site
from dotenv import load_dotenv
import website.pages as pages
import streamlit as st
import pandas as pd
import asyncio
import sys

# alterando a política do loop de eventos
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# carregando as variáveis de ambiente
load_dotenv()

st.set_page_config(
    page_title="Valorant Analytics Hub",
    layout="wide",)

cache_window = discover_reload_site()

dados_brutos = carregar_dados(cache_window)

if dados_brutos:
    logic = Brain([], {}, {}, {}, {}, [], [])
    logic.update_data(dados_brutos)
    
    pgs = pages.Pages(logic)

    pg = st.navigation(
        {
            "Help": [st.Page(pgs.help, title="Ajuda")],
            "Comandos": [st.Page(pgs.info_time, title="Informação de Time"), st.Page(pgs.vs, title="Time Vs. Time")],
        }
    )

    pg.run()
else:
    st.error("Erro ao carregar os dados do banco de dados.")